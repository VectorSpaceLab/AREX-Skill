# Model and Checkpoint Notes

## Default Inference Model

The Python image and video inference paths use:

- checkpoint: `models/phase1_wpdc_vdc.pth.tar`
- architecture function: `mobilenet_1`
- class count / output dimension: `62`
- input tensor shape: `N x 3 x 120 x 120`
- preprocessing: OpenCV BGR image crop resized to `120x120`, tensor channel order `3x120x120`, normalized with mean `127.5` and std `128`

A safe forward smoke for the default architecture must return shape `(1, 62)` for a single random input. From this sub-skill directory, use:

```bash
python scripts/smoke_mobilenet_forward.py --repo-root /path/to/3DDFA --arch mobilenet_1 --num-classes 62
```

This smoke is intentionally checkpoint-free. It validates architecture import and forward shape only.

## MobileNet Architecture Choices

The repo defines the following MobileNet-V1 width variants:

| Function | Width factor | Default `num_classes` | Notes |
|---|---:|---:|---|
| `mobilenet_2` | `2.0` | `62` | Wider than default; checkpoint-incompatible unless trained for this width. |
| `mobilenet_1` | `1.0` | `62` | Default inference architecture. |
| `mobilenet_075` | `0.75` | `62` | Narrower; checkpoint-incompatible with default checkpoint. |
| `mobilenet_05` | `0.5` | `62` | Narrower; checkpoint-incompatible with default checkpoint. |
| `mobilenet_025` | `0.25` | `62` | Narrowest; checkpoint-incompatible with default checkpoint. |

All variants accept `input_channel=3`. Do not change architecture, width, or `num_classes` when loading `phase1_wpdc_vdc.pth.tar` unless you also provide a matching checkpoint.

## 62-Parameter Output Layout

The 62-float output vector is decoded as:

- first 12 values: camera/pose matrix parameters;
- next 40 values: shape coefficients;
- final 10 values: expression coefficients.

The parameter vector is re-whitened by means/stds from `train.configs/param_whitening.pkl` before reconstructing landmarks or dense vertices. Sparse 68 landmarks and dense vertices share the same 62 parameters but use different 3DMM bases from `train.configs`.

## Checkpoint Loading Semantics

The native inference loaders:

1. load the checkpoint with CPU `map_location`;
2. read the checkpoint's `state_dict` key;
3. create `mobilenet_1(num_classes=62)`;
4. copy checkpoint tensors into the model state dict while stripping a leading `module.` prefix from multi-GPU training;
5. call `load_state_dict` and switch the model to `eval()`;
6. move model/input to CUDA only when `--mode gpu` is exact.

Operational implications:

- A checkpoint missing `state_dict` will not load in the native path.
- A checkpoint trained under a different MobileNet width or output dimension will not match the default model.
- The default checkpoint is loaded from a hard-coded path; the image/video CLIs do not expose a checkpoint flag.
- CPU loading is supported even for checkpoints trained with DataParallel because `module.` is stripped.

## Required Runtime Resources

The inference decode path needs more than the model weights:

| Resource | Why it matters |
|---|---|
| `models/phase1_wpdc_vdc.pth.tar` | Default MobileNet checkpoint. |
| `train.configs/keypoints_sim.npy` | Sparse keypoint selection for 68 landmarks. |
| `train.configs/w_shp_sim.npy`, `train.configs/w_exp_sim.npy` | Shape/expression bases. |
| `train.configs/u_shp.npy`, `train.configs/u_exp.npy` | Mean shape/expression components. |
| `train.configs/param_whitening.pkl` | Parameter mean/std for re-whitening. |
| `train.configs/Model_PAF.pkl` | PAF anchor model. |
| `train.configs/pncc_code.npy` | PNCC color code. |
| `visualize/tri.mat` | Triangle topology for PLY/OBJ/depth/PNCC rendering. |

Use `scripts/inspect_3ddfa_inference.py` to check these before native inference.

## Version Sensitivities

The source documentation reported successful testing around PyTorch 1.1.0 with Python 3.6+ and older NumPy/Matplotlib versions. Modern runtimes can still run the MobileNet smoke, but native inference may expose legacy issues:

- `np.int` use in PAF code can fail on NumPy 1.24+.
- Cython render extension must match the active Python ABI.
- `dlib` installation can be brittle and is imported before argument parsing.
- GUI display from Matplotlib/OpenCV should be disabled or wrapped in headless environments.
