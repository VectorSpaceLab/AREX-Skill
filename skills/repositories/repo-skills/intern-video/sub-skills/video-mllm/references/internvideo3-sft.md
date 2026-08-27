# InternVideo3 SFT and CPT workflow reference

This reference distills the InternVideo3 SFT README, configs, pyproject, and shell launchers into portable command and configuration guidance.

## What the SFT code covers

The inspected training subtree is an XTuner-based package for InternVideo3 supervised fine-tuning and continued pretraining. It exposes three current config families:

| Config family | Main use | Important defaults |
|---|---|---|
| `internvideo3_cpt.py` | Continued pretraining (CPT) after attention/model conversion | `sample_max_length=65536`, `pack_max_length=65536`, global batch size 128, LR `2e-5`, warmup ratio `0.03`, `fps=2`, video max frames 768, `rand_video_max_frames=24`. |
| `internvideo3_sft_short.py` | Regular/short SFT | `sample_max_length=65536`, global batch size 128, LR `3e-5`, warmup ratio `0.1`, `fps=2`, video max frames 768, `rand_video_max_frames=24`. |
| `internvideo3_sft_long.py` | Long-video SFT/debug-style long context | `sample_max_length=262144`, global batch size 8, LR `1e-5`, `fps=4`, video max frames 2048, larger video total pixel budget, `sp_size=4`, fewer workers. |

The configs build `InternVideo3Dense8BConfig` with vision encoder, MLA projector, and Qwen3-8B language model components. They use `VLMJsonlDataset`, `InternVideoTokenizeFnConfig`, `qwen3_vl_sft_collator`, soft packing, FSDP with CPU offload, recompute ratio 1.0, and CE loss in chunk mode with square reduction.

## Dependency envelope

The package metadata and installer indicate:

- Python `>=3.10`.
- PyTorch `>=2.6.0`.
- `transformers` 4.57.x generation; the installer pins 4.57.3 while package metadata pins 4.57.0.
- `datasets<4.0.0`, `mmengine`, `bitsandbytes`, `peft`, `einops`, `timm`, `opencv-python-headless`, `imageio`, `tensorboard`, and other XTuner utilities.
- Optional video extras include `decord` and `av`.
- FlashAttention 3 is expected when `XTUNER_USE_FA3=1`; verify the CUDA/PyTorch/FlashAttention trio before starting real runs.

Do not install or upgrade these packages in a user environment without approval. SFT dependencies are large and can conflict with other InternVideo generations.

## Portable launch shape

The source launch script can be distilled to the following shape. Use explicit config names from the current snapshot rather than relying on launcher defaults.

```bash
export META_DATA_PATH=<annotation-meta.json>
export WORK_DIR=<checkpoint-output-dir>
export LOAD_FROM=<pretrained-model-dir>
export PROCESSOR_PATH=<processor-or-tokenizer-dir>
export TOKENIZER_CACHE_DIR=<token-cache-dir>
export CEPH_CONFIG=<oss-config-if-needed>

export XTUNER_PACK_WORKERS=${XTUNER_PACK_WORKERS:-8}
export XTUNER_TOKENIZE_WORKERS=${XTUNER_TOKENIZE_WORKERS:-16}
export XTUNER_USE_FA3=${XTUNER_USE_FA3:-1}
export XTUNER_GC_ENABLE=${XTUNER_GC_ENABLE:-1}
export XTUNER_SKIP_EMPTY_THINK=${XTUNER_SKIP_EMPTY_THINK:-1}
export AV_LOG_FORCE_NOCOLOR=1
export AV_LOG_LEVEL=16

# Run from an environment where the InternVideo3 SFT package is importable.
torchrun \
  --nnodes=<node-count> \
  --node_rank=<node-rank> \
  --master_addr=<master-addr> \
  --master_port=<master-port> \
  --nproc_per_node=<gpus-per-node> \
  xtuner/v1/train/cli/sft.py --config <config.py>
```

For a single-node debug run, use `<node-count>=1`, `<node-rank>=0`, `<master-addr>=127.0.0.1`, `<gpus-per-node>=1`, and a tiny JSONL fixture validated with the sibling `datasets` sub-skill. Do not treat that as proof of full long-video training readiness.

## Meta JSON schema

The configs read `META_DATA_PATH` as a JSON object mapping dataset names to dataset specifications:

```json
{
  "my_sft_split": {
    "annotation": "<annotations.jsonl-or-directory>",
    "media_root": "<media-root>",
    "sample_ratio": 1.0,
    "fps": 2,
    "video_min_frames": 4,
    "video_max_frames": 768,
    "rand_video_max_frames": 24,
    "min_pixels": 4096,
    "max_pixels": 16777216,
    "video_min_total_pixels": 16384,
    "video_max_total_pixels": 25165824,
    "enable_3d_rope": true,
    "add_vision_id": true
  }
}
```

Only `annotation` is strictly required by the config loop; `media_root` defaults to empty and `sample_ratio` defaults to 1.0. Pixel and frame fields override tokenizer defaults per dataset. If `META_DATA_PATH` is not set, the configs look for exactly one `.json` file next to the config file, which is fragile for production; set `META_DATA_PATH` explicitly.

## Annotation JSONL schema reminders

Each annotation line is a JSON object with `messages`. Roles include `system`, `developer`, `user`, `assistant`, and `pretrain`; loss defaults to assistant/pretrain only. User/pretrain content may contain:

- `{"type": "text", "text": "...<VIDEO_CONTEXT>..."}` with optional `conversation_timestamps`.
- `{"type": "image_url", "image_url": {"url": "relative/image.jpg", "image_wh": [width, height]}}`.
- `{"type": "video_url", "video_url": {"url": "relative/video.mp4", "image_wh": [width, height], "origin_video_length": frames_or_duration, "origin_fps": fps}}`.

For video records, `image_wh` is needed for token counting/packing. Providing `origin_video_length` and `origin_fps` enables timestamp-aware frame sampling. If `processed_video_length` is provided, `processed_fps` must also be provided; `frames_timestamp` must match the processed frame count. Text placeholder counts must match the number of image/video content items.

## Current snapshot caveats

- Some launch comments/defaults refer to `internvideo3_sft.py` and `internvideo3_sft_debug.py`, but the inspected config files are `internvideo3_cpt.py`, `internvideo3_sft_short.py`, and `internvideo3_sft_long.py`. Pass an explicit existing config.
- The README lists `GLOBAL_BATCH_SIZE` as an environment override, but the current configs hard-code `global_batch_size`. To change it, create a derived config or edit the config in the working copy; do not assume the env var will be read.
- The rjob launcher encodes a specific cluster image, mounts, charged group, RDMA resources, and storage. Treat it as a cluster-specific example, not a portable recipe.
- The source install script performs package installation. For reproducibility, pre-build the environment intentionally instead of letting evaluation/training scripts install packages during a run.

## Preflight sequence

1. Validate meta JSON and JSONL annotations with the `datasets` sub-skill script.
2. Confirm model/processor paths match the checkpoint and tokenizer family.
3. Verify `transformers`, PyTorch, FlashAttention/FA3, and CUDA imports in the intended environment.
4. Run a tiny single-GPU debug with one or two short JSONL records only after the user approves GPU use.
5. Scale to multi-GPU/multi-node only after cache, packing, FSDP, and data loader behavior are understood.
