import { request } from '../request';

export function fetchOcrRecognize(file: File, options?: Api.Ocr.Options, signal?: AbortSignal) {
  const data = new FormData();
  data.append('file', file);
  if (options) data.append('options', JSON.stringify(options));
  return request<Api.Ocr.Result>({
    url: '/system-manage/ocr/recognize',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
    signal
  });
}
