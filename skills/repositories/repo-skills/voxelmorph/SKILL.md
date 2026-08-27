---
name: voxelmorph
description: "Use VoxelMorph's current PyTorch image-registration package for
  dense transforms, VxmPairwise registration models, VoxelMorph data generators,
  and medical-volume workflow troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VoxelMorph repo skill

Use this skill when a task involves VoxelMorph's current PyTorch package surface for learning-based medical image registration, dense deformation fields, pairwise registration models, VoxelMorph volume data conventions, or related troubleshooting.

## Best-fit tasks

- Build, inspect, or smoke-test VoxelMorph PyTorch registration code.
- Work with affine matrices, dense displacement fields, normalized coordinates, spatial warping, integration, resizing, composition, or random transforms.
- Construct or call `voxelmorph.nn.models.VxmPairwise` and understand its forward outputs.
- Prepare VoxelMorph `.npz`, NIfTI, MGZ, list-file, segmentation, atlas, or generator inputs.
- Diagnose VoxelMorph import errors, Neurite dependency issues, stale TensorFlow-era examples, deprecated loss classes, or missing legacy APIs.

## Avoid this skill when

- The task is about a different medical-imaging framework such as MONAI, nnU-Net, or TorchIO without a VoxelMorph-specific API question.
- The user needs clinical validation, benchmark-quality training, dataset acquisition, or model downloads but has not supplied concrete data, runtime, and acceptance criteria.
- The user explicitly asks for the stable TensorFlow branch or old `VxmDense`/`.h5` workflows; this skill covers the current PyTorch branch and flags those old surfaces as compatibility issues.

## Install and first checks

Basic package install:

```bash
python -m pip install voxelmorph
python - <<'PY'
import voxelmorph as vxm
import neurite
import torch
print(vxm.__version__, neurite.__version__, torch.__version__)
PY
```

For a source checkout, use an isolated environment and editable install:

```bash
python -m pip install -e .
python -m pip check
```

Then run the bundled root checker when VoxelMorph is available in the active environment:

```bash
python scripts/check_voxelmorph_env.py --help
python scripts/check_voxelmorph_env.py
```

Read [install and compatibility](references/install-and-compatibility.md) before using old tutorials, GPU environments, source installs, or checkpoints from another branch.

## Route map

| User intent | Read next | Why |
| --- | --- | --- |
| Affine/displacement fields, coordinate normalization, `spatial_transform`, scaling-and-squaring, `SpatialTransformer`, transform composition, random fields | [transform-ops](sub-skills/transform-ops/SKILL.md) | Owns tensor transform APIs and shape/sign/interpolation guidance. |
| `VxmPairwise` construction, forward return modes, tiny training loops, Neurite losses, checkpoint patterns, legacy registration-script caveats | [pairwise-registration](sub-skills/pairwise-registration/SKILL.md) | Owns current PyTorch model workflows and safe synthetic training smoke. |
| `.npz`/NIfTI/MGZ volume I/O, `vol`/`seg` schemas, labels, Dice/Jacobian helpers, scan-to-scan/atlas/semisupervised/template/surface/SynthMorph generators | [data-generators](sub-skills/data-generators/SKILL.md) | Owns data contracts and NumPy generator selection before model code. |
| Package import, dependency, branch/API drift, deprecated losses, optional CUDA, or stale docs | [root troubleshooting](references/troubleshooting.md) | Cross-cutting triage before routing to a sub-skill. |
| Staleness check for a checkout | [repo provenance](references/repo-provenance.md) | Records commit, package version, and evidence paths used to create this skill. |

## Current API anchors

- Package import: `import voxelmorph as vxm`.
- Pairwise model: `vxm.nn.models.VxmPairwise`.
- Transform functions: top-level `vxm.affine_to_disp`, `vxm.spatial_transform`, `vxm.integrate_disp`, `vxm.resize_disp`, `vxm.compose`, plus `vxm.nn.functional` for `(B, C, *spatial)` neural-network layouts.
- Transform modules: `vxm.nn.modules.SpatialTransformer`, `IntegrateVelocityField`, `ResizeDisplacementField`.
- Data utilities and generators: `vxm.py.utils` and `vxm.py.generators`.
- Losses: use `neurite.nn.modules`; VoxelMorph loss classes are deprecated stubs in this branch.

## Important branch warnings

- Do not route future agents to old TensorFlow script paths or `.h5` model-loading commands unless the user intentionally switches to the TensorFlow branch.
- Do not use `vxm.networks.VxmDense.load(...)` as a current runnable API; this branch exposes `VxmPairwise` under `vxm.nn.models`.
- Source example scripts are evidence, not runtime dependencies. Reusable safe behavior is distilled into this skill's bundled scripts and references.
- CPU is sufficient for the bundled smokes and package inspection. Verify a CUDA-capable PyTorch install separately before claiming GPU execution.

## Bundled root files

- [Install and compatibility](references/install-and-compatibility.md): package identity, dependencies, backend guidance, and branch/API drift notes.
- [Troubleshooting](references/troubleshooting.md): cross-cutting failure triage and links to sub-skill-specific fixes.
- [Repo provenance](references/repo-provenance.md): source commit, package version, and evidence baseline for refresh decisions.
- [Router metadata](references/repo-routing-metadata.json): structured placement for `repo-skills-router` import tools.
- [Environment checker](scripts/check_voxelmorph_env.py): safe import, signature, model, and transform smoke check.

## Operating sequence

1. Identify whether the task is transform math, pairwise model work, or data/generator preparation.
2. Run the smallest relevant bundled smoke or validator before changing real workflows.
3. Keep `.npz` schema and tensor shape conventions explicit when moving between sub-skills.
4. Treat old TensorFlow/VxmDense material as a compatibility question, not as a current runnable path.
5. Stop for explicit user data/runtime decisions before long training, downloads, GPU-only execution, checkpoint conversion, or quality claims.
