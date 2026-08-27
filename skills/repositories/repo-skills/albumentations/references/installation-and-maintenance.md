# Installation and maintenance

## Package baseline

- Distribution/import package: `albumentations`.
- Covered version: `2.0.8`.
- Python requirement: Python `>=3.9`.
- Core runtime dependencies include NumPy, SciPy, PyYAML, Pydantic v2, Albucore, and an OpenCV Python package. The setup logic prefers an already installed OpenCV provider; otherwise it selects a headless OpenCV package.
- Optional extras: `pytorch` installs PyTorch support, `hub` installs Hugging Face Hub support, and `text` installs Pillow-backed text functionality.

## Recommended install checks

```bash
python -m pip install albumentations
NO_ALBUMENTATIONS_UPDATE=1 python - <<'PY'
import albumentations as A
print(A.__version__)
print(A.Compose([A.NoOp()])(image=__import__('numpy').zeros((2, 2, 3), dtype='uint8'))['image'].shape)
PY
```

Set `NO_ALBUMENTATIONS_UPDATE=1` in deterministic or offline automation. Without it, importing Albumentations can attempt a version check and emit a warning if the network is blocked or slow.

## OpenCV choice

Albumentations imports `cv2` through its core transforms. In headless servers and CI, prefer `opencv-python-headless` or an environment where `cv2` already imports. Avoid installing multiple conflicting OpenCV wheels in the same environment unless you know which package owns `cv2`.

## Optional extras

Install optional extras only for workflows that need them:

```bash
python -m pip install "albumentations[pytorch]"
python -m pip install "albumentations[hub]"
python -m pip install "albumentations[text]"
```

A base install may not export `A.ToTensorV2` or `A.ToTensor3D`; route tensor workflows to `sub-skills/framework-integration/` and check `from albumentations.pytorch import ToTensorV2` after installing compatible PyTorch.

## Maintenance status

The source README states that the original Albumentations repository is no longer actively maintained and that active development moved to AlbumentationsX. For existing MIT-licensed projects, this skill remains useful for stabilizing current Albumentations 2.x pipelines. For new long-term projects, mention the maintenance trade-off and licensing implications before recommending migration.
