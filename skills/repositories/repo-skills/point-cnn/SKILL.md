---
name: point-cnn
description: "Use the legacy PointCNN TensorFlow 1.x repository to build X-Conv
  models, prepare point-cloud datasets, train classification or segmentation
  workflows, and validate evaluation artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PointCNN

Use this skill for the public `yangyanli/PointCNN` codebase: legacy TensorFlow
1.x point-cloud classification and segmentation built around X-Conv/X-DeConv.
This is a versioned operating guide, not a copy of the source checkout. Read
[provenance](references/repo-provenance.md) before deciding whether a different
checkout is still covered.

## First route

- **Model internals, X-Conv/X-DeConv, pointfly, or custom operators:** read
  [core-xconv-and-operators](sub-skills/core-xconv-and-operators/SKILL.md).
- **ModelNet40, ScanNet object, TU-Berlin, Quick Draw, MNIST, or CIFAR-10
  classification:** read
  [classification-workflows](sub-skills/classification-workflows/SKILL.md).
- **ShapeNet Parts, S3DIS, ScanNet, or Semantic3D segmentation:** read
  [segmentation-workflows](sub-skills/segmentation-workflows/SKILL.md).
- **Dataset download/conversion boundaries, HDF5/file lists, labels, or PLY
  contracts:** read [data-preparation](sub-skills/data-preparation/SKILL.md).
- **Prediction files, confidence merges, IoU/accuracy, or TensorBoard/checkpoint
  artifacts:** read
  [evaluation-and-artifacts](sub-skills/evaluation-and-artifacts/SKILL.md).

For a task that crosses routes, prepare and validate data first, select a
model/setting second, run a bounded workflow third, and inspect/merge artifacts
last. Keep the owning sub-skill in control of its detailed contract.

## Compatibility gate

This repository uses TensorFlow 1.x graph-mode APIs (`tf.contrib`, `tf.layers`,
placeholders, sessions, and `tf.py_func`). Start with the bundled read-only
probe:

```bash
python scripts/check_environment.py --help
python scripts/check_environment.py
```

Use a deliberately isolated legacy environment and the public dependencies
listed in the repository's requirements, adapting versions to the target
platform. Do not assume that a current TensorFlow release or eager execution
will work. Classification requires a functioning TensorFlow 1.x graph stack.

Every supplied segmentation setting uses `sampling = 'fps'`. FPS,
`GatherPoint`, and related operators are registered only for a CUDA GPU and
must be built against a compatible TensorFlow framework ABI, CUDA toolkit, C++
toolchain, driver, and visible GPU. A CPU import, CPU graph build, or successful
HDF5 validation is **not** segmentation verification. Read the FPS diagnostics
and keep the required backend result visible; do not silently replace it with a
CPU fallback.

## Safe operating boundaries

Use explicit input and output paths. Historical shell launchers may background
jobs or assume repository-relative directories; adapt them to foreground
commands and disposable output roots. Do not make dataset downloads,
archive extraction, full conversions, Semantic3D acquisition/decompression,
long training, or benchmark runs part of a smoke check. Validate a tiny fixture
or CLI help first, and record checkpoint/setting/data provenance before treating
any metric as meaningful.

Cross-cutting symptoms and recovery order are in
[troubleshooting](references/troubleshooting.md). The generated skill is not
imported or synchronized to another agent by this creation run.
