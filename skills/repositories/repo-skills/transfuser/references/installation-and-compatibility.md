# Installation and Compatibility

Read this reference before installing dependencies or moving a TransFuser run to
another machine. It records the repository's verified legacy compatibility
contract and separates package-only checks from the external CARLA runtime.

## Historical stack

The checkout documents a Conda environment with Python 3.7 and a requirements
set centered on:

- PyTorch `1.12.1+cu113`, torchvision `0.13.1+cu113`, and torchaudio
  `0.12.1` from the CUDA 11.3 wheel family.
- `torch-scatter` matching PyTorch/CUDA, `mmcv-full==1.6.0` from the
  `cu113/torch1.12` wheel index, `mmsegmentation==0.25.0`, `mmdet==2.25.0`,
  and `mmcls==0.25.0`.
- `timm==0.6.7`, NumPy `1.21.6`, OpenCV `4.6.0.66`, Pillow `9.2.0`,
  scikit-image `0.19.3`, `ujson`, `tqdm`, `diskcache`, TensorBoard, Shapely,
  and the data/evaluation utilities used by the selected workflow.

This is a compatibility baseline, not a guarantee that every future platform
can install the historical wheels. Keep the framework, CUDA tag, Python ABI,
and compiled extensions aligned. If a port uses a modern stack, treat it as a
new implementation that needs fresh import, model-construction, and inference
verification rather than as a drop-in upgrade.

## Backend gates

### Learned workflows: CUDA required

`train.py` unconditionally selects a CUDA device and the sensor agent constructs
CUDA tensors and models. Require all of the following before training or learned
inference:

1. `torch.cuda.is_available()` is true.
2. A tiny CUDA allocation succeeds on the actual target GPU.
3. `mmcv.ops`, `mmdet`, `mmsegmentation`, `mmcls`, and `torch_scatter` import
   without ABI errors.
4. The selected backbone, image/lidar architectures, checkpoint provenance,
   and compiled extension versions match.

A CPU import, `--help`, or `pip check` is useful diagnostics but does not prove
this gate.

### Simulation workflows: CARLA required

Data generation and evaluation require CARLA `0.9.10.1`, its Python API egg,
a compatible ScenarioRunner/leaderboard tree, the route/scenario assets, and a
running `CarlaUE4.sh` server. Check the server and Python API independently;
never infer simulator readiness from a package-only import.

Use the command builders in the `data-and-routes` and `carla-evaluation`
sub-skills to inspect paths and emit a plan without starting the server. The
full simulator is deliberately not downloaded by this skill.

## Minimal runtime probe

From the generated skill root, run:

```bash
python scripts/check_environment.py --json
```

The probe reports Python, PyTorch/CUDA, selected compiled packages, optional
CARLA importability, and whether the caller supplied a repository root. It is
read-only and does not import the project's heavyweight model or start CARLA.
Use the workflow-specific `--check-runtime` or preflight only after confirming
that the environment is the intended isolated runtime.

## External assets and side effects

- The public training data download is about 210 GB and requires network,
  storage, and license acceptance. Validate a small local fixture first.
- Pretrained model archives are external downloads. Verify `args.txt`, checkpoint
  names, and architecture provenance before loading them.
- Docker packaging copies CARLA/ScenarioRunner/leaderboard/team-code trees and
  builds a GPU-capable image. Use the submission preflight; do not run a build
  as an import or smoke check.
- Cloud leaderboard submission requires an account, credentials, network, and
  an uploaded image. Keep it outside automated verification.
