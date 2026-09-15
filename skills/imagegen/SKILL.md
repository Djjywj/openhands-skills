---
name: imagegen
description: Generate a new image from a text prompt (text-to-image) using a free, no-API-key endpoint. Use when the deliverable is a brand-new visual - an illustration, icon, logo concept, scene, or artwork - and no source image exists yet. For editing, upscaling, or restoring an existing image, or reading what an image shows, see the notes below on what this environment cannot do.
---

# Image Generation

Turn a text prompt into an image file.

## What This Can and Cannot Do

Verify before promising anything. In this environment:

| Request | Status |
| --- | --- |
| Text-to-image (new image from a prompt) | **Works**, no API key needed |
| Image editing / inpainting / style transfer | **Not available** anonymously (HTTP 500 without a token) |
| Upscaling, restoring, de-blurring an existing image | **Not available** |
| Reading or describing an existing image | Not this skill - use `see-images` |

There is no image-generation model on the configured DeepSeek endpoint (its
`/images/generations` returns 404), so this skill uses Pollinations.AI instead. It needs no
account and no key.

When someone asks for editing or upscaling, say plainly that it is not available rather than
faking it with PIL or OpenCV - those can only rearrange pixels that already exist.

## Usage

```bash
python3 <this-skill-path>/scripts/gen.py "a watercolor fox reading a book, soft window light"
python3 <this-skill-path>/scripts/gen.py "minimal logo for a coffee shop" --out logo.png -W 1024 -H 1024
python3 <this-skill-path>/scripts/gen.py "a blue circle on white" --seed 42
```

| Flag | Purpose |
| --- | --- |
| `--out`, `-o` | Output path (default `generated.png`, or `generated-<seed>.png`) |
| `--width`/`--height`, `-W`/`-H` | Size, 64-2048 (default 1024x1024). The service caps anonymous requests near 768, so larger values come back smaller - the script reports the real size |
| `--seed`, `-s` | Fix the seed to reproduce an image exactly |
| `--model` | Model name; **ignored without a token** |
| `--no-logo`, `--private` | Watermark / hidden generation; **only honoured with a token** |
| `--timeout` | Request timeout in seconds (default 180) |

Environment: set `POLLINATIONS_TOKEN` to raise limits and enable the model, watermark, and
private options. Without it, anonymous access is text-to-image only and limits are lower.

## Prompting

Be concrete: subject, style, lighting, composition, and mood each change the result. Vague
prompts give generic output.

```
a red fox curled asleep on a mossy rock, morning mist, soft diffuse light, photographic
```

Iterate rather than expecting the first try: keep the wording that worked, change one element
at a time, and reuse a `--seed` to hold the composition steady while you vary the prompt.

## Verify the Result

Never report success without looking at the file. Hand it to the `see-images` skill and check
that it shows what was asked for - generation silently ignores parts of a prompt, and a
plausible-looking image can still be the wrong subject.

Also expect a small `pollinations.ai` watermark in a corner unless a token is set. Say so
rather than letting the user discover it.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `did not return a usable image` with a byte count | Rejected parameter or rate limit. Simplify the prompt or reduce the size, then retry |
| HTTP 500 | Usually an unsupported option such as image editing without a token |
| Blank or wrong-subject image | Rewrite the prompt more specifically; fix a seed and change one thing at a time |
| Very slow | Large sizes take longer. Drop to 512x512 to iterate, then render the final at full size |

## Files

| Path | Purpose |
| --- | --- |
| `scripts/gen.py` | Generate an image from a prompt; validates the response is a real image |
