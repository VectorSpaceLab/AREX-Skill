# InternVideo Generation Map

## Quick comparison

| Generation | Repository area | Core idea | Use when | Route |
|---|---|---|---|---|
| InternVideo1 | `InternVideo1/` | General video foundation models via generative and discriminative learning | The user mentions VideoMAE, ViCLIP, old retrieval/localization/VQA/open-set tasks, or 2022/2023 checkpoints | `legacy-workflows` |
| InternVideo2 single-modality | `InternVideo2/single_modality/` | Scaled video-only backbone pretraining/finetuning/distillation | The task is action recognition, masked video modeling, linear probing, or distilling smaller visual models | `single-modality` |
| InternVideo2 multi-modality | `InternVideo2/multi_modality/` | Stage2 video-text/audio alignment and CLIP-style retrieval models | The task is video-text retrieval, zero-shot retrieval/action recognition, CLIP branch training, demo ranking, or audio-text retrieval | `multi-modality` |
| InternVideo2.5 | `InternVideo2.5/` | Video MLLM built on InternVL2.5 with long and rich context modeling | The task asks about InternVideo2.5 model choice, HiCo/LRC, or released MLLM benchmark context | `video-mllm` |
| InternVideo3 | `InternVideo3/` | Long-horizon video MLLM with MCR and M2LA | The task asks for `InternVideo3-8B-Instruct`, long-video inference, SFT, evaluation scripts, or agentic video reasoning | `video-mllm` |
| InternVideo-Next | `InternVideo-Next/` | Visual foundation model without video-text supervision | The task asks for stage1/stage2 pretraining, InternVideo_next model internals, diffusion loss, JEPA masks, or 2025/2026 visual checkpoints | `next-pretraining` |
| InternVid/Data | `Data/` plus dataset docs in each generation | Video-text and instruction datasets | The task asks about video-caption annotations, WebVid/InternVid, benchmark JSONs, or data path validation | `datasets` |

## Checkpoint-family guardrails

- InternVideo2 single-modality Stage1 checkpoints support visual action-recognition style workflows and are configured through command-line flags.
- InternVideo2 multi-modality Stage2 and CLIP checkpoints use Python config files, video/text encoders, and retrieval/evaluation tasks.
- InternVideo2.5 and InternVideo3 are MLLM model families; use Transformers/processor message formats rather than InternVideo2 retrieval scripts.
- InternVideo-Next has its own stage1/stage2 entry points and model classes; do not treat it as a drop-in replacement for InternVideo2 shell scripts.

## Asking only when necessary

If the user says only "InternVideo model" but also gives a task clue, route directly:

- "rank captions for a video" -> multi-modality retrieval.
- "fine-tune K400" -> single-modality.
- "describe a long video with 8B" -> video-mllm.
- "pretrain without video-text supervision" -> next-pretraining.
- "InternVid annotation schema" -> datasets.

Ask a clarifying question only when two routes would lead to incompatible commands or checkpoints.
