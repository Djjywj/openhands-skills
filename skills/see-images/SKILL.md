---
name: see-images
description: This skill should be used whenever image content must actually be read - a user sends or references a screenshot, photo, diagram, chart, scanned text, or UI capture and expects an answer about what it shows ("what does this say", "who/what is in this image", "read the error in this screenshot", "描述这张图"). It also covers long or high-resolution screenshots whose text is unreadable at whole-image scale, and the case where the agent cannot even find the image the user sent. Use it even when the agent believes it cannot look at images, because it can delegate to a vision-capable model. Trigger phrases include "see this image", "look at this screenshot", "read the text in this image", "what's in this picture", "看图", "看截图", "这张图是什么", "识别图片文字", "图里写了什么", "我发的图片", "找不到图片", "这张图".
triggers:
- screenshot
- image
- vision
- ocr
- 看图
- 截图
- 图片
- 识别
- 这张图
- 长截图
---

# See Images by Delegating to a Vision Model

## Purpose

The agent driving a conversation cannot inspect image pixels. When a user sends a screenshot
or photo and asks about it, the agent must not say "I can't see images" and stop. Instead it
delegates the pixels to a vision-capable model (DeepSeek `deepseek-flash`), which returns a
text description the agent can reason about and relay.

This is not the agent developing vision. It is borrowing one. Results arrive as a text
transcript, so fine print, ambiguous glyphs, and subtle visual judgements may be wrong -
say so when precision matters.

Do not rely on the conversation's native image pass-through instead. It is unreliable in
practice: image blocks are dropped whenever `force_string_serializer` resolves to `None` and
the model name matches the SDK's `FORCE_STRING_SERIALIZER_MODELS` list (which includes
`deepseek`). Always route the pixels through `look.py`.

## Workflow

1. **Locate the image.** If it is a file in the workspace, use that path. If the user "sent"
   it in chat, pass `--latest` and skip the searching entirely - the script reads the
   conversation event log itself. (Chat images are also mirrored to `attachments/` by a
   daemon; see `references/finding-chat-images.md`.)
2. **Decide whether the whole image is readable.** For an ordinary screenshot or photo, read
   it whole - go to step 4. For a long browser screenshot, panorama, or dense scan, do the
   readability check in "Long and high-resolution images" below first.
3. **Tile only when the task actually needs it** (long/dense images), then read the tiles in
   order.
4. **Call the vision model.** Run the bundled script:

   ```bash
   python3 <this-skill-path>/scripts/look.py --latest "描述这张图，并逐字转录所有文字"
   python3 <this-skill-path>/scripts/look.py attachments/x.png "这个报错是什么原因"
   python3 <this-skill-path>/scripts/look.py a.png b.png "对比这两张图"
   ```

   `--latest` picks the newest image in the current conversation. Pass `--save out.png` to
   keep a copy in the workspace (do this when the user should be able to view or download it).
5. **Relay the answer**, attributing it to the model rather than to direct observation, and
   flag uncertainty for anything small or ambiguous.

## Long and high-resolution images

Whole-image reading scales the image down, and the loss is often **silent**: the model returns
a confident but wrong digit rather than an error. Verified on a 1200x6000 screenshot - the
whole-image read returned `555.50` where the file said `565.50`; reading the same region from a
tile returned `565.50` correctly. So for anything where exact text matters, check first.

Screen on geometry, then decide on readability. These are two different questions:

1. **Does the image match a geometry signal?** Longest side / shortest side >= 4, either side
   > 4096 px, or total pixels > 16,000,000. This means "check readability", never "must tile".
2. **Is the requested content actually readable?** Tile or crop only when scaling or density
   prevents reliable reading, or the user asked for tiles. A geometry match with readable
   content needs no preprocessing; an ordinary-size image with dense tiny text still does.

| Observed state | Action |
| --- | --- |
| Requested content is clear, whatever the dimensions | Read the whole image; do not tile |
| Only one region is unclear | Crop that region at original resolution |
| Content unreadable across the image | Tile, then read every tile in order |
| Readability not yet assessed | Assess a preview first; never tile on geometry alone |
| Content already blurred or cut off in the source | Tiling cannot recover it - report the limitation |

```bash
python3 <this-skill-path>/scripts/slice_image.py "<image>" --inspect-only
python3 <this-skill-path>/scripts/slice_image.py "<image>" --readability unreadable --mode vertical --output-dir <tiles>
```

`--mode vertical` for top-to-bottom screenshots, `horizontal` for panoramas, `grid` when both
dimensions need splitting. The default 12% overlap exists so no line is lost at a seam. The
script only inspects by default; `--force` is an explicit override and must not be added just
because a threshold matched.

Then read `manifest.json` and view every listed tile in manifest order (top-to-bottom,
left-to-right, or row-major). Do not skip a tile because its neighbours look similar. Reconcile
seams using the overlap - keep one copy of repeated content, and repair a cut word only when
another tile shows the complete version. Never concatenate fragments blindly: prefer the
clearer reading when they disagree, and flag what stays unresolved.

## Asking a good question

The prompt drives quality. State what is needed instead of a bare "what is this":

- Transcribe text exactly: `"逐字转录图中所有文字，保持大小写和标点不变"`
- Identify a specific region: `"只读右上角的小字"`
- Avoid confabulated identity: add `"如果无法确定，请明确说明无法确定，不要猜测"` for
  questions about who or where something is.
- For UI/screenshots: `"这是什么软件的什么对话框？完整转录框内文字，并解释报错含义"`

Raise `--detail` to `original` for dense small text; drop to `low` to cut cost when only the
gist matters.

## Handling limits automatically

The script normalises problem images before sending, so callers rarely need to intervene:

- BMP/TIFF and other formats the API rejects are re-encoded to JPEG.
- Images over 32 MiB, or with any side over 8192 px, are downscaled preserving aspect ratio.

See `references/deepseek-vision-api.md` for the full, empirically verified limit table and the
exact error strings the API returns.

## Key facts

- Model: `deepseek-flash` supports images; the chat/reasoner models do not.
- Formats: JPEG, PNG, GIF, WebP - detected from file **content**, not extension or MIME.
- Images may only appear in `user` messages; `system`/`assistant` images return HTTP 400.
- Per-image token cost is capped (1024), so a 2000x2000 and a 5000x5000 image cost the same;
  sending a larger image does not yield more detail. That is exactly why tiling is the fix for
  unreadable small text rather than sending the original at higher resolution.
- Without `--latest`/`--url`, ordinary file paths work, so this also handles workspace files,
  downloads, and images the agent generated itself.

## Constraints

- Never print, log, or commit the API key. The script reads it from the environment or
  decrypts a stored profile in memory; it never writes it to disk.
- Do not silently pass a real person's photo to a third-party API when the user's intent is
  identification of private individuals; describe the image content instead and decline to
  identify people unless they are public figures in an evident public context.
- Report what the model said, not what it was hoped to say. If the model is unsure, the answer
  is "unsure".

## Additional Resources

### Reference Files
- **`references/deepseek-vision-api.md`** - Verified request format, limits, and error catalogue.
- **`references/finding-chat-images.md`** - Where chat images live, how to recover them, and why
  the native pass-through is not dependable.

### Scripts
- **`scripts/look.py`** - Send one or more images to the vision model and print the answer.
- **`scripts/slice_image.py`** - Inspect image geometry and produce ordered overlapping tiles
  plus a reading-order manifest. Requires Pillow.
