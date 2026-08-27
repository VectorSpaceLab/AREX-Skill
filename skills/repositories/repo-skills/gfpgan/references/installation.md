# GFPGAN Installation and Runtime Setup

## Purpose

Read this before installing GFPGAN, selecting a PyTorch/CUDA stack, deciding whether Real-ESRGAN is needed, or diagnosing why an inference/training environment imports but cannot run model code.

## Package Roles

| Package | Why GFPGAN needs it | Notes |
| --- | --- | --- |
| `torch`, `torchvision` | model execution, tensors, losses, CUDA support | Match the wheel to the target CUDA runtime when GPU use is required. |
| `basicsr` | training pipeline, losses, utilities, architecture registries, image IO, degradation helpers | GFPGAN training and inference import BasicSR utilities. Original/paper model paths may use BasicSR custom/JIT ops. |
| `facexlib` | face detection/alignment/restoration helper used by `GFPGANer` | Missing facexlib usually breaks inference before model weights load. |
| `opencv-python` | image read/write, resize, color conversion, JPEG degradation | OpenCV/NumPy incompatibilities can surface in dataset degradation or image IO. |
| `lmdb` | LMDB dataset backend for FFHQ training fixtures | Required for LMDB data layouts and tests. |
| `pyyaml` | training/config parsing | Required by BasicSR config workflows. |
| `scipy`, `tqdm`, `numpy` | scientific utilities, progress, arrays | Used across BasicSR/facexlib/GFPGAN workflows. |
| `realesrgan` | optional background upsampling for non-face regions | Install only when the user wants background enhancement. |

## Common Install Patterns

For a normal package/application environment:

```bash
pip install gfpgan
python - <<'PY'
from gfpgan import GFPGANer
print('GFPGAN import ok:', GFPGANer)
PY
```

For a source checkout that the user is actively developing:

```bash
pip install -r requirements.txt
pip install -e .
```

For optional background enhancement:

```bash
pip install realesrgan
```

Do not install Real-ESRGAN only to run GFPGAN face restoration without a background upsampler; `bg_upsampler=None` is valid and is the safer CPU/default path.

## CUDA and CPU Expectations

- Clean GFPGAN models can be loaded on CPU or CUDA, but practical full-image restoration is much faster on CUDA.
- The original `1` paper model uses the `original` architecture. Its install path can need BasicSR JIT or compiled extensions. If the user only needs modern clean inference, prefer `1.3` or `1.4`.
- The original `inference_gfpgan.py` avoids Real-ESRGAN background upsampling on CPU because it is slow; use no background upsampler or explicitly accept slow CPU behavior.
- Training is not CPU-realistic for normal datasets. Use GPU/multi-GPU planning and small smoke tests for validation only.

## Checkpoint Placement

GFPGAN workflows need local model checkpoints unless the user explicitly allows downloads. Common filenames:

| Version | Architecture | Typical checkpoint filename | Notes |
| --- | --- | --- | --- |
| `1` | `original` | `GFPGANv1.pth` | Original paper model; may need BasicSR JIT/extensions. |
| `1.2` | `clean` | `GFPGANCleanv1-NoCE-C2.pth` | Clean model, sharper/makeup-like outputs. |
| `1.3` | `clean` | `GFPGANv1.3.pth` | More natural restoration, often a safe default. |
| `1.4` | `clean` | `GFPGANv1.4.pth` | More details and better identity in later demos. |
| `RestoreFormer` | `RestoreFormer` | `RestoreFormer.pth` | Alternative architecture exposed by the repo inference script. |

For training, additional checkpoints are typically required:

- `StyleGAN2_512_Cmul1_FFHQ_B12G4_scratch_800k.pth`
- `FFHQ_eye_mouth_landmarks_512.pth` when using component crops
- `arcface_resnet18.pth` when identity loss is enabled

## Version-Aligned Inspection Facts

The source evidence for this skill used GFPGAN package version `1.3.8`. The important verified signatures are:

```python
GFPGANer(model_path, upscale=2, arch='clean', channel_multiplier=2, bg_upsampler=None, device=None)
GFPGANer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True, weight=0.5)
```

If a future package changes these signatures, refresh this repo skill.
