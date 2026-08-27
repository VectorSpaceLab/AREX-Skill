---
name: viewers
description: "Guides gaussian-splatting SIBR remote and real-time viewer build,
  run, connection, and troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Viewers

Use this sub-skill when the task is about the SIBR network viewer, the real-time Gaussian viewer, viewer build commands, optimizer connection settings, navigation, top view, or CUDA/OpenGL interop issues.

## Read First

- Read [references/viewer-workflows.md](references/viewer-workflows.md) for build/run commands, remote viewer flow, real-time viewer flow, top-view behavior, and OpenXR notes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for connection, path override, build dependency, OpenGL/CUDA interop, and performance problems.
- Use [scripts/build_viewer_command.py](scripts/build_viewer_command.py) to print a viewer command without running a binary.

## Viewer Types

- **Network/remote viewer** connects to a running `train.py` optimizer over a socket. The optimizer defaults to `127.0.0.1:6009` unless `--ip` and `--port` are changed.
- **Real-time viewer** loads a trained model directory and renders it interactively using SIBR/OpenGL/CUDA.

## Preconditions

- Python training/rendering setup is handled by [../setup-and-backends/SKILL.md](../setup-and-backends/SKILL.md).
- A trained model for the real-time viewer is produced through [../training/SKILL.md](../training/SKILL.md).
- SIBR viewer binaries must already be downloaded or built; this sub-skill does not assume they exist.

## Command Shapes

Remote viewer:

```bash
SIBR_remoteGaussian_app --ip 127.0.0.1 --port 6009
```

Optimizer side:

```bash
python train.py -s <scene> --ip 127.0.0.1 --port 6009
```

Real-time viewer:

```bash
SIBR_gaussianViewer_app -m <trained-model>
```

Use `-s <source-scene>` if the viewer cannot resolve the model's saved source path.

## Boundaries

- Do not diagnose SIBR internals beyond documented build/run and runtime failure modes unless the user is explicitly editing the SIBR source.
- Do not treat SIBR viewer success as proof that Python training/rendering metrics work, or vice versa.
