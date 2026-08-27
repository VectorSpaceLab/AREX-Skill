# Environment and verification guidance

## Public installation baseline

VAD documents a legacy OpenMMLab stack. A compatible environment normally includes:

```text
Python 3.8-era runtime
PyTorch with CUDA support (the repository documents 1.9.1+cu111)
torchvision matching PyTorch
mmcv-full 1.4.0
mmdet 2.14.0
mmsegmentation 0.14.1
timm
mmdetection3d v0.17.1
nuscenes-devkit 1.1.9
```

Install PyTorch/torchvision using a wheel or build compatible with the host CUDA driver, then install the matching OpenMMLab wheels and build/install MMDetection3D v0.17.1 with its native operators. Do not use the repository's full historical `requirements.txt` as a request to install unrelated notebooks, CARLA, or every development package.

A minimal generic probe is:

```bash
python -c "import torch, mmcv, mmdet, mmseg, mmdet3d; print(torch.__version__, mmcv.__version__, mmdet.__version__, mmseg.__version__, mmdet3d.__version__)"
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"
```

If the second probe is false, do not claim that VAD model execution is supported. If `mmdet3d` imports but `mmdet3d.datasets`, `mmdet3d.models`, or a custom op fails, the native extension build is incomplete or ABI-incompatible.

## Native extension gate

VAD plugin imports reach MMDetection3D operators such as ball query, IoU, voxel, and related CUDA extensions. Verify the version-matched `.so` modules and a minimal operator import before attempting a model build. Compiler/CUDA version, PyTorch ABI, Python version, and GPU architecture all matter.

A config parse with `mmcv.Config.fromfile` is intentionally a weaker check: it validates Python config inheritance and syntax but does not import every plugin or build a detector.

## Verification scope for this skill

Safe checks:

- dependency/version and CUDA probes;
- config parsing and structural checks;
- bundled data-layout and result-artifact inspectors;
- CLI contract/static checks without training or data downloads.

Bounded checks:

- full temporal conversion needs external nuScenes/CAN-bus data;
- plugin/model construction needs working native extensions and CUDA;
- training/evaluation needs data and checkpoints and is intentionally expensive;
- rendering needs a compatible result artifact plus the full nuScenes sensor/calibration tree.

Keep all skipped checks explicit. Do not turn a missing dataset/checkpoint or failed native build into an `ok` end-to-end claim.
