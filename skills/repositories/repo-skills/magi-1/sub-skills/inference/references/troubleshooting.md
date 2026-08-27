# Inference troubleshooting

Provenance: distilled from inference/common/config.py, inference/infra/distributed/dist_utils.py, inference/infra/checkpoint/checkpointing.py, inference/pipeline/entry.py, inference/pipeline/prompt_process.py, inference/pipeline/video_process.py, inference/model/dit/dit_model.py, README.md runtime notes, and example launch scripts.

## First response checklist

When a MAGI inference run fails, do these in order before changing model code:

1. Run `python3 scripts/magi_config_check.py <config.json> --world-size <expected-processes>`.
2. Rebuild the launch command with `python3 scripts/magi_command_builder.py ...` and compare mode-specific arguments.
3. Verify CUDA is available and the process count matches `pp_size * cp_size`.
4. Verify DiT, T5, VAE, and special-token asset paths exist.
5. Verify ffmpeg can read any image/video input and write the output directory.
6. Treat helper success as preflight only; full generation still needs downloaded checkpoints.

## Config parse failures

### `Missing fields in the configuration file`

Cause: `MagiConfig` requires every dataclass field in `model_config`, `runtime_config`, and `engine_config`, including fields with Python defaults.

Fix:

- Start from one of the release-family config files and edit a copy.
- Use `scripts/magi_config_check.py` to list missing fields.
- Do not delete architecture or schedule fields to make a shorter config.

### `Please set cfg_number: 1 in config.json for distill or quant model`

Cause: `engine_config.distill` or `engine_config.fp8_quant` is true but `runtime_config.cfg_number` is not `1`.

Fix: set `cfg_number` to `1` and make sure `load` points to a checkpoint family containing `inference_weight.distill` or `inference_weight.fp8` as appropriate.

### `Please set cfg_number: 3 in config.json for base model`

Cause: both `distill` and `fp8_quant` are false but `cfg_number` is not `3`.

Fix: set `cfg_number` to `3`, or switch to a distill/quant config as a whole.

## CUDA and distributed startup

### `assert torch.cuda.is_available()` or no CUDA devices

Cause: source distributed initialization requires CUDA even if some text embedding work can run on CPU.

Fix:

- Run on a CUDA host with a compatible PyTorch build.
- Do not claim CPU-only inference support for MAGI source generation.
- Re-check driver/CUDA/PyTorch compatibility before changing config.

### `assert config.engine_config.cp_size * config.engine_config.pp_size == torch.distributed.get_world_size()`

Cause: launched process count does not match config parallelism.

Fix examples:

- 4.5B example configs: use one process or keep `pp_size: 1`, `cp_size: 1`.
- 24B example configs: use `torchrun --nproc_per_node=8` for `pp_size: 1`, `cp_size: 8`.
- 24B on RTX 4090 x8 per README note: set `pp_size: 2`, `cp_size: 4`, and still launch 8 processes.
- Re-run `scripts/magi_config_check.py <config> --world-size <n>`.

### Hang or timeout in `init_process_group`

Likely causes:

- Missing or conflicting `MASTER_ADDR` / `MASTER_PORT` for single-process launches.
- A port still occupied by a prior failed run.
- Mismatched `--nproc_per_node`, `WORLD_SIZE`, `RANK`, or visible GPU count.
- NCCL topology or network issue.
- Slow startup with large checkpoints and too-small `distributed_timeout_minutes`.

Fix:

- For single-process 4.5B runs, export `MASTER_ADDR=localhost`, `MASTER_PORT=<free-port>`, `WORLD_SIZE=1`, and `RANK=0`.
- For multi-GPU runs, prefer `torchrun --rdzv-backend=c10d --rdzv-endpoint=localhost:<free-port>`.
- Increase `distributed_timeout_minutes` only after process counts and ports are correct.
- If NCCL/NVLS errors appear, try the 24B example environment variable `NCCL_ALGO=^NVLS` and keep `CUDA_DEVICE_MAX_CONNECTIONS=1` for that run.

### `Unsupported cp_strategy` or `Invalid CP strategy`

Cause: `cp_strategy` is not one of the source-supported values.

Fix:

- Use `none` only with `cp_size: 1`.
- Use `cp_ulysses` for Hopper/newer GPU strategies when matching example configs.
- Use `cp_shuffle_overlap` for RTX 4090/older strategies when needed.
- Keep `cp_size * pp_size` equal to world size.

## Checkpoint and asset failures

### `Ckpt directory ... does not exist or empty`

Cause: `runtime_config.load` is wrong, or the loader-appended subdirectory is absent.

Fix:

- Base model expects `<load>/inference_weight`.
- Distill model expects `<load>/inference_weight.distill`.
- FP8 quant model expects `<load>/inference_weight.fp8`.
- Repoint `load` to the MAGI DiT checkpoint family root, not directly to an unrelated file.
- Use `scripts/magi_config_check.py <config> --check-paths --repo-root <magi-source-root>` for a no-load preflight.

### Safetensors file or index not found

Cause: the selected inference-weight directory lacks `model.safetensors`, `model.safetensors.index.json`, or referenced shard files.

Fix:

- Verify the checkpoint download completed.
- Verify shard names in the index match files on disk.
- If shards are compressed as `.zst`, ensure decompression support is installed.

### T5 or VAE loading errors

Cause: `t5_pretrained` or `vae_pretrained` points to a missing, incomplete, or incompatible local cache.

Fix:

- Validate both paths with the config checker.
- Keep T5/VAE checkpoint families paired with the MAGI release family.
- For memory pressure, use `OFFLOAD_T5_CACHE=true` and `OFFLOAD_VAE_CACHE=true`.
- For 4.5B, example configs put T5 on CPU; for 24B, examples put T5 on CUDA. Changing `t5_device` trades memory for latency.

### `special_tokens.npz` missing at import time

Cause: prompt processing loads special-token assets when the module imports. The default asset path is relative to the MAGI source tree.

Fix:

- Ensure the source asset exists at the default location, or set `SPECIAL_TOKEN_PATH` to the local special-token file before running.
- If using a packaged source layout, verify that assets are included in the runtime image.

## Mode and media failures

### CLI says `--image_path is required for i2v mode`

Cause: `--mode i2v` was used without `--image_path`.

Fix: add `--image_path <image>` or change mode to `t2v`.

### CLI says `--prefix_video_path is required for v2v mode`

Cause: `--mode v2v` was used without `--prefix_video_path`.

Fix: add `--prefix_video_path <video>` or change mode.

### ffmpeg decode/encode error

Likely causes:

- ffmpeg executable or codec support is missing.
- The input image/video path is wrong or unreadable.
- The output directory does not exist or is not writable.
- Media is corrupt or in an unsupported container/codec.

Fix:

- Install ffmpeg in the runtime environment.
- Pre-create the output directory.
- Probe the media with ffmpeg or convert it to a common JPEG/PNG/MP4 input.
- Remember i2v resizes one image to config size, and v2v samples frames at config `fps` and uses the first 32 frames as source prefix context.

## Memory and performance

### CUDA out of memory during T5/VAE/DiT load or generation

Mitigations, least invasive first:

1. Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
2. Set `OFFLOAD_T5_CACHE=true` and `OFFLOAD_VAE_CACHE=true`.
3. Use a distill or distill+fp8 config with matching checkpoint paths.
4. Lower `video_size_h`, `video_size_w`, `num_frames`, or `window_size`; keep dimensions compatible with VAE/patching.
5. For 4.5B distill+fp8, README notes `window_size: 1` can fit smaller GPUs.
6. For 24B, use the intended multi-GPU process layout; do not try to force a 24B config into one process by editing only launch flags.
7. Reduce competing GPU processes and confirm visible device order.

### `flash_attn` or `flashinfer` import/runtime errors

Cause: incompatible wheel for the current PyTorch/CUDA stack, missing GPU capability, or missing package.

Fix:

- Match the wheel to PyTorch 2.4 and CUDA 12.4 when following the verified stack.
- Reinstall only in an isolated runtime environment; avoid mutating shared environments without approval.
- If using fp8 quant configs, treat `flashinfer-python` compatibility as required.

## API misuse and long-running processes

### API run hangs in an interactive process

Cause: `MagiPipeline(config_path)` initializes `torch.distributed` and model-parallel state. Reusing an interpreter after a failed run can leave global process state initialized.

Fix:

- Prefer a fresh `python3` process or `torchrun` launch per generation.
- If embedding in a service, isolate generation workers and cleanly terminate failed ranks.
- Keep `pp_size * cp_size` aligned with the worker launch topology.

### Debug run appears to succeed without real weights

Cause: `SKIP_LOAD_MODEL` can bypass DiT checkpoint loading for debug paths.

Fix: do not use debug/no-load runs as generation validation. A real smoke test must load MAGI DiT, T5, VAE, special tokens, generate an MP4, and verify the file is non-empty and playable.
