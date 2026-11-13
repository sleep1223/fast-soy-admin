"""Local, generic OCR service.

The OCR engine is optional: install it with ``uv sync --extra ocr``. This module
must stay independent of business concepts such as order or ticket numbers.
"""

from __future__ import annotations

import importlib
import io
import threading
import time
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import APP_SETTINGS
from app.core.log import log

# Match the image formats accepted by the existing upload service. OCR never
# writes the image to disk; the bytes are decoded and released in memory.
OCR_IMAGE_FORMATS = frozenset({"JPEG", "PNG", "GIF", "WEBP"})


class OcrError(Exception):
    """Base class for OCR failures that are safe to translate at the API layer."""


class OcrUnavailable(OcrError):
    """The optional OCR dependency or engine is not available."""


class OcrInvalidImage(OcrError):
    """The uploaded bytes are empty, too large, unsupported, or malformed."""


class OcrBusy(OcrError):
    """No inference slot became available before the queue timeout."""


class OcrFailed(OcrError):
    """The engine failed while processing a valid image."""


class OcrEngine(Protocol):
    """Minimal engine contract used by tests and the RapidOCR adapter."""

    def recognize(self, image: Image.Image, *, use_cls: bool) -> OcrEngineOutput: ...


@dataclass(frozen=True)
class OcrEngineOutput:
    texts: Sequence[str]
    scores: Sequence[float]
    boxes: Sequence[Sequence[tuple[int, int]]]


@dataclass(frozen=True)
class OcrItem:
    text: str
    confidence: float
    box: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class OcrResult:
    text: str
    items: tuple[OcrItem, ...]
    elapsed_ms: int
    truncated: bool
    width: int
    height: int


@dataclass(frozen=True)
class OcrCrop:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class OcrLimits:
    enabled: bool = True
    max_image_mb: int = 10
    max_pixels: int = 25_000_000
    max_items: int = 500
    max_side: int = 1600
    timeout_seconds: int = 30
    queue_timeout_seconds: int = 10
    max_concurrency: int = 1

    @classmethod
    def from_settings(cls) -> OcrLimits:
        return cls(
            enabled=bool(getattr(APP_SETTINGS, "OCR_ENABLED", True)),
            max_image_mb=max(1, int(getattr(APP_SETTINGS, "OCR_MAX_IMAGE_MB", 10))),
            max_pixels=max(1, int(getattr(APP_SETTINGS, "OCR_MAX_PIXELS", 25_000_000))),
            max_items=max(1, int(getattr(APP_SETTINGS, "OCR_MAX_ITEMS", 500))),
            max_side=max(1, int(getattr(APP_SETTINGS, "OCR_MAX_SIDE", 1600))),
            timeout_seconds=max(1, int(getattr(APP_SETTINGS, "OCR_TIMEOUT_SECONDS", 30))),
            queue_timeout_seconds=max(0, int(getattr(APP_SETTINGS, "OCR_QUEUE_TIMEOUT_SECONDS", 10))),
            max_concurrency=max(1, int(getattr(APP_SETTINGS, "OCR_MAX_CONCURRENCY", 1))),
        )


@dataclass(frozen=True)
class _BoxTransform:
    """Map boxes from the processed image back to the uploaded image."""

    offset_x: int
    offset_y: int
    scale_x: float
    scale_y: float

    def apply(self, box: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
        return tuple(
            (
                int(round(self.offset_x + x / self.scale_x)),
                int(round(self.offset_y + y / self.scale_y)),
            )
            for x, y in box
        )


class RapidOcrEngine:
    """Lazily imports RapidOCR so the base installation stays independent."""

    def __init__(self) -> None:
        try:
            module = importlib.import_module("rapidocr")
            rapid_ocr = getattr(module, "RapidOCR")
        except (ImportError, AttributeError) as exc:
            raise OcrUnavailable("OCR 组件未安装，请执行 uv sync --extra ocr 后重启服务") from exc
        try:
            self._engine: Any = rapid_ocr()
        except Exception as exc:
            raise OcrUnavailable("OCR 引擎初始化失败，请检查模型文件及运行环境") from exc

    def recognize(self, image: Image.Image, *, use_cls: bool) -> OcrEngineOutput:
        result = self._engine(image, use_det=True, use_cls=use_cls, use_rec=True)
        if result is None:
            return OcrEngineOutput((), (), ())
        raw_texts = getattr(result, "txts", None)
        raw_scores = getattr(result, "scores", None)
        raw_boxes = getattr(result, "boxes", None)
        texts = tuple(str(value) for value in (raw_texts if raw_texts is not None else ()))
        scores = tuple(float(value) for value in (raw_scores if raw_scores is not None else ()))
        boxes: list[tuple[tuple[int, int], ...]] = []
        for raw_box in raw_boxes if raw_boxes is not None else ():
            boxes.append(tuple((int(round(float(point[0]))), int(round(float(point[1])))) for point in raw_box))
        return OcrEngineOutput(texts=texts, scores=scores, boxes=tuple(boxes))


def _default_engine_factory() -> OcrEngine:
    return RapidOcrEngine()


def _open_image(content: bytes, limits: OcrLimits) -> Image.Image:
    if not content:
        raise OcrInvalidImage("图片不能为空")
    if len(content) > limits.max_image_mb * 1024 * 1024:
        raise OcrInvalidImage(f"图片不能超过 {limits.max_image_mb} MB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as source:
                if source.format not in OCR_IMAGE_FORMATS:
                    raise OcrInvalidImage("仅支持 JPG、PNG、GIF、WebP 图片")
                if source.width * source.height > limits.max_pixels:
                    raise OcrInvalidImage(f"图片像素不能超过 {limits.max_pixels}，请先缩小图片")
                source.load()
                image = ImageOps.exif_transpose(source)
                if image is None:
                    raise OcrInvalidImage("图片方向信息无效")
                image = image.convert("RGB")
    except OcrInvalidImage:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise OcrInvalidImage("图片内容无效，请上传有效的 JPG、PNG、GIF 或 WebP 图片") from exc
    if image.width * image.height > limits.max_pixels:
        image.close()
        raise OcrInvalidImage(f"图片像素不能超过 {limits.max_pixels}，请先缩小图片")
    return image


def _prepare_image(content: bytes, limits: OcrLimits, crop: OcrCrop | None) -> tuple[Image.Image, _BoxTransform, int, int]:
    image = _open_image(content, limits)
    original_width, original_height = image.size
    offset_x = offset_y = 0
    if crop is not None:
        if crop.width <= 0 or crop.height <= 0 or crop.x < 0 or crop.y < 0 or crop.x + crop.width > image.width or crop.y + crop.height > image.height:
            image.close()
            raise OcrInvalidImage("裁切区域超出图片范围")
        cropped = image.crop((crop.x, crop.y, crop.x + crop.width, crop.y + crop.height))
        image.close()
        image = cropped
        offset_x, offset_y = crop.x, crop.y

    crop_width, crop_height = image.size
    longest = max(crop_width, crop_height)
    if longest > limits.max_side:
        ratio = limits.max_side / longest
        resized = (max(1, round(crop_width * ratio)), max(1, round(crop_height * ratio)))
        resized_image = image.resize(resized, Image.Resampling.LANCZOS)
        image.close()
        image = resized_image
        scale_x = resized[0] / crop_width
        scale_y = resized[1] / crop_height
    else:
        scale_x = scale_y = 1.0
    return image, _BoxTransform(offset_x=offset_x, offset_y=offset_y, scale_x=scale_x, scale_y=scale_y), original_width, original_height


def _build_result(output: OcrEngineOutput, transform: _BoxTransform, limits: OcrLimits, elapsed_ms: int, width: int, height: int) -> OcrResult:
    items: list[OcrItem] = []
    texts = output.texts[: limits.max_items]
    for index, raw_text in enumerate(texts):
        text = str(raw_text).strip()
        if not text:
            continue
        confidence = float(output.scores[index]) if index < len(output.scores) else 0.0
        confidence = min(1.0, max(0.0, confidence))
        raw_box = output.boxes[index] if index < len(output.boxes) else ()
        items.append(OcrItem(text=text, confidence=round(confidence, 4), box=transform.apply(raw_box)))
    return OcrResult(
        text="\n".join(item.text for item in items),
        items=tuple(items),
        elapsed_ms=elapsed_ms,
        truncated=len(output.texts) > limits.max_items,
        width=width,
        height=height,
    )


class OcrService:
    """Thread-safe, per-process OCR service with one reusable engine."""

    def __init__(
        self,
        engine_factory: Callable[[], OcrEngine] | None = None,
        limits: OcrLimits | None = None,
    ) -> None:
        self._engine_factory = engine_factory or _default_engine_factory
        self._limits = limits or OcrLimits.from_settings()
        self._engine: OcrEngine | None = None
        self._engine_lock = threading.Lock()
        self._inference_slots = threading.BoundedSemaphore(self._limits.max_concurrency)

    @property
    def limits(self) -> OcrLimits:
        return self._limits

    def _get_engine(self) -> OcrEngine:
        if not self._limits.enabled:
            raise OcrUnavailable("OCR 功能已关闭，请设置 OCR_ENABLED=true 后重启服务")
        if self._engine is not None:
            return self._engine
        with self._engine_lock:
            if self._engine is None:
                self._engine = self._engine_factory()
        return self._engine

    def recognize(self, content: bytes, *, crop: OcrCrop | None = None, use_cls: bool = True) -> OcrResult:
        """Recognize text synchronously. Callers should run this in a worker thread."""
        image, transform, width, height = _prepare_image(content, self._limits, crop)
        try:
            engine = self._get_engine()
            if not self._inference_slots.acquire(timeout=self._limits.queue_timeout_seconds):
                raise OcrBusy("OCR 服务繁忙，请稍后重试")
            started = time.perf_counter()
            try:
                output = engine.recognize(image, use_cls=use_cls)
            finally:
                self._inference_slots.release()
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            return _build_result(output, transform, self._limits, elapsed_ms, width, height)
        except OcrError:
            raise
        except Exception as exc:
            # Never log image bytes or recognized text; they may contain production data.
            log.exception("OCR recognition failed")
            raise OcrFailed("OCR 识别失败，请稍后重试") from exc
        finally:
            image.close()


ocr_service = OcrService()


__all__ = [
    "OcrBusy",
    "OcrCrop",
    "OcrEngine",
    "OcrEngineOutput",
    "OcrError",
    "OcrFailed",
    "OcrInvalidImage",
    "OcrItem",
    "OcrLimits",
    "OcrResult",
    "OcrService",
    "OcrUnavailable",
    "RapidOcrEngine",
    "ocr_service",
]
