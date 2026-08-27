# Runtime checks

Run runtime checks before expensive training, demos, or export.

## Main smoke check

From the generated skill directory:

```bash
python scripts/check_install.py --cuda-ops
```

The script checks:

1. PyTorch import, CUDA availability, and visible devices.
2. Detectron2 import.
3. AdelaiDet import and version surface.
4. `adet.config.get_cfg()` and key config sections.
5. Detectron2 registry side effects after importing AdelaiDet modeling.
6. `adet._C` extension symbols.
7. Optional tiny CUDA BezierAlign, DefROIAlign, and `_C.ml_nms` calls.

Use `python scripts/check_install.py` without `--cuda-ops` only for CPU/import-only analysis.

## CLI help checks

After the base smoke check, verify public script imports/parsers:

```bash
python /path/to/AdelaiDet/tools/train_net.py --help
python /path/to/AdelaiDet/demo/demo.py --help
python /path/to/AdelaiDet/tools/visualize_data.py --help
python /path/to/AdelaiDet/onnx/export_model_to_onnx.py --help
```

Equivalent skill-owned wrappers also support `--help` and `--dry-run`.

## What failures mean

| Failed check | Meaning | Next route |
| --- | --- | --- |
| PyTorch/CUDA unavailable | Wrong PyTorch build, hidden GPUs, driver mismatch, or CPU-only task. | Stay in `setup-build`. |
| Detectron2 import fails | Wheel/ABI mismatch or Pillow dependency issue. | Stay in `setup-build`. |
| `import adet` fails | Usually missing OpenCV, Pillow/rapidfuzz issue, or extension load error. | Stay in `setup-build`. |
| Config keys missing | AdelaiDet config defaults were not added, or wrong package imported. | Stay in `setup-build`; inspect `adet.config`. |
| Registry names missing | AdelaiDet modeling modules did not import/register. | Stay in `setup-build`; inspect import traceback. |
| `adet._C` missing symbols | Editable build did not compile the extension. | Rebuild from setup recipe. |
| BezierAlign/DefROIAlign/ml_nms fails | CUDA extension/runtime mismatch or CPU-only build. | Fix before training/inference requiring those ops. |
| CLI help fails | Missing dependency or import-time model/data issue. | Use the error message to route to setup, text, data, or export. |

## Minimum success bar by task

- **Config reading only:** `python scripts/check_install.py` must pass.
- **Training/evaluation/demo on GPU:** `python scripts/check_install.py --cuda-ops` must pass, then wrapper dry-run.
- **Text spotting:** `--cuda-ops` plus rapidfuzz `<3` and text dataset files.
- **ONNX export:** base smoke plus export wrapper dry-run; optional runtime validation depends on extra packages.
