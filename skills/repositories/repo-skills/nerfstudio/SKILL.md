---
name: nerfstudio
description: "Routes Nerfstudio NeRF, Gaussian Splatting, camera-pose, dataset
  conversion, training, viewer, evaluation, rendering, export, and
  plugin-extension tasks using its typed CLI and Python APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Nerfstudio

Use this skill when a task involves the `nerfstudio` package, `ns-*` commands,
NeRF or Gaussian Splatting training, camera-pose conversion, `transforms.json`,
viewer/render/export workflows, or custom Nerfstudio methods and dataparsers.
This is a router: read only the focused route and references needed for the task.

## First checks

- Prefer Python 3.8-3.10 for this 1.1.x-era package and install the public package with `python -m pip install nerfstudio` or an editable install when developing a package.
- Production training/rendering expects a compatible NVIDIA CUDA/PyTorch environment. A CPU path is useful for parser/config/plugin checks and reduced tests, not for claiming GPU throughput.
- Run the bundled read-only diagnostic when the environment is unclear: [`scripts/check_environment.py`](scripts/check_environment.py). Use `--require-cuda` only when the requested workflow truly needs CUDA and `--check-cli` to validate installed entry points.
- Read [`references/architecture-overview.md`](references/architecture-overview.md) when a task crosses data, training, and output stages; read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting failures.

## Route by task

- **Install, entry points, help ordering, shell completion, or safe dataset download planning:** read [`cli-workflows/SKILL.md`](sub-skills/cli-workflows/SKILL.md).
- **Convert images/video/device exports, validate `transforms.json`, or choose a dataparser:** read [`data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md).
- **Choose a method, build `ns-train` commands, override configs, resume, or use multi-GPU/logging:** read [`training-and-configs/SKILL.md`](sub-skills/training-and-configs/SKILL.md).
- **Launch the viewer, render camera paths, evaluate metrics, or export point clouds/meshes/Gaussian Splats:** read [`visualization-and-export/SKILL.md`](sub-skills/visualization-and-export/SKILL.md).
- **Add a custom method/dataparser or debug plugin registration:** read [`api-extension/SKILL.md`](sub-skills/api-extension/SKILL.md).

## Standard handoff

1. Establish a valid dataset directory and validate its paths/schema.
2. Build a typed `ns-train` command with method arguments before dataparser arguments.
3. Save and preserve the generated `config.yml`; it is the downstream handoff for viewer, evaluation, rendering, and export.
4. For CUDA workflows, check device availability and memory before starting long jobs; prefer explicit ray/batch limits and an output directory.
5. Do not run original repository tests, examples, downloaders, or infinite viewer services as part of ordinary use. The routes contain safe preflights and distilled recipes.

## Currentness

Read [`references/repo-provenance.md`](references/repo-provenance.md) before using this skill against a checkout whose package version, commit, entry points, or method/dataparser catalog may differ. Refresh the skill when those facts change.
