---
name: series-map
description: "Selects the right InternVideo generation, branch, and downstream
  route before using generation-specific training, evaluation, dataset, or MLLM
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Series Map

Use this sub-skill when the user names InternVideo vaguely, asks which version to use, mixes generation terms, or needs a high-level repo map before command construction.

## Read first

- [Generation map](references/generation-map.md) gives the detailed generation/task matrix.
- [Troubleshooting](references/troubleshooting.md) covers common selection mistakes and checkpoint-family mismatches.

## Route by intent

| Intent | Best route |
|---|---|
| Legacy 2022 InternVideo, VideoMAE, ViCLIP, old downstream tasks | `../legacy-workflows/SKILL.md` |
| Video-only action recognition, masked video pretraining, Kinetics/SSv finetuning, distillation | `../single-modality/SKILL.md` |
| Video-text retrieval, Stage2, CLIP post-pretraining, audio/text retrieval, demo retrieval | `../multi-modality/SKILL.md` |
| Long-video MLLM, InternVideo2.5, InternVideo3, SFT/eval of video LLMs | `../video-mllm/SKILL.md` |
| InternVideo-Next latest visual foundation model without video-text supervision | `../next-pretraining/SKILL.md` |
| InternVid, WebVid/InternVid annotations, VideoChat instruction data, benchmark data | `../datasets/SKILL.md` |

## Decision workflow

1. Identify the user-facing output: trained visual backbone, retrieval model, video-text scores, MLLM answer, benchmark metrics, dataset validation, or code maintenance.
2. Identify the checkpoint family named by the user. If absent, ask for the model generation only when route choice would change the answer.
3. Identify execution scale. Most generation-specific launchers are large SLURM jobs; for local inspection, use command builders and validators rather than native training scripts.
4. Confirm external assets: dataset root, checkpoint root, processor/tokenizer path, and download/storage approval.
5. Route to the narrowest sub-skill, then return to root troubleshooting only for cross-cutting backend/path problems.

## Non-goals

- Do not run training or evaluation from this route.
- Do not assume InternVideo2.5 and InternVideo3 share the same processor/config conventions just because both are video MLLMs.
- Do not use legacy InternVideo1 scripts when the user is asking about InternVideo2 or later checkpoints.
