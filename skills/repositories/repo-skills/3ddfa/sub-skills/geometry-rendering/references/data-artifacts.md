# Data Artifacts

This sub-skill relies on a small set of repository-bundled arrays and mesh artifacts. They are read as data contracts, not as code.

## Geometry artifacts

| File | Shape / type | Role |
| --- | --- | --- |
| `visualize/tri.mat` | `tri` with shape `(3, 105840)`, `uint16` | Canonical triangle list for the 68-landmark and dense face meshes. Values are 1-based on disk. |
| `train.configs/keypoints_sim.npy` | `(204,)`, `int64` | Keypoint remapping indices used by `utils.params`. |
| `train.configs/u_shp.npy` | `(159645, 1)`, `float32` | Mean 3DMM shape basis. |
| `train.configs/u_exp.npy` | `(159645, 1)`, `float32` | Mean expression basis. |
| `train.configs/w_shp_sim.npy` | `(159645, 40)`, `float32` | Shape basis used for the simplified 68-point branch. |
| `train.configs/w_exp_sim.npy` | `(159645, 10)`, `float32` | Expression basis used for the simplified 68-point branch. |
| `train.configs/pncc_code.npy` | `(3, 53215)`, `float32` | Mean-shape PNCC code used by `utils.render.cpncc`. |
| `train.configs/param_whitening.pkl` | `param_mean`, `param_std`, both `(62,)` | Whitening statistics for the 62-D parameter vector. |
| `train.configs/Model_PAF.pkl` | `mu_filter`, `w_filter`, `w_exp_filter` | Simplified face basis used by `utils.paf`. |

## How the package uses them

- `utils.params` loads these artifacts at import time and exposes the derived arrays used by geometry, rendering, and PAF helpers.
- `utils.ddfa.reconstruct_vertex` consumes the whitened parameter statistics.
- `utils.render.cpncc` consumes `pncc_code`.
- `utils.paf` consumes the filter bases for the PAF anchor.

## BFM neck-removal warning

`BFM_Remove_Neck/readme.md` warns that the z-axis values of `bfm.ply` and `bfm_refine.ply` are opposite in `model_refine.mat`. Do not use those PLY files as training inputs unless you intentionally reconcile the axis convention first.

## Practical interpretation

- `visualize/tri.mat` is the mesh topology contract.
- `train.configs` is the basis/statistics contract.
- `BFM_Remove_Neck/` is a preprocessing and visualization note, not a general-purpose runtime dependency.
