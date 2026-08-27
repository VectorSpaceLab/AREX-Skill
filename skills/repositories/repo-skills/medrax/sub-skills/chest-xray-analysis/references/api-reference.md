# Chest-X-ray tool API reference

The public classes are LangChain `BaseTool` implementations exported by the
MedRAX tools package. The source-level `name` values are shown below; invoke
with the input fields, then inspect the returned value and metadata tuple. The
schemas intentionally describe image paths rather than image bytes or DICOM.

## Common input rule

`image_path: str` means a readable JPG/PNG path. `XRayVQATool` uses
`image_paths: list[str]`; `LlavaMedTool` accepts an optional `image_path`. These
implementations do not perform DICOM parsing. A path can exist and still fail
later if the file is unreadable or not an image.

## Classification

### `ChestXRayClassifierTool`

- Source tool name: `chest_xray_classifier`.
- Constructor: `ChestXRayClassifierTool(model_name="densenet121-res224-all", device="cuda")`.
  `device` may be requested as `cuda` or `cpu`; the model is moved to it.
- Input: `{ "image_path": str }`.
- Output: `(scores, metadata)`. `scores` maps the following 18 default
  TorchXRayVision labels to values in the source's 0–1 probability convention:

  `Atelectasis`, `Cardiomegaly`, `Consolidation`, `Edema`, `Effusion`,
  `Emphysema`, `Enlarged Cardiomediastinum`, `Fibrosis`, `Fracture`, `Hernia`,
  `Infiltration`, `Lung Lesion`, `Lung Opacity`, `Mass`, `Nodule`,
  `Pleural Thickening`, `Pneumonia`, `Pneumothorax`.

- Metadata includes `image_path` and `analysis_status`; failures are encoded
  as `scores={"error": message}` with `analysis_status="failed"`.
- The implementation center-crops and normalizes the image, removes extra
  channels by taking channel zero, and runs inference mode. It does not return
  a confidence interval, threshold, heatmap, or visualization.

## Segmentation

### `ChestXRaySegmentationTool`

- Source tool name: `chest_xray_segmentation`.
- Constructor: `ChestXRaySegmentationTool(device="cuda", temp_dir=<Path-compatible temporary directory>)`.
  The source default is a relative temporary directory; supply a caller-owned
  writable directory when output retention matters.
- Input:
  `{ "image_path": str, "organs": list[str] | None }`.
  `organs=None` requests all available targets.
- Exact valid organ names: `Left Clavicle`, `Right Clavicle`, `Left Scapula`,
  `Right Scapula`, `Left Lung`, `Right Lung`, `Left Hilus Pulmonis`,
  `Right Hilus Pulmonis`, `Heart`, `Aorta`, `Facies Diaphragmatica`,
  `Mediastinum`, `Weasand`, `Spine`. Matching is exact after whitespace trim.
- Output: `(output, metadata)`. `output` has:
  - `segmentation_image_path`: saved overlay PNG, or an error output on failure;
  - `metrics`: selected organs with `area_pixels`, `area_cm2`, `centroid`,
    `bbox`, `width`, `height`, `aspect_ratio`, `relative_position`,
    `mean_intensity`, `std_intensity`, and `confidence_score`.
- Metadata includes original/model sizes, requested and processed organs,
  `pixel_spacing_mm` (the implementation's fixed `0.2`), visualization path,
  input path, and status. A selected organ with an empty mask may be omitted
  from `metrics`; that is not a negative clinical finding.
- Coordinate conventions: centroids are `(y, x)`; bounding boxes are
  `(min_y, min_x, max_y, max_x)`. Relative `top` and `left` are normalized
  centroid positions; `center_dist` is normalized distance from image center.
- Masks are produced after center crop and resize to 512×512, then aligned back
  to the original array by the source's square-crop assumption. The fixed pixel
  spacing makes `area_cm2` approximate and unsuitable for ordinary JPG/PNG.

## Report generation

### `ChestXRayReportGeneratorTool`

- Source tool name: `chest_xray_report_generator`.
- Constructor: `ChestXRayReportGeneratorTool(cache_dir=<caller-managed model cache>, device="cuda")`.
  It loads two model/tokenizer/processor triplets: findings
  `IAMJB/chexpert-mimic-cxr-findings-baseline` and impression
  `IAMJB/chexpert-mimic-cxr-impression-baseline`.
- Input: `{ "image_path": str }`.
- Output: `(report_text, metadata)`. Successful text is exactly structured as
  `CHEST X-RAY REPORT`, then `FINDINGS:`, then `IMPRESSION:`. Metadata lists
  `sections_generated=["findings", "impression"]`. Failures return an error
  string and failed metadata.
- The implementation uses `VisionEncoderDecoderModel`, `BertTokenizer`, and
  `ViTImageProcessor` for each section, converts the image to RGB, resizes
  processor output to the model encoder image size if needed, and generates
  with one return sequence, max length 128, cache enabled, and beam width 2.
- No calibrated confidence, citations, localization, or visualization is
  returned. Treat both sections as a draft.

## CheXagent visual QA

### `XRayVQATool`

- Source tool name: `chest_xray_expert`.
- Constructor:
  `XRayVQATool(model_name="StanfordAIMI/CheXagent-2-3b", device="cuda", dtype=torch.bfloat16, cache_dir=None, **kwargs)`.
- Input:
  `{ "image_paths": list[str], "prompt": str, "max_new_tokens": int }`,
  where `max_new_tokens` defaults to `512`.
- Output: `({"response": str}, metadata)`. Metadata echoes image paths, prompt,
  token limit, and status. The tool checks every path before generation and
  returns an error object plus failed metadata for a missing path or inference
  failure.
- It formats one or more images into the tokenizer's chat input and uses
  deterministic generation (`do_sample=False`, one beam, cache enabled).
  There is no confidence score or visualization artifact.
- The constructor temporarily presents Transformers as version `4.40.0` while
  loading remote-code model components, then restores the prior version. Treat
  this as a compatibility constraint, not as a general environment fix.

## MAIRA-2 phrase grounding

### `XRayPhraseGroundingTool`

- Source tool name: `xray_phrase_grounding`.
- Constructor:
  `XRayPhraseGroundingTool(model_path="microsoft/maira-2", cache_dir=None, temp_dir=None, load_in_4bit=False, load_in_8bit=False, device="cuda")`.
  Do not set both quantization flags. `temp_dir` must be writable if a
  visualization is required.
- Input: `{ "image_path": str, "phrase": str, "max_new_tokens": int }`,
  with `max_new_tokens` defaulting to `300`.
- Output: `({"predictions": [...], "visualization_path": path_or_none}, metadata)`.
  Each prediction contains the returned phrase and
  `bounding_boxes.model_coordinates` plus
  `bounding_boxes.image_coordinates`.
- Coordinate convention: each model box is ordered
  `[x_min, y_min, x_max, y_max]` with normalized coordinates in the model's
  image space. `image_coordinates` are adjusted for the original PIL image
  width/height by `adjust_box_for_original_image_size`; use those for drawing
  on the original image. The overlay uses the image-coordinate boxes.
- Metadata includes original size, model input size, device, and status. An
  empty decoded prediction list returns `completed_no_finding` with no image;
  predictions without boxes are skipped. This is not the same as failed
  inference and is not a confidence score.

## Optional LLaVA-Med QA

### `LlavaMedTool`

- Source tool name: `llava_med_qa`.
- Constructor:
  `LlavaMedTool(model_path="microsoft/llava-med-v1.5-mistral-7b", cache_dir=<caller-managed model cache>, low_cpu_mem_usage=True, torch_dtype=torch.bfloat16, device="cuda", load_in_4bit=False, load_in_8bit=False, **kwargs)`.
- Input: `{ "question": str, "image_path": str | None }`. The implementation
  always builds an image-token prompt, even when no image is provided; use the
  image-backed mode for this sub-skill and treat image-less QA as optional.
- Output: `(answer_text, metadata)` with question, image path, and status. No
  confidence or visualization is returned.
- The implementation processes an optional PIL image, then unconditionally
  calls CUDA tensor helpers while preparing input. Do not promise CPU support
  merely because a `device` parameter exists; verify this separately before use.

## Optional RoentGen generation

### `ChestXRayGeneratorTool`

- Source tool name: `chest_xray_generator`.
- Constructor:
  `ChestXRayGeneratorTool(model_path=<manually supplied RoentGen directory>, cache_dir=<caller-managed cache>, temp_dir=None, device="cuda")`.
  The source has installation-local defaults for `model_path` and `cache_dir`;
  override them rather than relying on an unknown machine layout.
- Input: `prompt: str`, `height=512`, `width=512`,
  `num_inference_steps=75`, and `guidance_scale=4.0`.
- Output: `({"image_path": generated_png}, metadata)` with prompt, steps,
  guidance, device, image size, and status. Errors return an error object.
- The pipeline is loaded with Diffusers, moved to float32 and the requested
  device, and saves the first generated image. Manual weights are a hard
  prerequisite; the tool does not provide evidence about real findings.

## Evidence boundary

These details are derived from the implementation modules named
`classification.py`, `segmentation.py`, `report_generation.py`, `xray_vqa.py`,
`grounding.py`, `llava_med.py`, `generation.py`, and the tools export module.
The README's high-level report description differs from the inspected report
implementation: use the class behavior above for exact fields and sections.
