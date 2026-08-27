---
name: environment-and-model-setup
description: "Set up and verify Hunyuan3D-2 Python, CUDA, extension, and
  model-cache environments."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Hunyuan3D-2 Environment and Model Setup

Use this sub-skill when the task is about installing `hy3dgen`, choosing PyTorch/CUDA variants, building texture extensions, validating GPU/backend readiness, selecting model subfolders, or planning local/offline model caches.

## Route here for

- Installing package requirements and `hy3dgen` from a package source or a repository tree the user is intentionally working in.
- Building `custom_rasterizer` and `mesh_processor` for texture generation.
- Diagnosing CUDA toolkit/header, PyTorch CUDA, pymeshlab/OpenGL, and extension import failures.
- Understanding model zoo names, subfolders, VRAM needs, and `HY3DGEN_MODELS` cache behavior.
- Running non-downloading environment checks before shape/texture/service workflows.

## Do not route here for

- Shape generation code parameters after the environment is ready: use `../shape-generation/`.
- Texture/mesh workflow details after extensions are ready: use `../texture-and-mesh/`.
- API server/Gradio/Blender client behavior: use `../services-and-integrations/`.

## Essential references

- [Installation and backends](references/installation-and-backends.md) for installation order, CUDA extension build guidance, and backend readiness checks.
- [Model overview](references/model-overview.md) for model repo/subfolder selection, VRAM guidance, and cache behavior.
- [Troubleshooting](references/troubleshooting.md) for common install/backend failures and stale documentation warnings.

## Bundled helper

- [scripts/check_install.py](scripts/check_install.py) checks package metadata/imports and optional CUDA/extension readiness without downloading model weights.

Examples:

```bash
python scripts/check_install.py --json
python scripts/check_install.py --check-cuda --json
python scripts/check_install.py --check-cuda --check-extensions --json
```

A passing helper check proves installation/backend readiness for the selected probes. It does not prove that full model inference ran or that model checkpoints are cached.
