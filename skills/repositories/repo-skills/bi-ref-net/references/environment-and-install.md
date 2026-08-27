# Environment and Install

Read this before installing dependencies, choosing a backend, or deciding whether a BiRefNet task can run in the current environment.

## Installation shape

BiRefNet is a source-code-first repository. It has `requirements.txt` but no packaging metadata such as `pyproject.toml`, `setup.py`, or console entry points. For source workflows, install dependencies and put the user's BiRefNet checkout on `PYTHONPATH` or run from the checkout root. Bundled helper scripts accept `--repo-root` when they need source modules.

Documented setup:

```bash
conda create -n birefnet python=3.11 -y
conda run -n birefnet python -m pip install -r requirements.txt
```

For a non-conda environment, use Python 3.11 and install the same requirements file. Keep PyTorch backend selection explicit.

## Base dependencies

`requirements.txt` declares:

- `torch>=2.5.0`, `torchvision`
- `numpy<2`, `opencv-python`
- `timm`, `scipy`, `scikit-image`, `kornia`, `einops`
- `tqdm`, `prettytable`, `tabulate`, `ipykernel`
- `huggingface-hub>0.25`, `accelerate`

The README's one-line `AutoModelForImageSegmentation.from_pretrained(..., trust_remote_code=True)` path also needs `transformers`; install it only when that Hugging Face Transformers API is required.

ONNX conversion is optional and needs extra packages such as `onnx`, `onnxscript`, and `onnxruntime-gpu` plus the deformable-convolution exporter workaround described in `sub-skills/model-architecture/references/onnx-and-export-notes.md`.

## Safe checks

Dependency-only check:

```bash
python scripts/check_birefnet_environment.py
```

Source-module check for a checkout:

```bash
python scripts/check_birefnet_environment.py --repo-root /path/to/BiRefNet --check-source
```

Optional model construction check without pretrained backbone downloads:

```bash
python scripts/check_birefnet_environment.py --repo-root /path/to/BiRefNet --check-source --construct-model
```

## Backend expectations

| Workflow | CPU enough? | CUDA/GPU expectation |
|---|---|---|
| Import/dependency checks | Yes | Not required |
| Config and dataset validation | Yes | Not required |
| `image2patches` / `patches2image` helpers | Yes | Not required |
| CPU `refine_foreground` smoke | Yes | Not required |
| Full image/video inference at 1024+ resolution | Partial | Recommended/expected for practical speed and memory |
| GPU foreground refinement | No for GPU path | Requires CUDA-enabled PyTorch and a visible NVIDIA GPU |
| DDP/Accelerate training | No for intended workflow | Requires CUDA, datasets, backbone weights, and high VRAM |
| ONNX conversion for default Swin-L model | Partial | README notes high memory demand; GPU is normally expected |

The current generated skill verified only CPU/any checks during construction. Do not report CUDA workflows as verified unless you run fresh checks in the user's target environment.

## Memory and asset notes

- README reports inference at `1024x1024` needing about 5.5GB GPU memory for the standard model.
- README reports single-GPU training needing roughly 36.5GB+ GPU memory, with original large runs using multiple high-memory GPUs.
- ONNX conversion of the standard model was noted as needing about 19.7GB GPU memory; a lightweight backbone is more suitable for constrained environments.
- Full training/evaluation requires external dataset trees under the configured data root and backbone/model weights under the configured weights root.

## Import patterns

Source-code model path:

```python
from models.birefnet import BiRefNet
model = BiRefNet(bb_pretrained=False)
```

Hugging Face hub-mixin path from the source class:

```python
from models.birefnet import BiRefNet
model = BiRefNet.from_pretrained("ZhengPeng7/BiRefNet")
```

Transformers AutoModel path from the README:

```python
from transformers import AutoModelForImageSegmentation
model = AutoModelForImageSegmentation.from_pretrained(
    "zhengpeng7/BiRefNet",
    trust_remote_code=True,
)
```

Use the source-class path when you need to edit local `config.py`, load local `.pth` weights, or inspect architecture internals. Use the Transformers path when you only need the published remote-code model and have the required package installed.
