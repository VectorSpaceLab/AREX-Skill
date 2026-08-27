# Model and asset map

| Asset | Used by | Why it matters | Notes |
| --- | --- | --- | --- |
| `configs/mb1_120x120.yml` | default demos and benchmarks | Default MobileNet V1 configuration | Points to `weights/mb1_120x120.pth` and `configs/bfm_noneck_v3.pkl`. |
| `configs/mb05_120x120.yml` | demo variants | Smaller and faster MobileNet V1 variant | Uses `widen_factor: 0.5` and `weights/mb05_120x120.pth`. |
| `configs/resnet_120x120.yml` | alternate backbone experiments | ResNet-22 configuration | Needs `weights/resnet22.pth` or the converted ONNX model. |
| `configs/bfm_noneck_v3.pkl` | `TDDFA` / `TDDFA_ONNX` | Basel Face Model parameters and topology | Public academic asset; large binary file not bundled into the skill. |
| `configs/tri.pkl` | dense reconstruction and renderers | Triangle indices for the BFM variant used here | Required when the `bfm_noneck_v3.pkl` layout is used. |
| `configs/BFM_UV.mat` | `uv_tex` | UV coordinate map | Required for texture mapping. |
| `configs/indices.npy` | `uv_tex` | UV index subset for the BFM layout | Used together with `BFM_UV.mat`. |
| `configs/param_mean_std_62d_120x120.pkl` | `TDDFA` | Parameter normalization stats | Default stats file for the 62D MobileNet models. |
| `weights/mb1_120x120.pth` | default `TDDFA` demo path | Main MobileNet V1 checkpoint | Public download link recorded in `weights/readme.md`. |
| `weights/mb05_120x120.pth` | smaller demo path | Smaller MobileNet V1 checkpoint | Public download link recorded in `weights/readme.md`. |
| `weights/resnet22.pth` | ResNet config path | Alternate backbone checkpoint | Used only if `configs/resnet_120x120.yml` is selected. |
| `FaceBoxes/weights/FaceBoxesProd.pth` | face detector | Detector checkpoint for the first pipeline stage | Public download link recorded in `FaceBoxes/weights/readme.md`. |
| `weights/mb1_120x120.onnx` | `speed_cpu.py` and ONNX demo path | Optional preconverted inference model | Auto-generated from `weights/mb1_120x120.pth` if absent. |
| `FaceBoxes/weights/FaceBoxesProd.onnx` | ONNX detector path | Optional preconverted detector model | Auto-generated from `FaceBoxesProd.pth` if absent. |
| `configs/bfm_noneck_v3.onnx` | ONNX reconstruction path | Optional ONNX BFM decoder | Auto-generated from `configs/bfm_noneck_v3.pkl` if absent. |

## Input media

The runtime demos expect caller-supplied image or video paths. Local smoke
fixtures can be used when a checkout includes them, but they are not part of the
generated skill itself.

## Output locations

- Still-image and render outputs default to `examples/results/`.
- Video outputs default to `examples/results/videos/`.

## Acquisition notes

The public download links for the checkpoint assets live in:

- `weights/readme.md`
- `FaceBoxes/weights/readme.md`
- `bfm/readme.md`
- `configs/readme.md`

Use those notes when a fresh checkout is missing the binary assets required by
one of the demo or benchmark workflows.
