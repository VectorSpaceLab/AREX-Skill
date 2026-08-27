---
name: pretraining
description: "Guides OFA multimodal pretraining and continuous-pretraining
  workflows, including mixed TSV layouts and negative-sample preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# pretraining

Use this sub-skill when a user wants to pretrain OFA, resume pretraining from a checkpoint, or validate the pretraining workspace before launch.

## Trigger phrases

- "Pretrain OFA"
- "Continuous pretraining"
- "Why does `pretrain_ofa_large.sh` fail?"
- "What files go in the pretraining folder?"
- "How do I validate the negative-sample directory?"

## What this sub-skill owns

- the mixed pretraining TSV bundle,
- continuous-pretraining vs scratch decisions,
- negative-sample folder requirements,
- the pretraining task and dataset composition,
- prelaunch validation of the pretraining workspace.

## What it excludes

- downstream caption/VQA/RefCOCO/OCR/ImageNet finetuning -> `vision-language-tasks`,
- image generation -> `image-generation`,
- speech pretraining -> `mmspeech`,
- generic setup and launch mechanics -> `setup-and-command-building`.

## Read these files

- [references/workflows.md](references/workflows.md) for the pretraining flow and command shape.
- [references/data-layout.md](references/data-layout.md) for the four TSV families and the negative-sample directory.
- [references/troubleshooting.md](references/troubleshooting.md) for missing-file and wrong-column failures.
- [scripts/validate_pretraining_inputs.py](scripts/validate_pretraining_inputs.py) to verify the workspace before launch.

## Typical workflow

1. Decide whether to restore a checkpoint or start from scratch.
2. Confirm the mixed TSV bundle is complete.
3. Check that the negative-sample files exist and are readable.
4. Render the launch command only after the layout validator passes.

## Notes

- Pretraining uses multiple TSVs, not a single generic dataset file.
- The same workspace may hold text-only, image-only, vision-language, and detection rows.
- A missing negative-sample file is often easier to fix than a long failed GPU run.
