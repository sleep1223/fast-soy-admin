"""Generic OCR request/response schemas.

Only generic fields live here. Business-specific parsing belongs to the caller.
"""

from pydantic import ConfigDict, Field

from app.core.base_schema import SchemaBase


class OcrCrop(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    x: int = Field(ge=0, title="裁切起点 X")
    y: int = Field(ge=0, title="裁切起点 Y")
    width: int = Field(gt=0, title="裁切宽度")
    height: int = Field(gt=0, title="裁切高度")


class OcrOptions(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    crop: OcrCrop | None = Field(None, title="裁切区域")
    use_cls: bool = Field(True, title="启用文本方向分类")


class OcrItemOut(SchemaBase):
    text: str = Field(title="识别文本")
    confidence: float = Field(ge=0, le=1, title="置信度")
    box: list[list[int]] = Field(default_factory=list, title="文本框坐标")


class OcrResultOut(SchemaBase):
    text: str = Field(title="识别文本")
    items: list[OcrItemOut] = Field(default_factory=list, title="识别项")
    elapsed_ms: int = Field(ge=0, title="识别耗时毫秒")
    truncated: bool = Field(False, title="是否因条数限制截断")
    width: int = Field(gt=0, title="图片宽度")
    height: int = Field(gt=0, title="图片高度")
