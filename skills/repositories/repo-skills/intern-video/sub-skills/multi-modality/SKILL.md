---
name: multi-modality
description: "Guides InternVideo2 multi-modality Stage2 and CLIP
  video-text/audio training, retrieval evaluation, demo setup, Python configs,
  launchers, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# InternVideo2 Multi-Modality

Use this sub-skill for `InternVideo2/multi_modality`: Stage2 video-language alignment, CLIP post-pretraining, zero-shot/fine-tuned retrieval, audio-text/audio-visual tasks, demo retrieval, config files, and distributed launch adaptation.

## Read first

- [Workflows](references/workflows.md) explains Stage2, CLIP, evaluation, demo, preprocessing, and launcher layers.
- [Configuration and data](references/configuration-and-data.md) records config system, path variables, model families, annotation/preprocess expectations, and checkpoint naming.
- [Troubleshooting](references/troubleshooting.md) covers PYTHONPATH, FlashAttention/Apex/DeepSpeed, checkpoint, tokenizer, and dataset failures.

## Safe helper

Use the bundled launch builder to print command skeletons without submitting jobs:

```bash
python scripts/build_multimodal_launch.py --task pretrain --branch stage2 --config scripts/pretraining/stage2/1B/config.py --nodes 8 --gpus-per-node 8
python scripts/build_multimodal_launch.py --task evaluate --branch stage2 --config scripts/evaluation/stage2/zero_shot/1B/config_msrvtt.py --pretrained ${INTERNVIDEO2_MODEL_PATH}/1B_stage2_pt.pth
python scripts/build_multimodal_launch.py --task retrieval --branch clip --config scripts/evaluation/clip/zero_shot/1B/config_msrvtt.py --pretrained ${INTERNVIDEO2_MODEL_PATH}/InternVideo2_CLIP_1B.pth --no-slurm
```

The helper prints a `tools/run.py` dry-run concept for Stage2 plus a direct `srun` or `torchrun` skeleton. It never calls the source launcher.

## Route by task

| Task | Route |
|---|---|
| Stage2 pretraining or finetuning | `tasks/pretrain.py` plus a Python config under `scripts/pretraining` or `scripts/finetuning`; config owns text encoder, dataset roots, DeepSpeed, and evaluation flags. |
| CLIP post-pretraining | `tasks_clip/pretrain.py`; use matching vision/text checkpoint paths and remember CLIP variants may be InternVL/LLM-backed or MobileCLIP-backed. |
| Zero-shot retrieval/action evaluation | Stage2 uses `tasks/pretrain.py` with `evaluate True`; CLIP retrieval uses `tasks_clip/retrieval.py`; both rely on dataset-specific config files. |
| Demo video-text retrieval | Use the demo config and `demo/utils.py` with the multi-modality folder on `PYTHONPATH`; Stage2 demo needs tokenizer and checkpoint paths before inference. |
| Preprocess/annotation conversion | Use `preprocess/create_sqlite_db.py` as schema evidence for JSON-to-SQLite shape, but keep destructive conversions out of the helper script. |
| Job submission abstraction | Treat `tools/run.py` as a launcher template that copies code to `VL_EXP_DIR`, resolves SLURM/local mode, and forwards tasks through `torchrun`; use the bundled helper for dry runs. |
| Audio-video workflows | Stage2 configs can switch to BEATs audio encoders and audio-visual losses; verify audio packages, media roots, and checkpoint paths first. |

## Required decisions before execution

1. Branch: Stage2 or CLIP.
2. Mode: pretrain, evaluate/retrieval, demo, or preprocess.
3. Config file and overrides: dataset paths, output dir, `pretrained_path`, checkpoint paths, DeepSpeed setting, and optional extra config args.
4. Text/vision/audio checkpoint family: BERT tokenizer folder, InternVL/LLM text encoder path, MobileCLIP/LoRA path, vision backbone checkpoint, BEATs audio weights, or distilled extra checkpoint.
5. Runtime: SLURM or local torchrun, GPU count, FlashAttention/Apex/DeepSpeed readiness, and whether `PYTHONPATH` must be rooted at the multi-modality folder.

## Boundaries

- Route video-only action recognition finetuning to `../single-modality/SKILL.md`.
- Route MLLM long-video chat to `../video-mllm/SKILL.md`.
- Route annotation validation and InternVid dataset questions to `../datasets/SKILL.md`.
