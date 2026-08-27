# GradSLAM API surface

Use the focused sub-skill references for signatures and shape contracts. This
page only answers where to look and which imports are stable at the package
boundary.

## Package-level imports

`import gradslam` loads Open3D, exposes the package version, re-exports the
projective geometry functions, metrics, and structure classes, and imports the
odometry and SLAM namespaces. The package-level structure entry points include
`RGBDImages` and `Pointclouds`. Use the environment checker before treating a
missing dependency as an API error.

The package-level geometry exports are the projective functions:

- `homogenize_points`;
- `unhomogenize_points`;
- `project_points`;
- `unproject_points`;
- `inverse_intrinsics`.

Do not assume every helper under `geometryutils` or `se3utils` is re-exported.
Import those modules directly as shown below.

## Focused direct modules

```python
from gradslam.config import CfgNode
from gradslam.datasets.tum import TUM
from gradslam.datasets.icl import ICL
from gradslam.datasets.scannet import Scannet
from gradslam.geometry.geometryutils import (
    cam2pixel, compose_transforms_3d, create_meshgrid,
    relative_transformation, transform_normals, transform_pointcloud,
    transform_pts_3d,
)
from gradslam.geometry.se3utils import se3_exp, so3_exp
from gradslam.odometry import (
    GroundTruthOdometryProvider, ICPOdometryProvider,
    GradICPOdometryProvider,
)
from gradslam.slam import ICPSLAM, PointFusion
```

The `Scannet` spelling is the implementation's public class name. Dataset
adapters are file-backed and return variable-length tuples controlled by return
flags; see the datasets sub-skill rather than assuming `None` placeholders.

## Cross-workflow data flow

```text
caller files
  → datasets.TUM / ICL / Scannet
  → DataLoader tensors: (B,L,H,W,3), (B,L,H,W,1), (B,1,4,4), optional poses
  → structures.RGBDImages
  → vertex/normal maps or structures.Pointclouds
  → geometry transforms/projection as needed
  → odometry providers, PointFusion, or ICPSLAM
```

`RGBDImages` accepts channels-last `(B,L,H,W,C)` or channels-first
`(B,L,C,H,W)` RGB/depth tensors, with matching intrinsics and optional poses.
`Pointclouds` accepts ragged lists or padded `(B,N,3)` point tensors. Preserve
batch/device/layout metadata across each handoff.

## API caveats

- `se3_exp` is a direct `se3utils` import and consumes a six-vector ordered as
  translation followed by rotation in this release.
- `inverse_intrinsics` is the package's supported pinhole inverse helper, not a
  promise of arbitrary matrix inversion.
- `ICPSLAM` and `PointFusion` validate `odom` against `gt`, `icp`, and
  `gradicp`; their solver and fusion defaults are in the odometry-slam API
  reference.
- `CfgNode` is a nested configuration object, not an application-wide schema.
  The caller owns model, dataset, and command-line key definitions.
- Visualization adapters can construct Open3D/Plotly objects, but display is
  outside the safe CPU smoke path.
