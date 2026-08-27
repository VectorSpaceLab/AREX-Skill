---
name: imgclsmob
description: "Guide imgclsmob image-classification model selection, CPU
  inference, dataset-aware training and evaluation plans, checkpoint conversion,
  and bounded multi-framework compatibility workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# imgclsmob

Use this repo-specific skill when a task mentions `imgclsmob`, `gluoncv2`,
`pytorchcv`, MXNet/Gluon model providers, ImageNet/CIFAR/SVHN/CUB
classification workflows, checkpoint conversion, or the repository's
multi-framework training/evaluation conventions.

## Route by task

- **Model construction, one-batch prediction, preprocessing, checkpoints, or
  model statistics:** read [model-inference](sub-skills/model-inference/SKILL.md).
  Start with the bundled CPU/non-pretrained smoke scripts.
- **Dataset roots, metainfo, classification train/eval command plans, metrics,
  resume state, or batch/device settings:** read
  [training-evaluation](sub-skills/training-evaluation/SKILL.md). Run its
  filesystem-only preflight before constructing a real command.
- **Gluon/MXNet, PyTorch, TF1, TF2, Keras, Chainer, or TFLite checkpoint
  translation:** read [conversion](sub-skills/conversion/SKILL.md). Use its
  standard-library argument inspector before any backend or file operation.
- **TensorFlow 1/2, Tensorpack, Keras/Keras-MXNet, Chainer, or CUDA-specific
  compatibility:** read [framework-compatibility](sub-skills/framework-compatibility/SKILL.md).
  Treat these as bounded-unverified unless a matching backend is independently
  prepared and exercised.

Read [troubleshooting](references/troubleshooting.md) for cross-cutting import,
optional-dependency, checkpoint, data, CLI, and device failures. Read
[repo-provenance](references/repo-provenance.md) before deciding whether a
refresh is needed; the skill is anchored to one published repository snapshot.

## Verified core and safe defaults

The verified core is CPU MXNet/Gluon plus CPU PyTorch with the external
`pytorchcv` provider. The core smoke contract is: `pretrained=False`, no
network, one synthetic or local image, an NCHW `(1, 3, 224, 224)` input, and a
rank-2 classification output. Use `scripts/check_environment.py` to report
which optional imports are available; it never installs packages or downloads
weights.

Install only the packages needed by the selected route. For the verified CPU
core, use a NumPy version below 2 with MXNet 1.9.1, a CPU-capable MXNet build,
and compatible CPU PyTorch/torchvision wheels plus the external `pytorchcv`
package. Install `gluoncv2` at the snapshot version when using its public
provider. Do not install the repository's broad legacy requirements file
wholesale. Pretrained flags, absent CIFAR/SVHN caches, and publication helpers
may contact the network or write artifacts; keep them opt-in.

A successful CPU probe does **not** prove CUDA, TensorFlow, Keras, Chainer, or
legacy Tensorpack behavior. Do not use a visible GPU or a CPU wheel as backend
verification. The conversion sub-skill records the GPU-only native conversion
limits and the exact TF1/TF2 labels.

## Self-contained helper entry points

Run these from the generated skill directory or use their absolute path in an
agent's skill installation:

```bash
python scripts/check_environment.py --help
python scripts/check_environment.py
python sub-skills/model-inference/scripts/infer_gluon.py --help
python sub-skills/model-inference/scripts/infer_pytorch.py --help
python sub-skills/training-evaluation/scripts/check_dataset_layout.py --help
python sub-skills/training-evaluation/scripts/build_command.py --help
python sub-skills/conversion/scripts/inspect_conversion_args.py --list
```

The inference helpers default to random-weight CPU smoke tests. The dataset
checker performs no framework import or download. The command builder and
conversion inspector only validate/print plans; neither launches training or
conversion.
