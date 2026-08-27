---
name: legacy-workflows
description: "Guides InternVideo1 legacy pretraining and downstream task routes,
  including VideoMAE, ViCLIP, retrieval, localization, VQA, open-set
  recognition, and submodule cautions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Legacy Workflows

Use this sub-skill when the user works with `InternVideo1` or legacy InternVideo checkpoints/tasks from the 2022/2023 code areas.

## Read first

- [Workflows](references/workflows.md) maps legacy pretraining and downstream subprojects.
- [Troubleshooting](references/troubleshooting.md) covers submodules, dependency fragmentation, and old-script pitfalls.

## Route by legacy component

| User signal | Area |
|---|---|
| Video masked autoencoder, `run_mae_pretraining.py`, `run_class_finetuning.py` | VideoMAE pretraining/finetuning |
| ViCLIP, video CLIP, InternVid-10M/200M transfer | ViCLIP / Multi-Modalities pretraining |
| MSR-VTT, DiDeMo, LSMDC, MSVD, VATEX, ActivityNet retrieval | Downstream video-text retrieval |
| AVA, THUMOS14, ActivityNet localization | Spatial/temporal action localization |
| VQA, zero-shot action recognition, zero-shot multiple choice | Multi-modalities downstream |
| UCF/HMDB open-set | Open-set action recognition |
| VLN-CE | Visual-language navigation |

## Operating workflow

1. Confirm the user really needs InternVideo1. If they mention InternVideo2/3/Next, route away.
2. Identify the legacy subproject and treat it as self-contained: dependencies and scripts differ across subdirectories.
3. Check for submodule or external repo requirements before running anything.
4. Prefer adapting documented command patterns in a fresh environment instead of mixing dependencies from multiple legacy subprojects.
5. For new research, consider whether a later generation fits better; legacy scripts are useful for reproducing old baselines and downstream tasks.

## Boundaries

- Do not import UniFormerV2/Ego-Tasks assumptions unless the submodule/external checkout is present.
- Do not reuse InternVideo2 environment requirements for InternVideo1 without checking the subproject README.
- Do not run legacy downstream scripts until data and checkpoint paths are explicit.
