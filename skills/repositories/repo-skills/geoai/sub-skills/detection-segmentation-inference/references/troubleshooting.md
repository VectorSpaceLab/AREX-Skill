# Troubleshooting

This page focuses on inference-time failures and the quickest safe fixes.

## Missing optional packages

Common missing packages and the workflows they enable:

- `rfdetr` / `supervision` → RF-DETR detection and segmentation.
- `omniwatermask` → water segmentation.
- `omnicloudmask` → cloud and cloud-shadow segmentation.
- `multiclean` → mask cleanup and small-island removal.
- `opensr_model` → super-resolution.
- `onnx` / `onnxruntime` → ONNX export and runtime.
- `transformers` / `leafmap` / `torch` → SAM, CLIPSeg, and HF-style auto inference routes.

Safe response:

1. Confirm the package is actually needed for the selected workflow.
2. Prefer a different workflow family only if the geometry semantics still match.
3. Do not make the helper download weights or datasets just to satisfy preflight.

## Checkpoint, model, class, or channel mismatches

Symptoms:

- shape errors in the model head
- empty or noisy masks
- wrong class labels
- RGB output from a multispectral source that should have used more bands

Fixes:

- Set `num_channels` to match the checkpoint and source imagery.
- Set `num_classes` to match the prediction head.
- For 4-band NAIP imagery, prefer a 4-channel checkpoint or explicit 4-channel model settings.
- For Grounding DINO / CLIP-style prompts, make sure text prompts are normalized as the API expects.
- For `SamGeo`, call `set_image()` before prompt-mode `predict()`.

Special note for the 4-band NAIP + local Mask R-CNN case:

- Use a checkpoint whose first layer and head were trained for four channels.
- Keep `window_size > overlap` and start with a moderate tile size.
- Use a georeferenced vector output path such as `.geojson` or `.gpkg` if you want polygons.

## Window, overlap, and band-order problems

Symptoms:

- seams between tiles
- edge artifacts
- misaligned masks
- water/cloud/SR workflows reading the wrong channels

Fixes:

- Keep `overlap < tile_size` or `overlap < window_size`.
- Use smaller tiles and batch sizes when memory is tight.
- Remember that band indices are 1-based.
- Water presets:
  - NAIP → `[1, 2, 3, 4]`
  - Sentinel-2 → `[3, 2, 1, 4]`
  - Landsat → `[4, 3, 2, 5]`
- Cloud masking wants explicit red, green, and NIR band numbers.
- Super-resolution wants exactly four bands in RGB+NIR order.

## CUDA, MPS, and CPU memory

Symptoms:

- CUDA out-of-memory
- very slow CPU inference
- MPS fallback warnings
- large rasters failing partway through a tiled run

Fixes:

- Reduce `tile_size`, `window_size`, or `patch_size` first.
- Reduce `batch_size` second.
- Reduce `overlap` only if you can tolerate more seam risk.
- Prefer smaller RF-DETR variants or a smaller HF model when memory is tight.
- For super-resolution, keep the default `patch_size=128` unless you have a strong reason to change it.
- For prompt segmentation, use the lighter CLIPSeg or text-prompt route if SAM is too heavy.

## Vectorization and output extensions

Symptoms:

- raster output written but no vectors appear
- `output_vector_path` is ignored or creates an unreadable file
- a cleaned mask cannot be saved

Fixes:

- Use a vector extension that the workflow can write: `.geojson`, `.gpkg`, `.shp`, `.fgb`, or `.parquet` when supported.
- Make sure the source has CRS and transform metadata before asking for polygons.
- Clean noisy masks with `geoai.tools.multiclean` before vectorization.
- Confirm the parent directory exists and is writable.

If vectorization returns nothing, the mask may be empty, thresholded away, or missing georeferencing metadata.

## HF token, network, and cache issues

Symptoms:

- a model ID is provided but the workflow cannot find local weights
- an HF-backed call stalls on network access
- a cached model works on one machine but not another

Fixes:

- Prefer local checkpoint paths when you want a strictly offline run.
- If a Hugging Face model ID is required, make sure the cache is populated and the network is allowed.
- Use cache-related environment variables such as `HF_HOME` and `HUGGINGFACE_HUB_CACHE` if the environment needs a predictable cache location.
- Only use tokens when the remote model host actually requires them.

Safe distinction:

- `AutoGeoModel.from_pretrained`, `download_model_from_hf`, `predict_detector_from_hub`, `rfdetr_detect_from_hub`, and `super_resolution` can all end up resolving remote resources.
- The preflight helper in this sub-skill never downloads them; it only reports the dependency or cache requirement.

## RF-DETR missing-extra fallback

If `check_rfdetr_available()` fails, do not silently switch to another detector family.

- RF-DETR detection and RF-DETR-Seg geometry are different from standard detector outputs.
- Report the missing optional package.
- Ask for an installed RF-DETR environment or route the task to a non-RF-DETR detector only if the user explicitly accepts that change.

## Prompt segmentation surprises

- `GroundedSAM` prefers lower-case labels and a period suffix when using text prompts.
- `CLIPSegmentation` is text-prompt-only and does not behave like Grounding DINO + SAM.
- `SamGeo` automatic mode and prompt mode are different entry points; use the right one for the prompt style.

## ONNX export and runtime issues

- `export_to_onnx` requires the original PyTorch/HF stack and a task that can be inferred or provided.
- `ONNXGeoModel` needs `onnxruntime` and the `.onnx` file plus any JSON sidecar metadata.
- If the model output shape is unexpected, check the task mapping and the ONNX sidecar first.
