# Generic OCR

The project includes local OCR powered by [RapidOCR](https://github.com/RapidAI/RapidOCR) with the ONNX Runtime CPU backend. Recognition runs locally or inside the container; no online OCR API is used.

OCR is a generic capability: it converts an image to text and boxes only. Business fields such as order numbers, part numbers or ticket codes belong to the caller.

## Install

OCR is an optional extra because its dependencies are relatively large:

```bash
uv sync --extra ocr
```

The production Docker image installs this extra in `deploy/app.Dockerfile`. If it is missing, the OCR endpoint returns business code `2411` and other features continue to work.

Dependencies:

- `rapidocr==3.10.0`: Apache-2.0, about 27 MB wheel with bundled detection, orientation and recognition models.
- `onnxruntime`: MIT, CPU inference.
- `opencv-python-headless` is pulled by RapidOCR; no GUI libraries are required on servers.
- Keep RapidOCR's `MODEL_LICENSES.md` and the Baidu/PaddleOCR attribution when redistributing.

## Configuration

`.env` overrides:

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

| Key | Meaning |
|---|---|
| `OCR_ENABLED` | Enable or disable OCR |
| `OCR_MAX_IMAGE_MB` | Maximum upload size |
| `OCR_MAX_PIXELS` | Maximum decoded pixels |
| `OCR_MAX_ITEMS` | Maximum returned items; sets `truncated` |
| `OCR_MAX_SIDE` | Maximum inference side; larger images are scaled down and boxes mapped back |
| `OCR_TIMEOUT_SECONDS` | Request-level timeout |
| `OCR_QUEUE_TIMEOUT_SECONDS` | Wait timeout for an inference slot |
| `OCR_MAX_CONCURRENCY` | Concurrent inferences per process, default 1 |

## API

`POST /api/v1/system-manage/ocr/recognize`

- Requires authentication and system API permission (`DependPermission`); it is not public.
- `multipart/form-data`:
  - `file`: JPG / PNG / GIF / WebP.
  - `options` (optional): JSON string.

```json
{
  "useCls": true,
  "crop": { "x": 0, "y": 0, "width": 800, "height": 200 }
}
```

The response uses the standard `Success` envelope and camelCase fields:

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

Business codes:

| Code | Meaning |
|---|---|
| `2411` | OCR dependency missing or disabled |
| `2412` | Invalid, unsupported or oversized image |
| `2413` | Inference queue busy |
| `2414` | Recognition timeout |
| `2415` | Recognition failed |

## Frontend component

```vue
<script setup lang="ts">
import OcrRecognizer from '@/components/advanced/ocr-recognizer.vue';

const ocr = ref<Api.Ocr.Result | null>(null);
</script>

<template>
  <OcrRecognizer v-model:value="ocr" :max-size-mb="10" @recognized="handleRecognized" />
</template>
```

It supports file selection, drag and drop, pasted screenshots, local preview with boxes, editable text, confidence labels and low-confidence warnings. Images are not stored in the image library and are not retained.

## Security and performance

- Only `UploadFile` is accepted; no server paths or remote URLs.
- Images are decoded in memory and released after recognition; nothing is written to disk or logs.
- Defaults: 10 MB, 25 million pixels, at most 500 items.
- The engine is lazy-loaded per process and reused; inference is serialized per process by default.
- Inference runs in a worker thread and does not block the event loop. The timeout is request-level; native inference cannot be force-killed. Downscale large images first.
- With multiple workers, every worker that handles OCR loads its own model. Reduce `WORKERS`, keep `OCR_MAX_CONCURRENCY=1`, or move OCR to a dedicated local service when memory is tight.
- Do not log recognized text. Business audit logs should contain IDs, counts and result codes only.

## Tests

`tests/test_ocr.py` uses a fake engine to cover result mapping, crop, resize coordinates, invalid images, missing dependency, authorization and business codes. The frontend test covers selection, recognition, low confidence, text correction, invalid files and paste.
