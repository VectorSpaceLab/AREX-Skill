# VGen text-to-video troubleshooting

Use this reference when a T2V, HiGen, TF-T2V, VideoLCM, VideoComposer-style conditioning, or SR600 run fails before or during a long CUDA job.

## Dispatch and config failures

### `KeyError: <TASK_TYPE> not found in ENGINE/INFER_ENGINE registry`

- Confirm whether the command should be `train_net.py` or `inference.py`.
- `TASK_TYPE` must match a function registered into `ENGINE` or `INFER_ENGINE` by imports under `tools/__init__.py`.
- Known repo-specific issue: `configs/higen_train.yaml` declares `TASK_TYPE: train_t2v_higen_entrance`, but the provided training entrypoint registers `train_t2v_entrance` and `train_videolcm_t2v_entrance`, not a HiGen-specific train function. For HiGen training work, use a temporary config with a valid trainer only after checking the generic trainer supports the HiGen UNet kwargs, or add a small code alias that registers the intended HiGen name.

### Config edits work from YAML but not from CLI overrides

VGen's positional overrides are raw strings for the common no-`_BASE` YAMLs. String path overrides are safe; numeric, boolean, list, and dict overrides can break later math. Prefer a copied YAML for `guide_scale`, `max_frames`, `partial_keys`, `video_compositions`, `double_frames_sr`, scheduler settings, or nested model fields.

### Wrong model family after an inference config loads

Many inference YAMLs carry `vldm_cfg`. The entrypoint first loads the base model/diffusion config from `vldm_cfg`, then applies the inference overrides. If a future agent points `vldm_cfg` at the wrong training config, the entrypoint can build the wrong UNet or miss required fields such as `video_compositions`.

## Checkpoint and asset failures

### `FileNotFoundError` for `test_model`, OpenCLIP, or autoencoder checkpoints

The code does not download weights automatically in the entrypoints. Check:

- `test_model` for the requested family.
- `embedder.pretrained`, commonly `models/open_clip_pytorch_model.bin`.
- `auto_encoder.pretrained`, commonly `models/v2-1_512-ema-pruned.ckpt` for TF-T2V/VideoLCM.
- SR600 `models/sr_step_110000_ema.pth`.

Use repo-relative model paths in YAML or safe string CLI overrides. Do not put machine-specific absolute paths into reusable configs.

### `load_state_dict` strict mismatch

- Match the checkpoint to the config family (`UNetSD_T2VBase`, `UNetSD_HiGen`, `UNetSD_TFT2V`, `UNetSD_VideoLCM`, or `UNetSD_SR600`).
- Watch 16-frame vs 32-frame TF-T2V checkpoints.
- Do not use DreamVideo, I2VGen, or InstructVideo checkpoints with this sub-skill's configs.

## CUDA and package failures

### CPU run fails even though imports succeed

Full VGen generation is GPU-native. Entrypoints call `.cuda()`, use NCCL/distributed setup outside debug paths, and query NVML. A CPU-only environment is not a substitute for T2V/HiGen/TF-T2V/VideoLCM/SR600 inference or training.

### Missing package errors

Typical required packages for these workflows include CUDA PyTorch, torchvision, xformers, open-clip-torch, fairscale, diffusers, transformers, einops, easydict, pynvml, imageio/imageio-ffmpeg, OpenCV, and NumPy compatible with OpenCV. VideoComposer-style conditioning also imports annotator modules for depth/sketch/canny paths.

The repo's old model smoke helper imports `thop` and `ptflops` unconditionally. The bundled `check_t2v_model_forward.py` separates forward smoke from optional complexity checks and gives an explicit install message if complexity packages are requested but missing.

### OpenCV/NumPy ABI errors

If `cv2` import fails with NumPy ABI messages, use an OpenCV-compatible NumPy version. The verified inspection environment used NumPy 1.x with headless OpenCV.

### `pynvml` or NVML errors

Inference entrypoints call `pynvml.nvmlInit()` during sampling. Install `pynvml` and run on a host where NVIDIA drivers expose NVML. For a pure model-forward smoke, use the bundled smoke script instead of full inference.

## List-file and dataset failures

### `ValueError: not enough values to unpack` around `split('|||')`

Training and VideoComposer-style lists require the triple-pipe delimiter:

```text
relative_file.mp4|||caption
```

Prompt-only inference lists do not use `|||`. Validate before running:

```bash
python sub-skills/text-to-video/scripts/preview_dataset.py --repo-root /path/to/VGen --config <config.yaml> --no-render --strict
```
### Demo data list contains files not present in `data/videos/`

Some demo list rows can reference videos that are not in a shallow or partial checkout. Use the preview script with strict validation, remove missing rows, or point `data_dir`, `data_dir_list`, or `test_list_path` at complete data.

### Manual seed suffix is parsed inconsistently

HiGen, SR600, and VideoComposer-style entrypoints parse `caption|manual_seed`. Plain ModelScope T2V and TF-T2V text inference treat the whole line as the caption. Do not add `|seed` to a list unless the target entrypoint supports it.

### Dataset preview helper from `test_func/` fails

Use the bundled preview script. The repo helper has stale issues such as a missing `torch` import in one path and an `artist/font/...` font path in another path. The bundled script resolves the repo root, imports dependencies lazily, uses the bundled font when present, and avoids destructive output deletion.

## VideoComposer-style conditioning failures

### Condition outputs are missing or only one condition appears

The `partial_keys` field controls outputs. Defaults are usually:

```yaml
partial_keys:
  - ['y', 'depth']
  - ['y', 'sketch']
  - ['y', 'local_image']
```

Each partial-key group produces a separate file named with `condition_<keys>`. To add a condition, edit a temporary YAML and make sure the corresponding data generator and model embedding exist.

### Motion conditioning does not behave as expected

`video_compositions` includes `motion`, but the motion-vector extraction path is commented out in the vcomposer entrypoints. Treat motion as not operational unless a future code change wires and verifies motion-vector extraction.

### Depth/sketch annotator failures

The vcomposer entrypoints import MiDaS depth and PiDiNet/sketch cleaner helpers. Missing annotator weights, incompatible CUDA kernels, or model-download restrictions can fail before sampling. For a text-only TF-T2V or VideoLCM run, use the non-vcomposer configs instead.

### High-resolution vcomposer OOM

`configs/tft2v_vcomposer_896x512_infer.yaml` raises resolution while keeping many condition modules available. Reduce `max_frames`, use the 448x256 vcomposer config, lower `decoder_bs`/`chunk_size`, or run on a larger GPU.

## SR600 failures

### SR run cannot find low-resolution videos

SR600 reconstructs expected low-res paths from `log_dir`, the list stem, rank/index, condition keys for vcomposer, and sanitized captions. Confirm:

- The base low-res generation already completed.
- The SR config uses the same list file and compatible `partial_keys`.
- `log_dir` points to the same parent workspace used by low-res inference.
- Captions were not edited between low-res generation and SR.

### 16-frame videos fail in SR600

The SR model path expects 32-frame-style input. For 16-frame TF-T2V or VideoLCM sources, use a config with `double_frames_sr: True`; it duplicates frames for SR input and drops duplicates after sampling.

### SR output is saved but quality is poor

Check that the low-res video path matched the intended source. If SR silently read a different stale file with the same sanitized caption stem, delete stale workspace outputs or use a fresh `log_dir` before rerunning.

## Memory and throughput triage

- Reduce `decoder_bs` first if failure happens during autoencoder decode.
- Reduce `chunk_size` if failure happens during latent encode/decode chunks.
- Reduce `max_frames` or choose the 16-frame config before reducing resolution.
- For VideoLCM, `num_inference_steps` defaults to 4; raising it increases time and memory.
- Keep `use_fp16: True` on supported CUDA hardware unless debugging numerical issues.

## Smoke-test guidance

Use `scripts/check_t2v_model_forward.py` when changing `UNet` fields or `video_compositions`. For exact latent geometry, use the family defaults such as 16 frames at 32x56 latents for 448x256 output. For a lightweight code-path smoke, use smaller latent sizes and let the script adjust synthetic conditioning resolution.
