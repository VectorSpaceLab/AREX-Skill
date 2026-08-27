# pytorch-semseg compatibility notes

Read this when choosing a runtime environment or explaining why a workflow that matched the original README behaves differently on a modern Python stack.

## Package shape

The inspected checkout exposes the import package `ptsemseg` but does not include `setup.py` or `pyproject.toml`. If a future task needs the repository source rather than an already packaged release, make the `ptsemseg` package importable from a cloned or unpacked source tree, then run the bundled checks in this skill. Do not assume an editable install works for this snapshot.

A minimal import check is:

```bash
python - <<'PY'
from ptsemseg.models import get_model
from ptsemseg.loader import get_loader
print(get_model)
print(get_loader('pascal'))
PY
```

Use `scripts/check_environment.py` for a repeatable version of this check.

## Legacy requirements versus modern inspection

The README-era requirements pin old packages such as:

- `torch==0.4.1`
- `torchvision==0.2.0`
- `scipy==0.19.0`
- `matplotlib==2.0.0`
- `tensorboardX`
- optional `pydensecrf`

Those exact versions are often incompatible with modern Python versions and current CUDA stacks. For new investigation, choose between:

1. **Legacy reproduction environment**: use an older Python and the pinned requirements when the goal is to reproduce historical behavior exactly.
2. **Modern inspection/adaptation environment**: use a supported modern PyTorch stack to inspect APIs and adapt scripts, while explicitly checking for deprecations and behavior changes.

Do not claim exact paper-era reproduction from a modern environment unless the target model, data, checkpoints, and library versions were actually verified.

## Known compatibility hazards

| Surface | Symptom | Cause | Recovery |
| --- | --- | --- | --- |
| Generated Caffe protobuf file | `TypeError: Descriptors cannot be created directly` when importing `ptsemseg.models` | `ptsemseg/caffe_pb2.py` was generated for older protobuf APIs. | Install `protobuf<3.21`, regenerate the protobuf with a modern `protoc`, or set `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` as a slower workaround. |
| `test.py` image I/O | `AttributeError: scipy.misc has no attribute imread/imresize/imsave/toimage` | Modern SciPy removed legacy image helpers used by the original script. | Use a legacy SciPy/Pillow environment or adapt the image I/O to `PIL.Image`/`imageio` before real inference. The bundled inference helper only builds commands and warnings. |
| FCN/SegNet model smoke | Network/cache access for VGG weights | `get_model` calls `torchvision.models.vgg16(pretrained=True)` for FCN and SegNet variants. | Use FRRN/UNet/LinkNet for no-download API smokes, or pre-cache/allow weights before testing FCN/SegNet. |
| PyYAML config loading | `yaml.load()` requires a Loader argument | The original scripts use legacy `yaml.load(fp)` style. | Patch adapted scripts to `yaml.safe_load(fp)` or use a PyYAML version compatible with the original code. Bundled validators use `safe_load`. |
| CUDA expectations | Code runs on CPU unexpectedly or `DataParallel` behavior differs | The scripts choose `cuda` only when PyTorch reports CUDA available; model/data sizes may still be too large. | Run `scripts/check_environment.py` and review GPU memory, `torch.version.cuda`, and `torch.cuda.is_available()` before a long run. |
| Optional DenseCRF | `Failed to import pydensecrf` or `--dcrf` has no effect | `pydensecrf` is optional and may need compilation. | Install and verify `pydensecrf` only for DenseCRF post-processing tasks; normal single-image inference can run with `--no-dcrf`. |

## Backend policy

The repository's main workflows are PyTorch workflows. CPU can verify imports, parser behavior, static config validation, registry listings, metrics, and a small no-download FRRN smoke. CUDA is optional for speed and realistic large-image training/inference, not a required backend for using this skill.

If a user asks for performance, multi-GPU behavior, or full training/evaluation, verify CUDA separately in the target environment and do not substitute a CPU import check for GPU performance evidence.
