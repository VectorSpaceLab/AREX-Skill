# CLI and API routes

Provenance: distilled from README.md sections 3 and 5, example/4.5B/run.sh, example/24B/run.sh, inference/pipeline/entry.py, inference/pipeline/pipeline.py, inference/pipeline/video_process.py, inference/pipeline/prompt_process.py, and inference/pipeline/video_generate.py.

## What MAGI inference expects

MAGI source-code inference is driven by a JSON config plus one prompt. The config supplies model size, checkpoint locations, generation dimensions, diffusion steps, and distributed layout. The run call chooses one of three modes:

| Mode | Meaning | Required input arguments | Output |
| --- | --- | --- | --- |
| `t2v` | Text-to-video | `--prompt`, `--output_path` | MP4 video saved with the configured FPS |
| `i2v` | Image-to-video | `--prompt`, `--image_path`, `--output_path` | MP4 video; the source image is resized to the configured video size and VAE-encoded as a prefix |
| `v2v` | Video-to-video / continuation | `--prompt`, `--prefix_video_path`, `--output_path` | MP4 video; the source path is decoded through ffmpeg, resized, and its first 32 frames are VAE-encoded as prefix context |

The source pipeline saves videos with ffmpeg/libx264. Input image/video decoding also depends on ffmpeg availability.

## CLI entry point

The source-code CLI entry point is `inference/pipeline/entry.py`. It accepts:

- `--config_file`: MAGI JSON config file.
- `--mode`: one of `t2v`, `i2v`, or `v2v`.
- `--prompt`: prompt string.
- `--image_path`: required only for `i2v`.
- `--prefix_video_path`: required only for `v2v`.
- `--output_path`: destination MP4 path.

The CLI constructs `MagiPipeline(config_file)` and dispatches to exactly one public method. It exits with an explicit error if `i2v` lacks `--image_path` or `v2v` lacks `--prefix_video_path`.

## Build commands safely

Prefer the bundled helper rather than copying the repository example shell scripts verbatim:

```bash
python3 scripts/magi_command_builder.py \
  --config-file example/4.5B/4.5B_base_config.json \
  --mode t2v \
  --prompt "A quiet lake at sunrise, cinematic camera movement" \
  --output-path outputs/lake.mp4
```

For `i2v`, add `--image-path <input-image>`. For `v2v`, add `--prefix-video-path <input-video>`. The helper prints a command and recommended environment exports; it does not execute inference.

### Single-process 4.5B pattern

Use this only when `engine_config.pp_size == 1` and `engine_config.cp_size == 1`:

```bash
cd <magi-source-root>
export MASTER_ADDR=localhost
export MASTER_PORT=6009
export WORLD_SIZE=1
export RANK=0
export PAD_HQ=1
export PAD_DURATION=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OFFLOAD_T5_CACHE=true
export OFFLOAD_VAE_CACHE=true
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
python3 inference/pipeline/entry.py \
  --config_file example/4.5B/4.5B_base_config.json \
  --mode t2v \
  --prompt "Good Boy" \
  --output_path outputs/output_t2v.mp4
```

The example 4.5B configs use `pp_size: 1` and `cp_size: 1`. README guidance says the 4.5B family is intended for a single GPU with at least 24 GB VRAM; the 4.5B distill+fp8 config can be made more memory-frugal by setting `window_size` to `1`.

### Multi-process 24B pattern

Use `torchrun` when `pp_size * cp_size > 1`. The 24B example configs use `pp_size: 1` and `cp_size: 8`, so the launched world size must be 8 unless you edit both config and launch together.

```bash
cd <magi-source-root>
export CUDA_DEVICE_MAX_CONNECTIONS=1
export NCCL_ALGO=^NVLS
export PAD_HQ=1
export PAD_DURATION=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export OFFLOAD_T5_CACHE=true
export OFFLOAD_VAE_CACHE=true
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
torchrun \
  --rdzv-backend=c10d \
  --rdzv-endpoint=localhost:6009 \
  --nnodes=1 \
  --nproc_per_node=8 \
  inference/pipeline/entry.py \
  --config_file example/24B/24B_base_config.json \
  --mode i2v \
  --prompt "Good Boy" \
  --image_path example/assets/image.jpeg \
  --output_path outputs/output_i2v.mp4
```

README guidance recommends H100/H800 x8 for 24B base/distill. For RTX 4090 x8, it notes setting `pp_size: 2` and `cp_size: 4`; keep `--nproc_per_node` at the product.

## Public Python API

Use the API when embedding MAGI inference into a Python orchestration script while still honoring the same config and distributed constraints:

```python
from inference.pipeline import MagiPipeline

pipe = MagiPipeline("example/4.5B/4.5B_base_config.json")
pipe.run_text_to_video(
    prompt="A quiet lake at sunrise, cinematic camera movement",
    output_path="outputs/lake.mp4",
)
```

Public routes:

```python
MagiPipeline(config_path)
run_text_to_video(prompt, output_path)
run_image_to_video(prompt, image_path, output_path)
run_video_to_video(prompt, prefix_video_path, output_path)
```

API caveats:

- Constructor side effects are substantial: it parses `MagiConfig`, seeds random generators, initializes `torch.distributed`, initializes MAGI model-parallel groups, and prints config state.
- Use a fresh Python process for each distributed run. Interactive notebooks and long-lived services can hang or report "distribution already initialized" if a previous run left process groups alive.
- For multi-GPU configs, instantiate the API under `torchrun`; each rank runs the same Python entry logic.
- The API still loads T5, VAE, and DiT checkpoints during execution. A config parse or helper validation is not a generation smoke test.

## Environment variables seen in source examples

| Variable | Use |
| --- | --- |
| `PYTHONPATH` | Include the MAGI source root so `inference.*` imports resolve. |
| `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, `RANK` | Needed for single-process source runs because MAGI still calls `torch.distributed.init_process_group`. `torchrun` usually supplies rank/world variables for multi-process runs. |
| `PAD_HQ`, `PAD_DURATION` | Enables prompt special-token padding paths used by the example scripts. |
| `PAD_STATIC`, `PAD_DYNAMIC`, `PAD_BORDERNESS`, `PAD_THREE_D_MODEL`, `PAD_TWO_D_ANIME`, `NEG_PROMPT` | Optional prompt special-token controls exposed by prompt processing. Use only when you understand the conditioning effect. |
| `SPECIAL_TOKEN_PATH` | Overrides the default path to `special_tokens.npz`; set it if assets are not under the default source tree location. |
| `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | Reduces CUDA allocator fragmentation in long video runs. |
| `OFFLOAD_T5_CACHE=true`, `OFFLOAD_VAE_CACHE=true` | Avoids retaining singleton T5/VAE caches after use; helpful under memory pressure. |
| `CUDA_DEVICE_MAX_CONNECTIONS=1`, `NCCL_ALGO=^NVLS` | Used by the 24B example script for multi-GPU/NCCL behavior. |
| `SKIP_LOAD_MODEL` | Debug-only source switch that skips DiT checkpoint loading; do not treat outputs from such a run as real generation. |

## Output and validation checklist

Before launching full generation:

1. Confirm the config parses and satisfies CFG/distributed rules with `scripts/magi_config_check.py`.
2. Confirm checkpoint paths exist and point to DiT, T5, VAE, and special-token assets.
3. Confirm `pp_size * cp_size` equals the intended process count.
4. Confirm CUDA, `flash-attn`, `flashinfer-python`, ffmpeg, and PyTorch/CUDA versions are compatible.
5. Confirm the input path required by the chosen mode exists.
6. Remember that successful helper output is not a smoke test; only a real run with downloaded checkpoints can validate generation.
