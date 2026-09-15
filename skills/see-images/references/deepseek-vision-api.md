# DeepSeek Vision API - verified reference

Source: <https://api-docs.deepseek.com/zh-cn/guides/vision>
Values marked **(tested)** were confirmed by live calls, not only read from docs.

## Endpoint and request shape

OpenAI-compatible chat completions at `https://api.deepseek.com`, `content` as a block array:

```json
{
  "model": "deepseek-flash",
  "messages": [{
    "role": "user",
    "content": [
      {"type": "text", "text": "这张图片里有什么？"},
      {"type": "image_url", "image_url": {"url": "data:image/png;base64,<B64>", "detail": "high"}}
    ]
  }]
}
```

Three ways to supply an image:

| Way | Block | Notes |
| --- | --- | --- |
| Inline base64 | `image_url.url = "data:image/png;base64,..."` | counts toward the 48 MiB body limit |
| Remote URL | `image_url.url = "https://..."` | max 8192 chars, fetch within 60 s |
| Files API | `{"type": "file", "file_id": "file-api-..."}` | up to 64 MiB per image |

`image_url` may also be `{"type":"file","file_data":"data:image/jpeg;base64,...","filename":"a.jpg"}`.

## Limits

| Limit | Value |
| --- | --- |
| Supported formats | JPEG, PNG, GIF, WebP |
| External URL length | 8192 chars |
| Request body | 48 MiB |
| Single image (base64 / URL) | 32 MiB **(tested)** |
| Single image (Files API `file_id`) | 64 MiB |
| Images per request | 600 |
| Total image bytes per request | 64 MiB without `file_id`, up to 200 MiB with |
| Max dimension | 8192 px per side **(tested)**; 4096 px when >=15 images in one request |
| Image placement | `user` messages only |

`detail` values: `low` (resize to 512x512, cheaper) / `high` / `original` / `auto`
(`auto` currently equals `original`).

## Format detection is by content, not header

Uploaded bytes are sniffed; the declared MIME and file extension are ignored. Verified:

| Bytes | Declared MIME | Result |
| --- | --- | --- |
| PNG | `image/jpeg` | accepted |
| PNG | `image/gif` | accepted |
| PNG | `text/plain` | 400 rejected |
| PNG | `application/octet-stream` | 400 rejected |
| BMP | `image/bmp` | 400 rejected |
| TIFF | `image/tiff` | 400 rejected |

Consequence: re-encoding a BMP to PNG fixes it, while renaming it does not.

## Error strings

- `image file size exceeds limit 32 MB` - over the single-image cap.
- `You have uploaded an unsupported image. Please make sure your image is valid and has one of the following...`
  - unsupported format (BMP/TIFF), a non-image MIME, or a side longer than 8192 px.

## Token accounting

Every image is scaled before the model sees it: below ~544x544 it is upscaled preserving
aspect ratio; above that it is downscaled to roughly 1300x1300 total pixels. Per-image cost is
therefore capped at **1024 tokens**, so a 2000x2000 and a 5000x5000 image cost the same. Sending
a bigger image does not buy more detail.

## Local stack (OpenHands / Agent Canvas) differences

These are separate from the API limits and can mislead:

| Layer | Limit | Location |
| --- | --- | --- |
| SDK inlining of remote http images | 20 MB (`OH_INLINE_IMAGE_MAX_MB`) | `openhands/sdk/llm/utils/image_inline.py` |
| SDK inline image cache | 64 MB total | same |
| Local stack accepted MIME types | jpeg, png, gif, webp, **bmp, tiff** | same - wider than the API |
| Message text length | 30000 chars (`max_message_chars`) | LLM profile |

The local stack accepting BMP/TIFF does **not** mean the API will: the API rejects them.

## Anthropic and Responses APIs

- Anthropic-compatible endpoint (`https://api.deepseek.com/anthropic`, `/messages`) uses an
  `image` block whose `source.type` is `base64` (needs `media_type`), `url`, or `file`
  (needs header `anthropic-beta: files-api-2025-04-14`).
- Responses API carries images in `input_image` blocks (`image_url` + `detail`), allowed in
  `user` / `developer` messages and in `function_call_output` / `custom_tool_call_output`
  items. `file_id` and `image_url` are mutually exclusive there.
