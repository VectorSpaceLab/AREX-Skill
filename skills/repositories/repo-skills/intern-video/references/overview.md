# InternVideo Operating Overview

## Generation map

| Area | Best fit | Main workflows | Deep route |
|---|---|---|---|
| InternVideo1 | Legacy 2022 foundation models and downstream tasks | VideoMAE, ViCLIP, Multi-Modalities pretraining, retrieval, localization, VQA, open-set action recognition, VLN | `sub-skills/legacy-workflows/` |
| InternVideo2 single-modality | Video-only masked/discriminative foundation models | Stage1 pretraining, Kinetics/SSv/HMDB/UCF finetuning/linear probing, distillation from Stage2 teacher | `sub-skills/single-modality/` |
| InternVideo2 multi-modality | Video-text/audio alignment and retrieval | Stage2, CLIP post-pretraining, zero-shot retrieval/action evaluation, demo retrieval | `sub-skills/multi-modality/` |
| InternVideo2.5 | Released video MLLM with long and rich context modeling | Model selection, benchmark context, HiCo/LRC concepts, external training pointers | `sub-skills/video-mllm/` |
| InternVideo3 | Long-horizon video MLLM and agentic reasoning | Transformers quickstart, video/image/text messages, SFT config, evaluation scripts, MCR/M2LA concepts | `sub-skills/video-mllm/` |
| InternVideo-Next | Latest visual foundation model without video-text supervision | Stage1/stage2 pretraining, InternVideo_next architectures, diffusion/JEPA pieces | `sub-skills/next-pretraining/` |
| Data/InternVid and instruction data | Dataset releases and annotation guidance | InternVid video-text pairs, query seed list, VideoChat instruction data, annotation validation | `sub-skills/datasets/` |

## Operating principles

1. Pick the generation before picking a script. Many names overlap, but Stage1 visual checkpoints, Stage2 retrieval checkpoints, CLIP checkpoints, and MLLM checkpoints are not interchangeable.
2. Treat most repository launchers as templates. They encode correct flags, but cluster resources, paths, datasets, and checkpoints must be supplied by the user.
3. Validate placeholders and backend dependencies before running. Large jobs fail late and expensively when `your_data_path`, `your_model_path`, FlashAttention, or dataset JSON files are wrong.
4. Keep evidence local to this skill. Use bundled references and scripts for guidance; only use a user's checkout to run/edit actual code requested by the user.
