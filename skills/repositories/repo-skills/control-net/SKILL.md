---
name: control-net
description: "Route ControlNet 1.0 source-checkout tasks for annotators, Gradio
  inference apps, training datasets, and model/weight utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ControlNet Repo Skill

Use this skill for tasks involving the ControlNet 1.0 repository: preparing control maps, running or adapting Gradio demos, validating Fill50K-style training data, creating ControlNet initialization checkpoints, inspecting configs, or debugging source-checkout setup.

This repo is a source checkout, not an installable Python distribution. Do not assume `pip install control-net` exists. A working runtime usually needs the documented environment dependencies, external Stable Diffusion/ControlNet checkpoints, detector weights, and compatible GPU/Torch setup.

## Start Here

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a checkout or needs refresh.
- Read [references/evidence-map.md](references/evidence-map.md) for the source evidence and script-bundling decisions behind this skill.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, checkpoint, CUDA, model-download, and non-packaged-checkout failures.
- Run [scripts/check_controlnet_checkout.py](scripts/check_controlnet_checkout.py) for a safe checkout/config/import diagnostic; it does not launch Gradio, load checkpoints, download models, train, or generate images.

## Route By Task

| User task | Read |
| --- | --- |
| Prepare or debug Canny, HED, MLSD, MiDaS depth/normal, OpenPose, or Uniformer conditioning maps | [sub-skills/annotators-and-preprocessing/SKILL.md](sub-skills/annotators-and-preprocessing/SKILL.md) |
| Choose, inspect, run, or adapt a ControlNet Gradio image-generation app | [sub-skills/gradio-inference-apps/SKILL.md](sub-skills/gradio-inference-apps/SKILL.md) |
| Validate Fill50K-style data, write a custom dataset, or adapt tutorial training | [sub-skills/training-and-datasets/SKILL.md](sub-skills/training-and-datasets/SKILL.md) |
| Inspect configs/APIs, create init checkpoints, dry-run key mappings, or transfer ControlNet weights | [sub-skills/model-and-weight-utilities/SKILL.md](sub-skills/model-and-weight-utilities/SKILL.md) |

## Safe Setup Expectations

1. Create an environment compatible with the repository's `environment.yaml` family: Python 3.8-era ML stack, PyTorch/TorchVision, OpenCV, Gradio, PyTorch Lightning, OmegaConf, Transformers, OpenCLIP, and optional detector dependencies.
2. Treat model files as external assets. Stable Diffusion checkpoints belong with the model/config workflow, ControlNet demo checkpoints belong with Gradio app operation, and detector checkpoints belong with annotator preprocessing.
3. Use safe diagnostics first: parse configs and signatures, validate data layouts, and dry-run state-dict key mapping before launching servers, loading checkpoints, using CUDA, downloading weights, or training.
4. Prefer CPU/location-safe inspection for checkpoint metadata; only run CUDA, Gradio servers, or long training when the user explicitly wants execution and has provided assets/hardware.

## Minimal Safe Checks

```bash
python path/to/control-net/scripts/check_controlnet_checkout.py --repo-root path/to/ControlNet --json
```

Then route to the nearest sub-skill for workflow-specific checks:

- `annotators-and-preprocessing/scripts/inspect_annotator_inputs.py --self-check`
- `gradio-inference-apps/scripts/extract_gradio_signatures.py --repo-root path/to/ControlNet --json`
- `training-and-datasets/scripts/validate_fill50k_dataset.py --write-example-fixture path/to/tmp-fill50k --validate-written-fixture`
- `model-and-weight-utilities/scripts/inspect_weight_mapping.py --self-test`

## Common Boundaries

- Do not import `gradio_*2image.py` merely to inspect it; the source scripts build models, load checkpoints, move models to CUDA, and launch Gradio at top level.
- Do not instantiate learned annotators unless detector checkpoints, optional dependencies, CUDA/Torch compatibility, and network policy are clear.
- Do not run tutorial training as a smoke test; it requires Fill50K data, initialized checkpoints, GPU memory, and may trigger model/tokenizer downloads.
- Do not run checkpoint conversion scripts without explicit input/output paths and overwrite safeguards; use the bundled dry-run inspector first.

## Refresh Signals

Run `refresh-repo-skill` if the current checkout changes public Gradio scripts, `cldm/`, `ldm/`, `annotator/`, `models/*.yaml`, tutorial scripts, docs, environment dependencies, or source script behavior relative to [references/repo-provenance.md](references/repo-provenance.md).
