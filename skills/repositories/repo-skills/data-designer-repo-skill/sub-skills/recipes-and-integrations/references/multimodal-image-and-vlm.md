# Multimodal, Image, and VLM Recipe Patterns

## Purpose

Read this when adapting image-context tutorials, image generation/editing recipes, rich document image recipes, or long-document VLM pipelines. For exact config class fields, use [`../../config-authoring/SKILL.md`](../../config-authoring/SKILL.md). For actually running preview/create/export, use [`../../generation-runtime/SKILL.md`](../../generation-runtime/SKILL.md).

## Choose the right pattern

| Need | Pattern | Safe adaptation notes |
| --- | --- | --- |
| Generate text from existing images | Seed dataset + `LLMTextColumnConfig(..., multi_modal_context=[ImageContext(...)])` | Verify seed has image column and chosen model alias is VLM-capable before any preview |
| Generate new images from text | `ImageColumnConfig` + image model `ModelConfig` with `ImageInferenceParams` | Treat all model options in `extra_body` as provider-specific |
| Edit images or chain image columns | Second `ImageColumnConfig` with `ImageContext(column_name="previous_image")` | Requires an autoregressive image model that accepts image context; diffusion routes do not consume context |
| Build VQA seeds from generated images | Create images, then export seed parquet with base64 bytes and image metadata | Local file/base64 checks are safe; image generation itself is credentialed |
| OCR or VQA over documents | Long-document VLM sequence using `png_images_base64` seed rows | GPU/Docker/vLLM and model endpoint required for actual execution |
| Use audio/video context | Same `multi_modal_context` field with audio/video context objects | Verify model/provider supports every modality; local audio/video paths are not auto-converted like images |

## Image context rules that matter in recipes

`ImageContext` accepts one image value, a list of image values, or a JSON-serialized list. In auto mode, each value resolves as follows:

1. If it looks like a file path that exists under the generation artifact base path, DataDesigner loads the file and converts it to base64. This is why image-to-image editing can use image paths produced by `create`.
2. If it is an HTTP(S) image URL, DataDesigner passes it as a URL context.
3. Otherwise DataDesigner treats it as base64 image data.

For base64 seed columns:

- Store raw base64 without a `data:<mime>;base64,` prefix unless the upstream system already provides a data URI.
- If you set `data_type=BASE64`, also set `image_format`.
- If a data URI is present, its media type must match any configured `image_format`.
- A base64 column can hold a single payload or a serialized/list value when a record needs multiple pages or images.

For image URLs and generated paths:

- URLs depend on provider URL support and file-size limits.
- Generated images in preview are base64 strings in the in-memory dataframe.
- Generated images in create mode are saved on disk and the dataset stores relative image paths.
- When chaining created images into later image context, use the generated image column name; DataDesigner resolves relative paths from the artifact base.

## Image model configuration patterns

Image recipes use `ImageInferenceParams` so DataDesigner treats the model as image-generating. Image options are model/provider-specific and belong in `extra_body`.

The tested OpenRouter image recipes use this request-shape pattern:

```python
dd.ImageInferenceParams(
    extra_body={
        "modalities": ["image", "text"],
        "image_config": {
            "aspect_ratio": "4:3",  # recipe-specific
            "image_size": "1K",
        },
    },
    max_parallel_requests=10,
)
```

Do not replace that with a `generationConfig` shape for those OpenRouter chat-image recipes; the image recipe tests explicitly check that `generationConfig` is absent. Other providers may need different `extra_body` keys, so do not generalize this shape beyond matching providers/models.

`skip_health_check=True` appears in several image recipe model configs. Treat that as a provider-compatibility choice, not proof that the model endpoint will work. If execution is authorized, run a tiny preview or `check_models` equivalent through generation-runtime before scale-up.

## Seed and metadata patterns for image/VQA recipes

Use seed and person-data details from config-authoring; this section only names recipe-level shapes.

### Existing images as seed data

A safe seed table for VLM tasks usually includes:

- `image_base64` or `png_images_base64` for raw base64 image bytes; long-doc recipes use a JSON array of PNG base64 strings.
- Metadata columns that explain what produced or describes the image, such as document type, visual type, image format, MIME type, width, and height.
- Any labels or ground truth needed by a downstream judge or human review step.

Before adding the seed to a config, do a local check that the file/parquet is readable, the image column exists, at least one image decodes, and the metadata columns referenced by prompts exist.

### Rich document image recipes

The rich document image pattern generates dense business-document page images with controlled metadata, then can export a VQA-ready seed parquet. A safe adaptation should preserve:

- a row-level variation key to discourage duplicates;
- metadata columns for document type and visual/layout/condition controls;
- an image column named for the generated artifact;
- optional export to `image_base64`, `image_format`, `image_mime_type`, width/height, and metadata columns.

Do not upload or publish generated document images without reviewing whether the prompt may have produced sensitive-looking logos, people, or real-world marks.

## Long-document VLM pipeline sequence

The long-document recipes are a reference-only pipeline family because actual execution needs downloads, vLLM endpoints, Docker, GPUs, large context windows, or frontier model endpoints.

A safe adaptation should model the stages without executing them unless explicitly authorized:

1. **Seed preparation** — stream/download PDFs, render each page to PNG, and write seed parquets:
   - per-page rows for single-page tasks;
   - windowed rows with consecutive pages;
   - whole-document rows with all pages.
2. **OCR** — use a Nemotron-Parse-compatible VLM endpoint to produce transcribed text and bounding-box metadata.
3. **Text QA** — use OCR text to produce question/answer pairs and text-grounded relevance/correctness checks.
4. **Page classification** — use page image context to classify visual element categories and reasoning complexity.
5. **Visual QA** — use `png_images_base64` plus page classification to generate and judge visual questions.
6. **Single-page, windowed, and whole-document QA** — use image arrays sized to the page scope and capture reasoning separately when the model/provider supports it.
7. **Frontier judge** — evaluate question/answer rows against image context with explicit rubric scores and a weighted composite.

Mark these scripts GPU/Docker-bound when they name local vLLM services, multi-H100 launch commands, `--trust-remote-code`, large `--max-model-len`, or model-specific reasoning parsers.

## Domain and safety caveats for synthetic images

Image recipes include domains such as agriculture, airport/security scans, drone inspection, autonomous vehicle traffic scenes, humanoid robot scene understanding, medical X-ray style images, product images, pets, and rich documents. Keep these caveats in the adapted plan:

- Synthetic images are not substitutes for real medical, autonomy, surveillance, safety, or field validation data.
- Avoid prompts that create sensitive-facility targeting, surveillance, evasion, real-patient, or real-identity claims.
- For medical images, state that outputs are for AI research/education/prototyping only and not diagnosis or treatment.
- For robotics/autonomy/drone domains, use generated images for review sets, visual QA, calibration, and demos, not safety validation.

## Local dry-run checklist

Use these checks before any model call:

- The config can be constructed without importing large recipe source files.
- Every prompt reference is backed by a sampler, seed, or upstream column.
- The selected model alias has image/VLM generation type and a configured provider.
- Base64 seed values decode and match declared image format.
- URL context values are reachable only if the user permits network access.
- For created image datasets, expected relative image paths exist under the artifact base before using them as downstream context.
- For long-document pipelines, count pages/images per row and reject rows that exceed model context or provider limits.

If any check requires credentials, network, Docker, or GPUs, stop and ask for authorization or produce a reference-only plan.
