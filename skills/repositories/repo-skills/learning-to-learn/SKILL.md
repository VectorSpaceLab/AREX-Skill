---
name: learning-to-learn
description: "Routes TensorFlow 1.x learning-to-learn meta-optimizer,
  optimizer-network, problem-factory, training, and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# learning-to-learn

Use this repo skill when a task is about Google's TensorFlow implementation of **Learning to Learn by Gradient Descent by Gradient Descent**: learned optimizers, optimizer RNNs, built-in optimizee problems, or the training/evaluation scripts.

## Before doing runtime work

This is a legacy TensorFlow 1.x / Sonnet 1.x repository with root-level Python modules, not an installable package. For runtime checks, use a checkout/source tree that contains the root modules and a compatible Python environment.

Minimal dependency surface:

```bash
python -m pip install "tensorflow==1.15.*" "dm-sonnet==1.*" dill mock nose-parameterized "protobuf<3.20"
```

Minimal source-tree import check:

```bash
python -c "import tensorflow as tf, sonnet; import meta, networks, problems, preprocess, util; print(tf.__version__)"
```

If TensorFlow 2.x is installed or `tensorflow.contrib` is missing, stop and switch to a TensorFlow 1.x-compatible environment before debugging repo code.

## Route by task

| Task intent | Read |
| --- | --- |
| Build or debug `MetaOptimizer`, `meta_loss`, `meta_minimize`, returned ops, variable interception, `net_assignments`, second derivatives, or `.l2l` save/load | [`sub-skills/meta-optimizer-api/SKILL.md`](sub-skills/meta-optimizer-api/SKILL.md) |
| Choose/configure optimizer networks such as `CoordinateWiseDeepLSTM`, `KernelDeepLSTM`, `Sgd`, `Adam`, initializers, preprocessing, or network serialization | [`sub-skills/optimizer-networks/SKILL.md`](sub-skills/optimizer-networks/SKILL.md) |
| Choose built-in problems, inspect `util.get_config`, handle MNIST/CIFAR data side effects, or author custom optimizee loss factories | [`sub-skills/problem-factories/SKILL.md`](sub-skills/problem-factories/SKILL.md) |
| Run or adapt training/evaluation command workflows, tiny CPU smokes, saved optimizer directories, Adam-vs-L2L evaluation, or CLI flag behavior | [`sub-skills/training-evaluation/SKILL.md`](sub-skills/training-evaluation/SKILL.md) |

## Shared references and helpers

- [Overview](references/overview.md) maps the repository architecture and how modules cooperate.
- [Troubleshooting](references/troubleshooting.md) covers cross-cutting install/import, TensorFlow/Sonnet, data, and source-tree issues.
- [Repository provenance](references/repo-provenance.md) records the source snapshot used to create this skill.
- [Environment checker](scripts/check_l2l_environment.py) validates imports and optionally performs a tiny source-module graph smoke against a local checkout.

## Operating rules

1. Keep `make_loss` functions side-effect-light; perform dataset downloads, queue setup, and other Python side effects outside the function passed to `MetaOptimizer` when possible.
2. Treat `simple`, `simple-multi`, and `quadratic` as the safe CPU problem family for smoke checks.
3. Treat `mnist`, `cifar`, and `cifar-multi` as data-backed workflows that may download/cache data or create queues.
4. Use bundled helper scripts to generate/validate commands instead of relying on memory for flags or paths.
5. Do not assume a `.l2l` file is a TensorFlow checkpoint; it is a pickle payload loaded by `networks.factory(..., net_path=...)`.
