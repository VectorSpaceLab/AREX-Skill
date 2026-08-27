# Test Selection

Use the smallest command that exercises the changed surface. The repository already supports focused pytest selection, non-marked default runs, marker-gated heavy checks, and Makefile wrappers.

## Default Commands

- Install test dependencies for development: `make install_dev`.
- Fast broad suite: `make test` or `pytest -v -rsx -n 2 tests/ --non-marked-only`.
- Full marker and slow sweep: `make test_all` or `RUN_SLOW=1 pytest -v -rsx -n 2 tests/`.
- Lint and format: `make fixup`, or `ruff check --fix` followed by `ruff format`.
- Build docs from `docs/`: `make html`.
- Generate ported encoder table: `make table`.
- Generate timm encoder table: `make table_timm`.

## Marker Policy

`tests/conftest.py` adds `--non-marked-only`, which keeps only tests without direct markers. The declared markers are:

- `logits_match`: slow or pretrained checkpoint comparisons; usually needs `RUN_SLOW=1` and may download Hugging Face fixtures.
- `compile`: `torch.compile` compatibility checks; can be slower and PyTorch-version sensitive.
- `torch_export`: `torch.export.export` compatibility checks; encoder export tests require sufficiently new PyTorch.
- `torch_script`: TorchScript compatibility checks; useful for signature/control-flow changes.

Prefer non-marked tests first. Add marker-specific commands only when constructor signatures, control flow, feature shapes, model flags, or serialization/export behavior changed.

## Focus Matrix

| Changed paths | First focused command | Follow-up commands |
| --- | --- | --- |
| `segmentation_models_pytorch/decoders/unet/` | `pytest -q tests/models/test_unet.py --non-marked-only` | `pytest -q tests/models/test_unet.py -m "compile or torch_export or torch_script"` if compatibility flags or control flow changed |
| `segmentation_models_pytorch/decoders/unetplusplus/` | `pytest -q tests/models/test_unetplusplus.py --non-marked-only` | Add marker tests for script/export/compile-sensitive changes |
| `segmentation_models_pytorch/decoders/manet/` | `pytest -q tests/models/test_manet.py --non-marked-only` | Add interpolation or marker tests when decoder blocks changed |
| `segmentation_models_pytorch/decoders/linknet/` | `pytest -q tests/models/test_linknet.py --non-marked-only` | Include transformer-style encoder test if encoder interface changed |
| `segmentation_models_pytorch/decoders/fpn/` | `pytest -q tests/models/test_fpn.py --non-marked-only` | Add marker tests for compile/export/script-sensitive changes |
| `segmentation_models_pytorch/decoders/pspnet/` | `pytest -q tests/models/test_psp.py --non-marked-only` | Add marker tests for shared model behavior changes |
| `segmentation_models_pytorch/decoders/deeplabv3/` | `pytest -q tests/models/test_deeplab.py --non-marked-only` | Add dilation/output-stride checks and marker tests as needed |
| `segmentation_models_pytorch/decoders/pan/` | `pytest -q tests/models/test_pan.py --non-marked-only` | Add interpolation/deprecation checks when upsampling arguments change |
| `segmentation_models_pytorch/decoders/upernet/` | `pytest -q tests/models/test_upernet.py --non-marked-only` | `pytest -q tests/models/test_upernet.py -m torch_export` for export tolerance changes |
| `segmentation_models_pytorch/decoders/segformer/` | `pytest -q tests/models/test_segformer.py --non-marked-only` | Avoid `logits_match` unless pretrained checkpoint behavior is the task |
| `segmentation_models_pytorch/decoders/dpt/` | `pytest -q tests/models/test_dpt.py --non-marked-only` | Avoid `logits_match` unless pretrained DPT checkpoint behavior is the task |
| `segmentation_models_pytorch/base/` | `pytest -q tests/base tests/test_base.py tests/models --non-marked-only` | Add selected model marker tests if forward/export/script paths changed |
| `segmentation_models_pytorch/encoders/resnet.py`, `densenet.py`, `mobilenet.py`, `vgg.py` | `pytest -q tests/encoders/test_torchvision_encoders.py --non-marked-only` | Add marker tests for compile/export/script flags |
| `segmentation_models_pytorch/encoders/dpn.py`, `inception*.py`, `senet.py`, `xception.py` | `pytest -q tests/encoders/test_pretrainedmodels_encoders.py --non-marked-only` | Add marker tests if encoder feature or script behavior changed |
| `segmentation_models_pytorch/encoders/efficientnet.py`, `mix_transformer.py`, `mobileone.py` | `pytest -q tests/encoders/test_smp_encoders.py --non-marked-only` | Add `RUN_ALL_ENCODERS=1` only for explicit broad encoder sweeps |
| `segmentation_models_pytorch/encoders/timm_*.py` | `pytest -q tests/encoders/test_timm_ported_encoders.py tests/encoders/test_timm_universal.py tests/encoders/test_timm_vit_encoders.py --non-marked-only` | Add timm table generation or marker tests only for compatibility/table tasks |
| `segmentation_models_pytorch/encoders/_preprocessing.py` or preprocessing metadata | `pytest -q tests/test_preprocessing.py --non-marked-only` | Add matching encoder group tests if registry metadata changed |
| `segmentation_models_pytorch/losses/` | `pytest -q tests/test_losses.py --non-marked-only` | Add numerical regression cases for each mode/logits path touched |
| `segmentation_models_pytorch/metrics/` | `pytest -q tests/test_losses.py --non-marked-only` when shared functional math changed | Add or create metric-specific tests if metrics behavior is newly covered |
| `docs/*.rst` only | `cd docs && make html` | Run source tests only if docs examples import changed APIs |
| `README.md`, `pyproject.toml`, `Makefile` | `make test` or the affected command directly | Use docs/test extras depending on changed metadata |

## Helper Script

`../scripts/list_changed_test_focus.py` accepts changed path arguments and prints JSON with suggested commands. It does not inspect git, detect branches, mutate files, import SMP, or run tests.

Examples:

```bash
python sub-skills/repo-development/scripts/list_changed_test_focus.py segmentation_models_pytorch/decoders/unet/model.py docs/models.rst
python sub-skills/repo-development/scripts/list_changed_test_focus.py --pretty segmentation_models_pytorch/encoders/resnet.py
```

## Slow and Network-Sensitive Tests

- Slow tests are wrapped by `tests.utils.slow_test` and run only when `RUN_SLOW` is truthy.
- `logits_match` tests download or compare saved checkpoint fixtures and should be treated as heavyweight.
- Some tests choose GPU if available through `tests.utils.default_device`; failures can differ by device, PyTorch version, or CUDA availability.
- `tests.utils.check_run_test_on_diff_or_main` may skip marker tests on non-main branches when diff patterns do not match. Set `RUN_ALL=1` only when intentionally forcing those tests.
- `RUN_ALL_ENCODERS=1` expands encoder parameterization and can make encoder suites much larger.
