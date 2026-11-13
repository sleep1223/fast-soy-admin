"""Generic OCR tests use fake engines and isolated in-memory fixtures."""

from __future__ import annotations

import io
import json
from collections.abc import Sequence
from types import SimpleNamespace

import pytest
from PIL import Image

from app.core.ocr import OcrCrop, OcrEngineOutput, OcrInvalidImage, OcrLimits, OcrService, OcrUnavailable, RapidOcrEngine
from app.system.api import ocr as ocr_api


def png_bytes(size: tuple[int, int] = (40, 20)) -> bytes:
    image = Image.new("RGB", size, "white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    image.close()
    return output.getvalue()


class FakeEngine:
    def __init__(
        self,
        texts: Sequence[str] = ("000123456", "000123457"),
        scores: Sequence[float] = (0.98, 0.42),
        boxes: Sequence[Sequence[tuple[int, int]]] = (
            ((2, 2), (18, 2), (18, 8), (2, 8)),
            ((2, 10), (18, 10), (18, 16), (2, 16)),
        ),
    ) -> None:
        self.texts = texts
        self.scores = scores
        self.boxes = boxes
        self.use_cls: bool | None = None

    def recognize(self, image: Image.Image, *, use_cls: bool) -> OcrEngineOutput:
        self.use_cls = use_cls
        assert image.size == (20, 10)  # resized from 40x20
        return OcrEngineOutput(texts=self.texts, scores=self.scores, boxes=self.boxes)


def service(engine: FakeEngine | None = None, *, max_items: int = 10) -> tuple[OcrService, FakeEngine]:
    fake = engine or FakeEngine()
    limits = OcrLimits(
        max_side=20,
        max_pixels=1_000_000,
        max_image_mb=1,
        max_items=max_items,
        queue_timeout_seconds=1,
    )
    return OcrService(engine_factory=lambda: fake, limits=limits), fake


def test_service_maps_resized_boxes_and_confidence() -> None:
    ocr, fake = service()
    result = ocr.recognize(png_bytes(), use_cls=False)
    assert fake.use_cls is False
    assert result.text == "000123456\n000123457"
    assert result.width == 40 and result.height == 20
    assert result.items[0].confidence == 0.98
    assert result.items[0].box == ((4, 4), (36, 4), (36, 16), (4, 16))
    assert result.items[1].confidence == 0.42


def test_service_crops_before_resize_and_preserves_original_coordinates() -> None:
    ocr, _ = service()
    result = ocr.recognize(png_bytes(), crop=OcrCrop(x=10, y=5, width=20, height=10))
    assert result.width == 40 and result.height == 20
    # crop is 20x10, not resized; fake box is relative to the crop.
    assert result.items[0].box == ((12, 7), (28, 7), (28, 13), (12, 13))


def test_service_truncates_and_reports_empty_text() -> None:
    ocr, _ = service(FakeEngine(texts=("a", "b", "c"), scores=(1, 1, 1), boxes=((), (), ())), max_items=2)
    result = ocr.recognize(png_bytes())
    assert result.truncated is True
    assert result.text == "a\nb"
    empty, _ = service(FakeEngine(texts=(), scores=(), boxes=()))
    assert empty.recognize(png_bytes()).text == ""


def test_rapidocr_adapter_never_uses_numpy_array_truthiness() -> None:
    class ArrayLike(list[object]):
        def __bool__(self) -> bool:
            raise ValueError("ambiguous truth value")

    engine = RapidOcrEngine.__new__(RapidOcrEngine)
    engine._engine = lambda *args, **kwargs: SimpleNamespace(
        txts=("000123456",),
        scores=(0.99,),
        boxes=ArrayLike([[[1, 2], [3, 2], [3, 4], [1, 4]]]),
    )
    output = engine.recognize(Image.new("RGB", (10, 10)), use_cls=True)
    assert output.texts == ("000123456",)
    assert output.boxes == (((1, 2), (3, 2), (3, 4), (1, 4)),)


def test_service_rejects_invalid_image_and_unavailable_engine() -> None:
    ocr, _ = service()
    with pytest.raises(OcrInvalidImage):
        ocr.recognize(b"not-an-image")

    def unavailable() -> FakeEngine:
        raise OcrUnavailable("missing")

    missing = OcrService(engine_factory=unavailable, limits=OcrLimits(max_side=20))
    with pytest.raises(OcrUnavailable, match="missing"):
        missing.recognize(png_bytes())


@pytest.mark.asyncio(loop_scope="session")
async def test_api_requires_permission_and_returns_camel_case(auth_client, client, monkeypatch) -> None:
    ocr, _ = service()
    monkeypatch.setattr(ocr_api, "ocr_service", ocr)

    denied = await client.post(
        "/api/v1/system-manage/ocr/recognize",
        files={"file": ("test.png", png_bytes(), "image/png")},
    )
    assert denied.json()["code"] != "0000"

    response = await auth_client.post(
        "/api/v1/system-manage/ocr/recognize",
        files={"file": ("test.png", png_bytes(), "image/png")},
        data={"options": json.dumps({"useCls": False})},
    )
    payload = response.json()
    assert payload["code"] == "0000"
    assert payload["data"]["text"] == "000123456\n000123457"
    assert payload["data"]["elapsedMs"] >= 0
    assert payload["data"]["items"][0]["box"][0] == [4, 4]


@pytest.mark.asyncio(loop_scope="session")
async def test_api_returns_ocr_errors_with_business_codes(auth_client, monkeypatch) -> None:
    ocr, _ = service()
    monkeypatch.setattr(ocr_api, "ocr_service", ocr)

    invalid_image = await auth_client.post(
        "/api/v1/system-manage/ocr/recognize",
        files={"file": ("bad.png", b"not-an-image", "image/png")},
    )
    assert invalid_image.json()["code"] == "2412"

    invalid_options = await auth_client.post(
        "/api/v1/system-manage/ocr/recognize",
        files={"file": ("test.png", png_bytes(), "image/png")},
        data={"options": "{not-json}"},
    )
    assert invalid_options.json()["code"] == "1200"

    too_large = OcrService(
        engine_factory=lambda: FakeEngine(),
        limits=OcrLimits(max_image_mb=0, max_side=20),
    )
    monkeypatch.setattr(ocr_api, "ocr_service", too_large)
    oversized = await auth_client.post(
        "/api/v1/system-manage/ocr/recognize",
        files={"file": ("test.png", png_bytes(), "image/png")},
    )
    assert oversized.json()["code"] == "2412"

    def unavailable() -> FakeEngine:
        raise OcrUnavailable("OCR 组件未安装")

    missing = OcrService(engine_factory=unavailable, limits=OcrLimits(max_side=20))
    monkeypatch.setattr(ocr_api, "ocr_service", missing)
    unavailable_response = await auth_client.post(
        "/api/v1/system-manage/ocr/recognize",
        files={"file": ("test.png", png_bytes(), "image/png")},
    )
    assert unavailable_response.json()["code"] == "2411"
