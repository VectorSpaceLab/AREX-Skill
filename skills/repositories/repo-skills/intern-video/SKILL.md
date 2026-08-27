---
name: intern-video
description: "Routes InternVideo repository workflows for video foundation
  models, multimodal retrieval, video MLLMs, datasets, distributed training
  scripts, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# InternVideo Repo Skill

Use this skill when the user asks about the OpenGVLab InternVideo repository, including InternVideo1, InternVideo2, InternVideo2.5, InternVideo3, InternVideo-Next, InternVid data, video-text retrieval, action recognition, long-video MLLMs, or adapting the repo's distributed training/evaluation scripts.

This skill is a self-contained operating guide. It teaches the repo's structure, command conventions, dataset/model prerequisites, and failure modes; it does not require reopening the original repository documentation just to decide a route.

## First steps

1. Read [repo provenance](references/repo-provenance.md) when checking staleness against a checkout.
2. Read [overview](references/overview.md) when the user has not named a generation or branch.
3. Read [installation and backend readiness](references/installation-and-backends.md) before running any model, evaluation, or training command.
4. Use [cross-cutting troubleshooting](references/troubleshooting.md) for path, CUDA, FlashAttention, SLURM, download, and checkpoint issues.
5. Use [script inventory](references/script-inventory.md) when deciding whether to adapt a repo launcher, use a bundled helper, or only document a heavyweight script.

## Route by task

| User task | Read |
|---|---|
| "Which InternVideo generation should I use?" | [series-map](sub-skills/series-map/SKILL.md) |
| Legacy InternVideo1, VideoMAE, ViCLIP, retrieval/localization/VQA/open-set/VLN | [legacy-workflows](sub-skills/legacy-workflows/SKILL.md) |
| InternVideo2 single-modality pretraining, finetuning, linear probing, distillation, Kinetics/SSv/HMDB/UCF action recognition | [single-modality](sub-skills/single-modality/SKILL.md) |
| InternVideo2 multi-modality Stage2/CLIP, video-text/audio retrieval, demo retrieval, zero-shot evaluation, Python config system | [multi-modality](sub-skills/multi-modality/SKILL.md) |
| InternVideo2.5 or InternVideo3 video MLLM inference, SFT, evaluation, long-video reasoning | [video-mllm](sub-skills/video-mllm/SKILL.md) |
| InternVideo-Next stage1/stage2 visual pretraining and architecture | [next-pretraining](sub-skills/next-pretraining/SKILL.md) |
| InternVid, instruction data, video-text annotations, dataset path/schema validation | [datasets](sub-skills/datasets/SKILL.md) |

## Safe bundled helpers

- Run `python scripts/check_internvideo_environment.py --json` to report Python, torch/CUDA, optional package, command, and path readiness without installing or submitting jobs.
- Run `python scripts/summarize_training_script.py --script <local-launcher.sh>` when a user provides a launcher and you need to extract placeholders, resource requests, and Python entry points without executing it.

## Hard boundaries

- Do not submit SLURM jobs, download large datasets/checkpoints, build CUDA extensions, or run long training/evaluation unless the user explicitly authorizes that downstream action.
- Do not treat a CPU import check as proof that CUDA/FlashAttention/Apex/DeepSpeed workflows are ready.
- Do not mix checkpoint families: InternVideo2 single-modality Stage1/distillation weights, InternVideo2 Stage2 retrieval weights, InternVideo2 CLIP weights, InternVideo2.5 MLLM weights, InternVideo3 MLLM weights, and InternVideo-Next weights have different config expectations.
- If a workflow needs private benchmark data, credentials, or external storage, stop and ask for those resources before execution.

## Typical minimal readiness flow

```bash
python scripts/check_internvideo_environment.py --json
python scripts/check_internvideo_environment.py --data-root /path/to/data --model-root /path/to/models
```

Then enter the appropriate sub-skill and use its command builder or checklist to adapt the requested generation.
