---
name: runtime-and-custom-ops
description: "Set up and diagnose the legacy TensorFlow runtime and PointNet++
  custom operators used by Frustum PointNets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runtime and custom operators

Use this route for installation, version compatibility, TensorFlow graph-mode
imports, CUDA/toolkit decisions, and the custom operators used by the v2 model.
It is deliberately conservative: the repository is a Python-2/early-TensorFlow
release, not a modern pip package.

## Choose the runtime

1. Prefer an isolated legacy environment. The repository documents Python 2.7
   with TensorFlow 1.2/1.4, while the verified inspection baseline is Python
   3.7 with TensorFlow 1.15.5, NumPy 1.18.5, SciPy 1.4.1, OpenCV 4.5.5,
   Pillow 8.4.0, and protobuf 3.20.3.
2. For source-level KITTI geometry and v1 graph inspection, a CPU TensorFlow
   1.x environment is sufficient. It does not validate v2 custom ops.
3. For v2, training, or meaningful inference throughput, require a compatible
   CUDA TensorFlow build, compiler/toolkit, and all three compiled operators.
   A visible NVIDIA GPU is not proof that the old TensorFlow build can use it.
4. Run the bundled diagnostic before changing packages:
   `python scripts/check_legacy_runtime.py --json`.

Read [compatibility](references/compatibility.md) for version choices and
[custom operators](references/custom-ops.md) for build and load checks. Read
[troubleshooting](references/troubleshooting.md) whenever an import or loader
fails.

## Custom-op boundary

`models/pointnet_util.py` imports sampling, grouping, and 3D-interpolation
wrappers. Their Python modules call `tf.load_op_library` on local shared
objects, so v2 cannot be treated as a pure-Python CPU workflow. Build and test
operators in an isolated copy, discover TensorFlow's include/library paths
from the selected environment, and never paste machine-specific paths from an
old shell script into a reusable setup.

## Safe verification

Verify in this order: Python/TensorFlow import, graph-mode placeholder/session
smoke, framework device listing, compiler/toolkit visibility, one operator
load smoke, then the native op tests. Stop at the first failed gate. The
current generated skill has verified only the CPU graph smoke; CUDA and the
old custom-op ABI remain explicitly unverified. Route data preparation to
`../kitti-data-preparation/SKILL.md`, training to `../training/SKILL.md`, and
KITTI scoring to `../inference-and-evaluation/SKILL.md`.
