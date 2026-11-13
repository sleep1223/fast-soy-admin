# 通用 OCR 图片识别

项目内置本地 OCR 能力，基于 [RapidOCR](https://github.com/RapidAI/RapidOCR) + ONNX Runtime CPU。识别全部在本机/容器内完成，不调用在线 OCR API。

OCR 是通用能力，只负责“图片 → 文本/识别项”，不包含订单号、项目号、工票码等业务字段。业务解析由调用方完成。

## 安装

OCR 依赖较重，作为可选 extra 提供：

```bash
uv sync --extra ocr
```

生产 Docker 镜像已在 `deploy/app.Dockerfile` 中安装该 extra。未安装时 OCR 接口返回业务码 `2411`，不影响其他功能。

依赖说明：

- `rapidocr==3.10.0`：Apache-2.0，wheel 约 27 MB，内置检测/方向分类/识别 3 个小模型。
- `onnxruntime`：CPU 推理，MIT。
- `rapidocr` 自带 `opencv-python-headless`，服务器无需 GUI 库。
- 模型许可与归属见 RapidOCR 的 `MODEL_LICENSES.md`；分发时请保留该文件及百度/PaddleOCR 归属说明。

## 配置

在 `.env` 中可按需覆盖：

```dotenv
OCR_ENABLED=true
OCR_MAX_IMAGE_MB=10
OCR_MAX_PIXELS=25000000
OCR_MAX_ITEMS=500
OCR_MAX_SIDE=1600
OCR_TIMEOUT_SECONDS=30
OCR_QUEUE_TIMEOUT_SECONDS=10
OCR_MAX_CONCURRENCY=1
```

| 配置 | 说明 |
|---|---|
| `OCR_ENABLED` | 是否启用 OCR |
| `OCR_MAX_IMAGE_MB` | 单张图片字节数上限 |
| `OCR_MAX_PIXELS` | 解码后像素上限 |
| `OCR_MAX_ITEMS` | 最多返回识别项数量，超出标记 `truncated` |
| `OCR_MAX_SIDE` | 推理前最大边；超过会等比缩小，坐标会映射回原图 |
| `OCR_TIMEOUT_SECONDS` | 请求级识别超时 |
| `OCR_QUEUE_TIMEOUT_SECONDS` | 等待推理槽位的超时 |
| `OCR_MAX_CONCURRENCY` | 单进程同时推理数量，默认 1 |

## API

`POST /api/v1/system-manage/ocr/recognize`

- 需要登录并通过系统 API 权限（`DependPermission`）；不是公开接口。
- `multipart/form-data`：
  - `file`：JPG / PNG / GIF / WebP。
  - `options`（可选）：JSON 字符串。

`options` 示例：

```json
{
  "useCls": true,
  "crop": { "x": 0, "y": 0, "width": 800, "height": 200 }
}
```

响应仍使用项目统一 `Success`，字段 camelCase：

```json
{
  "code": "0000",
  "msg": "OK",
  "data": {
    "text": "000123456\n000123457",
    "items": [
      {
        "text": "000123456",
        "confidence": 0.98,
        "box": [[0, 0], [100, 0], [100, 30], [0, 30]]
      }
    ],
    "elapsedMs": 320,
    "truncated": false,
    "width": 800,
    "height": 600
  }
}
```

业务码：

| 码 | 含义 |
|---|---|
| `2411` | OCR 组件未安装或已关闭 |
| `2412` | 图片无效、格式不支持或超限 |
| `2413` | 推理队列繁忙 |
| `2414` | 识别超时 |
| `2415` | 识别失败 |

## 前端组件

```vue
<script setup lang="ts">
import OcrRecognizer from '@/components/advanced/ocr-recognizer.vue';

const ocr = ref<Api.Ocr.Result | null>(null);
</script>

<template>
  <OcrRecognizer v-model:value="ocr" :max-size-mb="10" @recognized="handleRecognized" />
</template>
```

组件能力：

- 选择图片、拖拽、粘贴截图；
- 本地预览与识别框叠加；
- 显示原始文本、识别项、置信度、低置信度提示；
- 文本可编辑，修改后通过 `update:value` 返回；
- 图片只用于本次识别，不会进入系统图片库，也不会长期保存。

## 安全与性能

- 只接受 `UploadFile`，不接受服务器路径或远程 URL。
- 图片在内存中解码，识别后释放；不写磁盘、不写日志。
- 默认限制 10 MB、2500 万像素、最多 500 个识别项。
- 引擎按进程懒加载并复用；单进程默认串行推理，避免 CPU 争抢。
- 推理在线程中执行，不阻塞事件循环；超时是请求级超时，原生推理线程无法强制终止。超大图片或长时间推理请先缩小图片。
- 多 worker 部署时，每个处理过 OCR 的 worker 都会加载一份模型。内存紧张时请降低 `WORKERS`、保持 `OCR_MAX_CONCURRENCY=1`，或把 OCR 拆到独立本地服务。
- 不要把识别文本写入普通日志；业务侧如需审计，只记录 ID、数量和结果码。

## 测试

`tests/test_ocr.py` 使用 fake engine 覆盖结果映射、裁切、缩放坐标、无效图片、未安装、权限与业务码；不会加载真实模型。前端 `ocr-recognizer.test.ts` 覆盖选图、识别、低置信度、文本修正、非法文件与粘贴。
