---
name: training
description: "Routes VITS LJ Speech and VCTK training, checkpoint resume, and
  launch planning tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training

Use this route when you need to plan, launch, or troubleshoot VITS training runs for the LJ Speech or VCTK configs.

## Use this route when

- You need the single-speaker LJ Speech training path.
- You need the multi-speaker VCTK training path.
- You need to choose between `ljs_base.json`, `ljs_nosdp.json`, and `vctk_base.json`.
- You need checkpoint resume, logging, or DDP launch guidance.
- You need to diagnose CUDA, NCCL, port, or config-mismatch failures during training.

## Do not use this route when

- You are cleaning filelists or building the monotonic-alignment extension; use `data-preparation`.
- You are generating audio from a checkpoint; use `inference`.
- You only need a quick sanity check; use `../../scripts/check_install.py` or `../../scripts/model_smoke.py`.

## Read first

- `../../references/workflows.md` for the training flow and helper scripts.
- `../../references/configuration.md` for the config-file differences.
- `../../references/api-reference.md` for the training-related class and function signatures.
- `../../references/troubleshooting.md` for cross-cutting failures.
- `references/troubleshooting.md` in this sub-skill for launcher- and checkpoint-specific failures.

## Bundled helpers

- `../../scripts/launch_training.py` — prints or launches the correct training module with a safe `MASTER_PORT`.
- `../../scripts/model_smoke.py` — checks that the model can run a tiny synthetic forward/infer pass.
- `../../scripts/check_install.py` — confirms the repo and dependencies before launching.

## Common workflow

1. Confirm the config family and whether the dataset is single-speaker or multi-speaker.
2. Make sure the monotonic-alignment extension and CUDA backend are ready.
3. Use `launch_training.py --run` only after a dry run looks correct.
4. Use `model_smoke.py` if you need to separate environment problems from long-running training problems.

## Ownership boundaries

- Include config selection, DDP launch, checkpoint resume, and training diagnostics here.
- Exclude preprocessing and inference outputs; route those to sibling sub-skills.
