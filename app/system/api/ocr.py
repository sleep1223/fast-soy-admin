"""Generic OCR API. The image is processed in memory and never persisted."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import ValidationError

from app.core.base_schema import ResponseModel, Success
from app.core.code import Code
from app.core.exceptions import BizError
from app.core.ocr import OcrBusy, OcrCrop, OcrError, OcrFailed, OcrInvalidImage, OcrResult, OcrUnavailable, ocr_service
from app.system.schemas.ocr import OcrItemOut, OcrOptions, OcrResultOut

router = APIRouter()


def _result_out(result: OcrResult) -> dict:
    payload = OcrResultOut(
        text=result.text,
        items=[OcrItemOut(text=item.text, confidence=item.confidence, box=[list(point) for point in item.box]) for item in result.items],
        elapsed_ms=result.elapsed_ms,
        truncated=result.truncated,
        width=result.width,
        height=result.height,
    )
    return payload.model_dump(mode="json", by_alias=True)


def _parse_options(raw: str | None) -> OcrOptions:
    if raw is None or not raw.strip():
        return OcrOptions.model_validate({})
    try:
        return OcrOptions.model_validate_json(raw)
    except ValidationError as exc:
        raise BizError(code=Code.REQUEST_VALIDATION, msg="OCR 识别参数无效") from exc


@router.post("/ocr/recognize", summary="识别图片文字", name="system.ocr.recognize", response_model=ResponseModel[OcrResultOut])
async def recognize_image(
    file: Annotated[UploadFile, File(description="待识别图片")],
    options: Annotated[str | None, Form(description="JSON 识别参数")] = None,
) -> Success:
    limits = ocr_service.limits
    if not limits.enabled:
        raise BizError(code=Code.OCR_UNAVAILABLE, msg="OCR 功能已关闭，请设置 OCR_ENABLED=true 后重启服务")
    limit = limits.max_image_mb * 1024 * 1024
    try:
        content = await file.read(limit + 1)
        if len(content) > limit:
            raise BizError(code=Code.OCR_INVALID_IMAGE, msg=f"图片不能超过 {limits.max_image_mb} MB")
        parsed = _parse_options(options)
        crop = OcrCrop(x=parsed.crop.x, y=parsed.crop.y, width=parsed.crop.width, height=parsed.crop.height) if parsed.crop else None

        def recognize() -> OcrResult:
            return ocr_service.recognize(content, crop=crop, use_cls=parsed.use_cls)

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(recognize),
                timeout=limits.timeout_seconds,
            )
        except TimeoutError as exc:
            raise BizError(code=Code.OCR_TIMEOUT, msg="OCR 识别超时，请缩小图片或稍后重试") from exc
        except OcrUnavailable as exc:
            raise BizError(code=Code.OCR_UNAVAILABLE, msg=str(exc)) from exc
        except OcrInvalidImage as exc:
            raise BizError(code=Code.OCR_INVALID_IMAGE, msg=str(exc)) from exc
        except OcrBusy as exc:
            raise BizError(code=Code.OCR_BUSY, msg=str(exc)) from exc
        except OcrFailed as exc:
            raise BizError(code=Code.OCR_FAILED, msg=str(exc)) from exc
        except OcrError as exc:
            raise BizError(code=Code.OCR_FAILED, msg="OCR 识别失败，请稍后重试") from exc
        return Success(data=_result_out(result))
    finally:
        await file.close()
