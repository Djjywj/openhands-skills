---
name: image-processing
description: Deterministically manipulate or transform existing image files - downscaling, cropping, format conversion, compression, filtering, edge detection, or scripted pixel pipelines. Use when the deliverable is a re-encoded or derived image file, or data extracted by code. For reading, describing, or answering questions about what an image shows, use the `see-images` skill instead.
---

# Image Processing

## When to Use

- When the task requires deterministic manipulation of existing image files, such as downscaling, trimming, format conversion, or compression
- When the task requires traditional computer vision operations, such as filtering, edge detection, or object recognition

Do not use this skill to read or describe an image. That is `see-images`, which delegates to a
vision model.

## Image Processing Best Practices

- For image understanding tasks like description or Q&A, use the `see-images` skill, which delegates the pixels to a vision model, instead of writing detection code
- For basic image manipulation tasks like downscaling, cropping, format conversion, and compression, use Python with PIL/Pillow
- For traditional computer vision operations like filtering, edge detection, and object recognition, use OpenCV
- Reserve OpenCV for deterministic pixel-level or geometric pipelines whose result is data or a re-encoded file; for recognizing, classifying, or describing what an image contains, the `see-images` skill is more accurate and cheaper than hand-written detection code
- DO NOT use deterministic processing where new visual content must be created; deterministic processing only rearranges or re-encodes pixels that already exist

## No Image Generation

This environment has no image-generation or AI image-editing capability: there is no generation
tool and no such skill. Do not claim to generate, edit, upscale, restore, or restyle an image,
and do not substitute a deterministic pipeline for it - PIL, OpenCV, canvas, SVG, and plotting
libraries can only rearrange or re-encode pixels that already exist, so using them here would
produce something the user did not ask for while appearing to fulfil the request.

When the request needs new visual content, say plainly that image generation is not available
in this environment rather than faking it with code. This applies to:

- Semantic edits, style transfer, upscaling, restoration, or enhancement
- Text added or laid out onto a visual - text-bearing images must be generated with their text
  already in place
- Annotations (labels, arrows, callouts, dimension marks, highlight boxes) when the annotated
  image is itself the deliverable
- Architectural drawings, floor plans, interior layouts, product design views, and engineering
  sketches
- New visuals, charts, or structured diagrams that are not transformations of an existing image

Two narrow exceptions, where code is still correct:

- The user needs annotation **coordinates as data**, or reproducible machine-generated overlays
  such as evaluation or dataset artifacts
- The user requires exact scale, verified measurements, or editable CAD/layout source files -
  a deterministic layout then serves the stated requirement

## Route Boundaries

- When a resize or crop would change the aspect ratio, preserve all content unless the user explicitly accepts edge loss; do not silently crop content away
- Prefer a minimal, reversible transformation over a clever one, and state plainly which pixels changed

## Delivering Results

- Write transformed output to a new file path; MUST NOT overwrite a user-provided original unless the user asked for in-place replacement
- When a transformation can silently damage the result, such as unintended aspect ratio, rotation, color-space, or transparency loss, confirm the output once via the `see-images` skill; a single pass/fail check is sufficient, do not open an extended inspection loop
- Deliver the resulting image files, and keep the accompanying script only when the user needs to rerun or adjust the transformation
