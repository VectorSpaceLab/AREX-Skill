# Troubleshooting

## Purpose

Read this page when TensorLayer import, CLI, or optional workflow behavior fails.

## Common failures and fixes

### `import tensorlayer` fails with `ModuleNotFoundError: No module named 'matplotlib'`

**Why it happens:** The current TensorLayer package imports `tensorlayer.app` during top-level import, and the app helpers import `matplotlib`.

**Fix:** Install `matplotlib` and retry the import.

**Next check:** Run `scripts/check_import.py`.

---

### `python -m tensorlayer.cli --help` crashes when `CUDA_VISIBLE_DEVICES` is empty

**Symptom:** The CLI dies with a `ValueError` from `int('')`.

**Why it happens:** `tensorlayer.cli.train` splits `CUDA_VISIBLE_DEVICES` and assumes every token is a valid integer.

**Fix:** Unset `CUDA_VISIBLE_DEVICES` or leave it unset before running the CLI help command. Avoid setting it to an empty string.

**Next check:** Run `scripts/check_cli_help.py`.

---

### `ModuleNotFoundError` for `cloudpickle`, `scikit-image`, `opencv-python`, or `nltk`

**Why it happens:** The file, preprocessing, vision, and sentence-tokenization helpers depend on those packages.

**Fix:** Install the missing package(s) and rerun the corresponding smoke script.

**Next check:**
- `sub-skills/data-and-utilities/scripts/smoke_prepro.py`
- `sub-skills/vision-and-apps/scripts/smoke_vision_models.py`
- `sub-skills/text-and-sequence/scripts/smoke_text.py`

---

### `AttributeError: module 'numpy' has no attribute 'float'` or `np.math`

**Why it happens:** TensorLayer 2.2.4 and some native tests still use legacy NumPy aliases that newer NumPy releases removed or deprecated.

**Fix:** Prefer a TensorFlow-compatible NumPy 1.x stack when possible. If you must run legacy native tests on a newer stack, add a tiny compatibility shim before import time, for example `import numpy as np, math; np.float = float; np.math = math`.

**Next check:** rerun the failing layer/model smoke or the selected native pytest case.

---

### Save/load errors for `.h5`, `.npz`, or `.npz_dict`

**Why it happens:** The save/load format does not match the API call, or the model state was modified between save and load in a way that changes the graph.

**Fix:** Use the same format on save and load, and follow the tiny roundtrip in `sub-skills/core-modeling/scripts/smoke_model.py`.

**Next check:** run `sub-skills/core-modeling/scripts/smoke_model.py` and prefer a tiny deterministic round-trip before expanding to graph serialization.

---

### Pretrained image examples fail because weights or data are missing

**Why it happens:** The app/tutorial scripts expect external weights, class-name files, or dataset files that are not bundled with the package.

**Fix:** Use `pretrained=False` for constructor smoke checks, or provide the missing model/data files explicitly.

**Next check:** `sub-skills/vision-and-apps/scripts/smoke_vision_models.py`.

---

### GPU or CUDA warnings appear during import

**Why it happens:** TensorFlow probes the GPU stack even when you only want CPU workflows.

**Fix:** CPU workflows are still valid if the import and tiny model smoke pass. Install a CUDA-capable TensorFlow stack only when you need the accelerator path.

**Next check:** use the relevant sub-skill reference for optional GPU notes.

---

### Training or distributed examples appear to hang

**Why it happens:** Some examples block on stdin, expect datasets, or assume Horovod/OpenMPI/Gym extras.

**Fix:** Use the bundled tiny smoke scripts first. Treat the long examples as reference workflows unless you intentionally want the full environment.

**Next check:** `sub-skills/training-and-cli/scripts/smoke_fit.py`.
