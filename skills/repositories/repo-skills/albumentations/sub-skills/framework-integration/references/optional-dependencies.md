# Optional Dependencies Reference

Albumentations 2.0.8 keeps several framework features behind optional dependencies. A base install can augment NumPy arrays without PyTorch, Hugging Face Hub, or Pillow text support.

## Extras

| Feature | Extra | Package required | What it enables |
| --- | --- | --- | --- |
| PyTorch tensor conversion | `albumentations[pytorch]` | `torch` | `albumentations.pytorch`, `ToTensorV2`, and `ToTensor3D`. |
| Hugging Face Hub integration | `albumentations[hub]` | `huggingface-hub` | `save_pretrained`, `from_pretrained`, and hub upload/download helpers on serializable transforms. |
| Text image transforms | `albumentations[text]` | `pillow` | PIL font/image support used by text rendering transforms. |

Install only the extras needed by the project:

```bash
pip install "albumentations[pytorch]"
pip install "albumentations[hub]"
pip install "albumentations[text]"
```

If a project already pins `torch`, install a compatible PyTorch build first using the project's hardware/backend policy, then install Albumentations. The `pytorch` extra only declares `torch`; it does not choose CUDA, CPU, ROCm, or platform-specific wheels for you.

## PyTorch Export Behavior

At import time, Albumentations attempts to expose PyTorch transforms from the top-level `albumentations` namespace only if importing the PyTorch module succeeds. If `torch` is missing or incompatible, the import error is suppressed and these names are absent:

```python
import albumentations as A

if not hasattr(A, "ToTensorV2"):
    raise RuntimeError("Install torch or albumentations[pytorch] before using ToTensorV2")
```

Prefer explicit imports in PyTorch dataset files because they fail close to the missing dependency:

```python
from albumentations.pytorch import ToTensorV2, ToTensor3D
```

If this import fails, fix the environment rather than replacing `ToTensorV2` with hand-written transposes unless the project intentionally avoids PyTorch.

## Hub Extra Behavior

Hub methods require `huggingface_hub`. When the package is missing, Hub helpers raise an `ImportError` with guidance to install either `huggingface_hub` or `albumentations[hub]`.

Use Hub support for sharing serialized augmentation configurations, not for ordinary in-process tensor conversion. Network access, credentials, and repository permissions are separate operational concerns; do not assume they are available in offline training jobs.

## Text Extra Behavior

Text transforms rely on Pillow font/image components. Missing Pillow can surface as an `ImportError` such as `ImageFont from PIL is required to use TextImage transform. Install it with pip install Pillow.` The `albumentations[text]` extra declares `pillow` for this surface.

Text transform selection and target semantics belong in `../transform-catalog/`; use this reference only for dependency and import troubleshooting.

## Safe Environment Checks

Use these checks in issue triage or CI smoke tests:

```python
import importlib.util
import albumentations as A

print("albumentations", A.__version__)
print("torch available", importlib.util.find_spec("torch") is not None)
print("ToTensorV2 exported", hasattr(A, "ToTensorV2"))
print("huggingface_hub available", importlib.util.find_spec("huggingface_hub") is not None)
print("Pillow available", importlib.util.find_spec("PIL") is not None)
```

If `torch available` is false, `ToTensorV2 exported` should also be false in a base install. If `torch available` is true but `ToTensorV2` is absent, check for a broken/incompatible `torch` installation or an import shadowing problem.
