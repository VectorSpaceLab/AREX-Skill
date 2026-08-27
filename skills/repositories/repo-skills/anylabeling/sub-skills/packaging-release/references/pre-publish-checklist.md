# Pre-publish checklist

## Purpose

Use this checklist before tagging an AnyLabeling release or changing packaging, dependencies, startup imports, auto-labeling model loading, or export behavior. It distills the repository's CI and local release playbook into task-oriented checks.

## 1. Fresh environment install

Create a clean environment so pip resolves current dependency versions, not whatever was already installed locally.

```bash
VENV=${TMPDIR:-/tmp}/anylabeling-check
python -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install .
```

Watch for resolver failures, wheel build failures, and platform-specific PyQt issues. On macOS, install PyQt6 through Conda or another supported channel before testing because package metadata excludes PyQt6 on Darwin.

## 2. Unit tests

Run the full unittest suite:

```bash
QT_QPA_PLATFORM=offscreen "$VENV/bin/python" -m unittest discover -s tests -v
```

Expected result: all non-real-model unit tests pass. Real-inference tests are allowed to skip when model files are absent.

Good focused subsets when debugging packaging changes:

```bash
"$VENV/bin/python" -m unittest tests.test_label_colormap -v
"$VENV/bin/python" -m unittest tests.test_registry tests.test_types tests.test_lru_cache tests.test_model_manager -v
"$VENV/bin/python" -m unittest tests.test_sam3_auto_detection tests.test_sam3_onnx_unit tests.test_segment_anything_utils -v
QT_QPA_PLATFORM=offscreen "$VENV/bin/python" -m unittest tests.test_canvas_bounded_move -v
```

## 3. Startup import smoke

Run the exact import path users hit near startup:

```bash
QT_QPA_PLATFORM=offscreen "$VENV/bin/python" -c "
from anylabeling.views.labeling import label_widget
from anylabeling import app
print('startup imports OK')
"
```

This catches import-time failures such as Qt platform problems, generated resource import mismatches, or the `imgviz.label_colormap()` read-only-array regression.

## 4. Optional real-model inference

Real inference requires model files under the user's AnyLabeling model cache. Use it when changing ONNX runner code, model preprocessing, variant detection, model config fields, or prompt behavior. It is not normally part of the automated CI gate because the SAM3 model is large.

Representative model folders checked by the tests:

- `yolov8n-r20230415` for YOLOv8.
- `mobile_sam_20230629` for MobileSAM/SAM1.
- `sam2_hiera_tiny_20240803` for SAM2.
- `sam3_vit_h_20260220` for SAM3 text/geometric prompts.

Then run:

```bash
"$VENV/bin/python" -m unittest tests.test_real_inference -v
```

If model files are missing, the test classes should skip cleanly. For SAM3 text-prompt checks, use an image that actually contains the prompted object; otherwise tests may exercise the pipeline but fail semantic assertions.

## 5. Cross-Python matrix

For release readiness, repeat install and tests on every supported Python. The project CI uses Python 3.11, 3.12, and 3.13 on Linux, Windows, and macOS. A quick local Linux-only pass can use any Python manager available to the user:

```bash
for v in 3.11 3.12 3.13; do
  PY=$(command -v python$v || true)
  [ -n "$PY" ] || continue
  VENV=/tmp/anylabeling-py${v//./}
  rm -rf "$VENV"
  "$PY" -m venv "$VENV"
  "$VENV/bin/python" -m pip install --upgrade pip --quiet
  "$VENV/bin/python" -m pip install . --quiet
  QT_QPA_PLATFORM=offscreen "$VENV/bin/python" -m unittest discover -s tests -v
done
```

## 6. GPU wheel metadata check

When preparing a GPU package, verify the built wheel metadata instead of trusting a name in source code:

```bash
ls dist/
python -m zipfile -e dist/anylabeling_gpu-*.whl /tmp/anylabeling-gpu-wheel
python - <<'PY'
from pathlib import Path
meta = next(Path('/tmp/anylabeling-gpu-wheel').glob('anylabeling_gpu-*.dist-info/METADATA'))
text = meta.read_text()
for line in text.splitlines():
    if line.startswith(('Name:', 'Requires-Dist: onnxruntime')):
        print(line)
PY
```

Expected: package name is `anylabeling-gpu`, and `Requires-Dist` includes `onnxruntime-gpu` rather than the CPU `onnxruntime` dependency.

## 7. Resource and executable smoke

If translations, resources, PyInstaller specs, or runtime hooks changed:

1. Run `python scripts/check_language_tools.py` from this skill's helper copy to confirm resource tool availability.
2. Regenerate resources only in a maintainer environment.
3. Run the startup import smoke.
4. Build the executable or folder mode artifact on the target platform.
5. Launch the built executable in a clean environment and check for missing `onnxruntime` DLLs or Qt plugin errors.

## Stop conditions

Do not tag or publish if any of these remain unresolved:

- Fresh install cannot resolve dependencies.
- Startup import smoke fails.
- Unit tests fail outside explicitly documented optional real-model skips.
- GPU wheel metadata still says `anylabeling` or depends on CPU `onnxruntime`.
- Resource regeneration leaves `resources.py` importing PySide6 instead of PyQt6.
- PyInstaller artifact misses ORT native libraries or the runtime hook no longer runs before ORT import.
