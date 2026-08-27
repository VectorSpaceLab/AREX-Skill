# FastReID setup and configuration troubleshooting

## 1) Source-only install or import fails

**Symptom**: `pip install -e` or a distribution lookup fails, or `import fastreid`
does not work from a fresh shell.

**Cause**: this repository is source-only and does not ship `setup.py` or
`pyproject.toml`.

**Fix**:

- add the checkout root to `PYTHONPATH`
- or add a private `.pth` file that points at the checkout root
- or use a helper script that inserts the repo root into `sys.path`

Do not expect editable distribution metadata to exist.

## 2) Python 3.10+ `collections.Mapping` import error

**Symptom**: `ImportError: cannot import name 'Mapping' from 'collections'`.

**Cause**: this FastReID source tree still uses a Python import pattern that is
compatible with Python 3.9 but breaks on Python 3.10+ without patching.

**Fix**:

- use Python 3.9 for inspection and config work
- or patch the import sites before attempting a newer interpreter

For a generated skill, prefer the compatibility-safe Python 3.9 path.

## 3) Missing core dependencies

**Symptom**: import or config checks fail because `yacs`, `torch`, `torchvision`,
`pyyaml`, `scipy`, `scikit-learn`, `opencv-python-headless`, `tabulate`,
`termcolor`, `prettytable`, `easydict`, `tensorboard`, `gdown`, or `faiss-cpu`
are missing.

**Cause**: the inspection environment does not yet contain the minimum runtime
set.

**Fix**: install only the packages required for the selected setup and retry the
import/config smoke check. Do not add optional GPU, Caffe, or TensorRT stacks
when you only need setup and configuration behavior.

## 4) Unsafe YAML loading error

**Symptom**: a config file raises a YAML constructor or unsafe loading error.

**Cause**: the file uses YAML tags that require unsafe loading.

**Fix**:

- keep the default safe loading path for ordinary config inspection
- only opt in to unsafe loading for a trusted file that you have already
  reviewed

Never treat unsafe loading as the default.

## 5) Malformed `opts`

**Symptom**: config merge fails after command-line overrides are applied.

**Cause**: the override list has an odd number of tokens, uses the wrong dotted
key, or has a value with spaces that was not quoted.

**Fix**:

- pass overrides as `KEY VALUE` pairs
- quote values that contain spaces
- use a valid dotted key from the config tree
- prefer the merge checker to catch mistakes before a training or evaluation run

## 6) Missing weights or pretrained backbone files

**Symptom**: the config loads, but a later step asks for a checkpoint or a
pretrained backbone file that is not present.

**Cause**: the recipe expects a local `MODEL.WEIGHTS` file or a cached pretrained
backbone path, but the machine is offline or the cache is empty.

**Fix**:

- point `MODEL.WEIGHTS` at a local checkpoint
- point `MODEL.BACKBONE.PRETRAIN_PATH` at a local pretrained backbone file
- or populate the standard torch checkpoint cache when downloads are allowed

Do not confuse a missing weight file with a config merge problem.

## 7) CPU dry-run still pulls CUDA-style defaults

**Symptom**: a merged config still points at GPU behavior when you wanted a CPU
inspection.

**Cause**: the recipe defaults `MODEL.DEVICE` to `cuda`.

**Fix**:

- override `MODEL.DEVICE` to `cpu`
- reduce `SOLVER.IMS_PER_BATCH` and `TEST.IMS_PER_BATCH` if the inspection
  machine is small
- inspect the merged result with the helper script before any heavier workflow

## 8) Legacy demo import mismatch

**Symptom**: a demo or visualization help check fails with an error similar to
`cannot import name 'evaluate_rank'`.

**Cause**: this checkout exposes that symbol from `fastreid.evaluation.rank`,
not from the top-level `fastreid.evaluation` import path.

**Fix**: treat it as a source mismatch and use the correct module path in the
generated guidance.

## 9) Rank evaluation is slower than expected

**Symptom**: evaluation works, but ranking is slower than desired.

**Cause**: the optional Cython acceleration is not compiled.

**Fix**:

- accept the Python fallback when you only need inspection
- compile the optional rank extension only if the target workflow truly needs
  the speedup

## 10) `faiss`-related import gaps

**Symptom**: retrieval or distance utilities complain about missing `faiss`.

**Cause**: the CPU inspection environment does not have the optional `faiss-cpu`
package.

**Fix**: install the CPU build only when the selected workflow needs the Faiss
path. Do not install GPU-specific variants for a setup-only task.
