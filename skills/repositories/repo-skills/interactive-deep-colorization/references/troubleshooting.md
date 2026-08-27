# Cross-Cutting Troubleshooting

## Purpose

Read this when a task spans setup, local-hints colorization, and global histogram transfer, or when the first failure signal does not clearly belong to one sub-skill.

## Route by symptom

| Symptom or request | Likely owner | Next step |
| --- | --- | --- |
| Missing `model.caffemodel`, `caffemodel.pth`, `global_model.caffemodel`, or `dummy.caffemodel` | Setup/model artifacts | Read [../sub-skills/setup-and-models/references/model-artifacts.md](../sub-skills/setup-and-models/references/model-artifacts.md) and run the model checker. |
| `No module named caffe`, Caffe Python layer errors, or global histogram cannot run | Setup plus global histogram | Read setup troubleshooting, then [../sub-skills/global-histogram-transfer/SKILL.md](../sub-skills/global-histogram-transfer/SKILL.md) if the task needs reference-image histogram transfer. |
| `No module named PyQt4` or GUI `--help` fails before parsing | Local-hints GUI setup | Use [../sub-skills/interactive-colorization/scripts/inspect_cli_defaults.py](../sub-skills/interactive-colorization/scripts/inspect_cli_defaults.py) for parser facts; install Qt only for real GUI launch. |
| User asks how to add color points, move points, select suggested colors, or save results | Local-hints workflow | Read [../sub-skills/interactive-colorization/references/workflows.md](../sub-skills/interactive-colorization/references/workflows.md). |
| User asks for a PyTorch global histogram transfer path | Capability mismatch | Explain that this checkout's global histogram workflow is Caffe-only and route to [../sub-skills/global-histogram-transfer/SKILL.md](../sub-skills/global-histogram-transfer/SKILL.md). |
| User asks for training or fine-tuning code in this repo | Out of scope for this checkout | State that training is delegated by the README to a separate repository and do not invent local training commands. |
| Docker GUI runs but no window appears | Display forwarding | Read [../sub-skills/setup-and-models/references/docker-reference.md](../sub-skills/setup-and-models/references/docker-reference.md). |
| Tensor shape or Lab/ab values are confusing | Local-hints data formats | Read [../sub-skills/interactive-colorization/references/data-formats.md](../sub-skills/interactive-colorization/references/data-formats.md). |

## Verification boundary

This generated skill's construction verified:

- source imports and signatures for `data.colorize_image`, `data.lab_gamut`, and `models.pytorch.model`;
- local-hints Lab/gamut helper behavior;
- PyTorch `SIGGRAPHGenerator` tiny CPU forward behavior and optional CUDA visibility;
- safe bundled scripts with help/parser checks.

It did not verify:

- PyCaffe runtime execution;
- Qt GUI launch on a display server;
- Docker build/run;
- network model downloads;
- trained model inference with real downloaded weights;
- global histogram native execution.

When a user needs one of the unverified runtime surfaces, treat it as a setup or environment gate, not as a reason to ignore the documented workflow.

## Staleness and refresh

Read [repo-provenance.md](repo-provenance.md) when working with another checkout. If the commit, changed source files, model layout, GUI scripts, or notebook workflows differ materially from the provenance snapshot, run the repo-skill refresh workflow before relying on exact API/CLI details.
