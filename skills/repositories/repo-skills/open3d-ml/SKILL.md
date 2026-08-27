---
name: open3d-ml
description: "Guides Open3D-ML installation, dataset workflows, config-driven
  training, visualization, and backend-specific troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Open3D-ML

Use this skill for Open3D-ML point-cloud workflows: installing the package,
loading datasets, building config-driven pipelines, inspecting predictions, and
handling the optional TensorFlow, CUDA, GUI, or OpenVINO paths.

## Start here

1. If the package does not import yet, read `references/troubleshooting.md`
   and route to `sub-skills/install-and-inspect/`.
2. If you need dataset folders, split handling, or custom data layouts, route
   to `sub-skills/datasets-and-preprocessing/`.
3. If you need model selection, config-driven training, or inference, route to
   `sub-skills/training-and-pipelines/`.
4. If you need point-cloud inspection, bounding boxes, TensorBoard summaries,
   or OpenVINO wrapping, route to `sub-skills/visualization-and-extensions/`.

## Quick install guidance

A conservative CPU inspection path is enough for many checks:

```bash
python -m pip install open3d 'torch==2.2.*+cpu' 'torchvision==0.17.*+cpu' \
  addict numpy<2 pyyaml tensorboard
```

If you are using a local Open3D-ML checkout with an external Open3D wheel,
set `OPEN3D_ML_ROOT` to the checkout root before importing `open3d.ml.*`.

## Minimal smoke checks

Use the bundled helper when you want a safe status report:

```bash
python scripts/check_install.py --framework torch
python scripts/check_install.py --framework torch --config path/to/config.yml
```

If you only need to inspect config files without launching a workflow, use:

```bash
python scripts/inspect_configs.py path/to/config-or-directory
```

## Route map

- `install-and-inspect`: importability, backend compatibility, and startup
  failure recovery.
- `datasets-and-preprocessing`: dataset constructors, split names, custom
  point-cloud layouts, and layout validation.
- `training-and-pipelines`: config loading, registry lookup, model selection,
  and semantic-segmentation/object-detection workflows.
- `visualization-and-extensions`: Visualizer, label LUTs, bounding boxes,
  TensorBoard summaries, and OpenVINO guidance.

## What this skill is good at

- Finding the right Open3D-ML class or config shape for a 3D workflow.
- Explaining the difference between dataset layout, pipeline configuration,
  and visualization output.
- Helping you choose a CPU smoke path versus an optional backend-specific path.

## What to read when you need more detail

- `references/model-overview.md` for the top-level task and model map.
- `references/troubleshooting.md` for cross-cutting failure families.
- The nearest sub-skill references for workflow-specific details.

## Provenance

Read `references/repo-provenance.md` before deciding whether this skill still
matches the current checkout, and refresh the skill if the repo state has
moved.
