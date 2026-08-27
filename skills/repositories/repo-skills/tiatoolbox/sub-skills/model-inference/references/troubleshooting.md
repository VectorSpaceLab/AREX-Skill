# Model Inference Troubleshooting

## Network or Weight Download Surprises

Symptom: constructing an engine with `model="some-registry-key"` blocks, fails on Hugging Face, or violates an offline requirement.

Actions:

- If downloads are disallowed, require `weights="local_weights.pth"` or a custom model object.
- Use `scripts/model_registry_probe.py` only for safe registry inspection; it does not fetch weights.
- Do not call `get_pretrained_model()` as a key validation step in offline plans because it can fetch weights.
- Record whether the user authorized network access, uses a pre-populated cache, or supplied local weights.

## Model Key Typos and Case

Symptom: `Pretrained model ... does not exist` or CLI plan uses a visually similar key.

Actions:

- Run the registry probe with `--list-prefix` for the family prefix.
- Preserve exact hyphen/underscore spelling and dataset suffix from the registry.
- Do not silently switch task families, such as from `mapde-*` detection to `hovernet*` instance segmentation.
- Treat custom model names as API-only unless they also exist in the registry.

## Device Availability

Symptom: CUDA/MPS device errors, CPU fallback confusion, or multi-GPU wrapping surprises.

Actions:

- Default to `device="cpu"` in portable plans.
- Before using CUDA, check `torch.cuda.is_available()` and optionally `torch.cuda.device_count()`.
- Before using MPS, check PyTorch MPS availability on the target host.
- Lower `batch_size` first when moving from GPU to CPU.
- Keep `num_workers=0` for reliable debugging; increase only after a smoke run.

## Output Type Mismatch

Symptom: unsupported output type error, missing `save_dir`, or downstream cannot read output.

Actions:

- Use `dict` for in-memory smoke tests, `zarr` for large tensor outputs, `annotationstore` for spatial annotation workflows, and `qupath` for QuPath JSON interop.
- Do not use `annotationstore` with `DeepFeatureExtractor`; use `dict` or `zarr`.
- Provide `save_dir` for `zarr`, `annotationstore`, and `qupath` outputs, especially in WSI mode.
- Route visualization, overlay, and store editing to `../annotation-visualization/`.

## YAML Config and CLI JSON Quoting

Symptom: CLI rejects `--input-resolutions`, `--output-resolutions`, or `--class-dict`.

Actions:

- Pass JSON strings, not Python literals: `'[{"units":"mpp","resolution":0.5}]'`.
- Keep resolution objects as a list even for one head.
- Use shell-safe quoting and avoid smart quotes.
- When using `--yaml-config-path`, ensure the file contains the same shape as the registry `ioconfig.kwargs` for the relevant config class.

## Shape, Stride, and Resolution Mismatches

Symptom: patch extraction errors, unexpected output dimensions, or misaligned annotation coordinates.

Actions:

- Confirm `patch_input_shape` matches the model's expected input size.
- Confirm `patch_output_shape` for segmentation models; it may differ from input shape due to valid crops or model heads.
- Confirm `stride_shape` is positive and does not exceed the intended sampling plan.
- Keep all IO config resolution units consistent; do not mix `mpp`, `power`, and `baseline` in one config.
- For WSI metadata uncertainty, route reader/resolution diagnosis to `../wsi-io/`.

## Memory Pressure

Symptom: process is killed, Dask/Zarr work spills heavily, or large-slide post-processing stalls.

Actions:

- Reduce `batch_size` and set `num_workers=0` while debugging.
- Lower `memory_threshold` to trigger more conservative caching/tile behavior.
- Use `zarr` output for large dense predictions rather than keeping `dict` outputs in memory.
- For detector or multitask post-processing, set `postproc_tile_shape` or `tile_shape` when available.
- Test on a small crop or a few patches before a full WSI batch.

## Deprecated NucleusInstanceSegmentor

Symptom: code or CLI plan uses `NucleusInstanceSegmentor` or `nucleus-instance-segment`.

Actions:

- State that `NucleusInstanceSegmentor` is deprecated since 2.1.0.
- Migrate API plans to `MultiTaskSegmentor` with the same model key, weights, IO config, `output_type`, and `return_predictions` intent.
- Prefer CLI `multitask-segmentor` for new commands unless the user explicitly needs legacy behavior.
- Preserve `annotationstore` versus `zarr` semantics during migration.

## Pretrained Weight Licenses

Symptom: user asks whether a pretrained model can be used in a regulated, commercial, or redistribution workflow.

Actions:

- Explain that registry inspection only identifies model keys and Hugging Face repository ids.
- Require the user to review the upstream model and dataset license terms before relying on pretrained weights.
- Prefer local custom weights when provenance or redistribution constraints are unclear.
