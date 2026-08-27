---
name: registration-workflows
description: "Use Torch Points3D registration datasets, configs, pair/fragment
  contracts, descriptor evaluation notes, FPS sampling, and backend caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Torch Points3D Registration Workflows

Use this sub-skill when the user asks about Torch Points3D registration tasks:
3DMatch fragments/patches, KITTI, ETH/TUM/KAIST/Planetary test sets, pair data,
fragment descriptor files, FPS sampling, registration model configs, or
registration-specific sparse/Open3D/backend issues.

## Read First

- Read [registration workflows](references/registration-workflows.md) for config families, train/test command shape, data contracts, and model choices.
- Read [registration evaluation](references/registration-evaluation.md) for descriptor file expectations, matching/evaluation concepts, and why repo demos are not safe default scripts.
- Read [registration troubleshooting](references/troubleshooting.md) for missing pair fields, feature files, ground-truth transforms, sparse backends, Open3D, and CUDA-only assumptions.
- Run [fps_registration_smoke.py](scripts/fps_registration_smoke.py) for a tiny CPU check of Torch Points3D's registration FPS utility.

## Main Workflows

### Choose a registration config

Common data config families include:

- `registration/fragment3dmatch`, `fragment3dmatch_dense`, `fragment3dmatch_partial`, `fragment3dmatch_sparse`, and sparse single-scale variants.
- `registration/patch3dmatch` for patch-level 3DMatch.
- `registration/fragmentkitti_sparse` for KITTI fragment registration.
- `registration/modelnet_sparse_ss` for siamese ModelNet.
- Test/evaluation configs such as `test3dmatch`, `testeth`, `testtum`, `testkaist`, and `testplanetary`.

Common model config groups include `registration/kpconv`, `registration/pointnet2`,
`registration/pointnet2_patch`, `registration/minkowski`, `registration/spconv3d`,
and `registration/ms_svconv_base`.

### Validate a pair/FPS utility path

```bash
python sub-skills/registration-workflows/scripts/fps_registration_smoke.py --json
```

This checks `torch_points3d.datasets.registration.utils.fps_sampling` using a
small in-memory tensor fixture. It does not prove full 3DMatch/KITTI evaluation,
but it is a safe first signal that the registration utility import path and CPU
PyG/PyTorch stack are usable.

### Plan descriptor evaluation

Registration evaluation scripts in the source repository assume real fragment
features, ground-truth logs, optional Open3D visualization, and sometimes
Minkowski/CUDA dependencies. Use [registration evaluation](references/registration-evaluation.md)
to map required inputs before running a user's local evaluation script.

## Boundary Rules

- For generic model constructor signatures and sparse backend selection, use [model-apis](../model-apis/SKILL.md).
- For registration data layouts that reduce to generic dataset/transform class lookup, use [datasets-transforms](../datasets-transforms/SKILL.md).
- For Hydra `train.py`/`eval.py` selector syntax and checkpoint/logging behavior, use [training-evaluation](../training-evaluation/SKILL.md).

## Safety Checklist

- Do not run registration demos or descriptor evaluation until the user provides required fragment/feature/ground-truth files and accepts output writes or visualization.
- Treat `MinkowskiEngine`, `torchsparse`, and CUDA as optional but required for specific sparse registration models.
- Distinguish pair/patch/fragment data contracts; a config for one family will not necessarily work with another.
- Use CPU utility smokes and config composition before heavy registration evaluation.
