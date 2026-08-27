---
name: gradslam
description: "Routes GradSLAM package workflows for RGB-D structures, tensor
  geometry, odometry and SLAM, dataset adapters, and CfgNode configuration on a
  CPU-first installation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GradSLAM operating guide

Use this repo skill when a Researcher needs the public `gradslam` Python
package for dense RGB-D geometry, RGB-D/point-cloud structures, odometry,
PointFusion or ICPSLAM, TUM/ICL/ScanNet loading, or `CfgNode` configuration.
This is operating context for a later Researcher, not a benchmark recipe and
not a replacement for the package's external datasets.

## Start here

1. Create an isolated environment, then install the public release with
   `python -m pip install gradslam`. When the exact source baseline is required,
   install the pinned public Git revision instead:
   `python -m pip install 'git+https://github.com/gradslam/gradslam.git@44470eee4484aaad703d7bf962a8f42496867a9d'`.
2. Run `python -m pip check`, then resolve and run the bundled environment
   diagnostic `scripts/check_environment.py`. Start with `--help`; the script
   reports import and backend facts without installing or changing anything.
3. Read [compatibility](references/compatibility.md) before selecting a
   dependency combination. CPU is the required verified path; successful CPU
   execution does not certify CUDA.
4. Record the input tensor contract, device, image layout, depth units, pose
   availability, and external-data boundary before calling package APIs.
5. Route to exactly one focused sub-skill, then use its API/reference page and
   its deterministic helper where one exists.

## Route by user intent

- **RGB-D tensors, vertex/normal maps, point-cloud conversion, ragged clouds,
  or safe display adapters:** [structures](sub-skills/structures/SKILL.md).
- **Projection, unprojection, intrinsics, pixel grids, rigid transforms,
  quaternions, or SE(3):** [geometry](sub-skills/geometry/SKILL.md).
- **Known-pose, ICP, GradICP, PointFusion, ICPSLAM, map fusion, or odometry
  diagnostics:** [odometry-slam](sub-skills/odometry-slam/SKILL.md).
- **TUM, ICL-NUIM, ScanNet paths, association metadata, preprocessing, labels,
  or DataLoader handoff:** [datasets](sub-skills/datasets/SKILL.md).
- **Nested config trees, YAML/Python files, merge precedence, overrides,
  freezing, or migration diagnostics:** [configuration](sub-skills/configuration/SKILL.md).

Cross-skill routing is intentional: datasets produce the RGB-D batch,
structures validate its layout, geometry supplies transforms, and odometry/SLAM
consumes the resulting objects. Do not skip the upstream shape and units check.

## Package boundaries

- The package imports Open3D during `import gradslam`; a missing or incompatible
  optional-looking dependency can therefore be an import blocker.
- The historical package metadata permits older Torch/dependency combinations,
  but exact compatibility is release- and extension-dependent. Follow the
  compatibility and troubleshooting references instead of blindly upgrading
  one binary package.
- External TUM, ICL-NUIM, and ScanNet data are not bundled. Layout checks are
  read-only preflight, not proof that images, poses, or timestamp association
  are valid.
- The bundled smoke programs use tiny deterministic in-memory CPU fixtures.
  They do not validate an external sequence, a full benchmark, CUDA behavior,
  a GUI viewer, or notebook execution.
- Keep colors, depths, intrinsics, poses, and map tensors on a deliberate
  device. Keep names, transforms, timestamps, semantic labels, and config
  metadata outside `RGBDImages` unless an API explicitly accepts them.

## Self-contained references

- [API surface](references/api-surface.md) — package exports and direct-module
  entry points.
- [Compatibility](references/compatibility.md) — supported claims, dependency
  caveats, and CPU/CUDA boundaries.
- [Troubleshooting](references/troubleshooting.md) — install/import, extension,
  device, data, and cross-workflow failures.
- [Provenance](references/repo-provenance.md) — source version and evidence
  baseline.
- [Environment checker](scripts/check_environment.py) — no-mutation import and
  backend diagnostic.

## Safe operating sequence

Prefer a short, observable progression: import check → tiny tensor or config
fixture → focused sub-skill smoke → one small caller-owned data item → only then
longer SLAM or dataset work. Stop when a required invariant fails. Do not
invent poses, silently rescale depth, download data, open a viewer, or claim an
accelerator path from a CPU-only result.
