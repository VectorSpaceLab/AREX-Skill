---
name: pocket-flow
description: "Use PocketFlow for TensorFlow 1.x model compression, learner
  selection, custom model/data integration, execution setup, and deployment
  conversion workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PocketFlow Repo Skill

Use this skill when the user asks about PocketFlow, Tencent's TensorFlow 1.x framework for compressing and accelerating computer-vision models with pruning, sparsification, quantization, distillation, and automated hyperparameter search.

## Start here

1. Confirm the user is operating a PocketFlow-compatible source checkout or wants conceptual guidance for one. PocketFlow is a Python 3.6 / TensorFlow 1.x-era, checkout-style project rather than a modern packaged CLI.
2. Public setup baseline: create or activate a Python 3.6-compatible environment, then install the checkout's requirements from the repository root:

   ```bash
   python -m pip install -r requirement.txt
   ```

   Expose the checkout root on `PYTHONPATH` if running modules directly. PocketFlow has no `pip install pocketflow` package metadata in this snapshot.
3. Minimal verification command before any training or conversion work:

   ```bash
   python - <<'PY'
   import tensorflow as tf
   print(tf.__version__)
   assert tf.__version__.startswith('1.')
   from tensorflow.contrib.lite.python import lite_constants
   print('tf.contrib.lite ok')
   PY
   ```

4. For a non-mutating checkout scan, run the bundled helper from this skill: `python scripts/check_pocketflow_skill.py --repo-root <pocketflow-checkout> --check-tensorflow`.
5. Decide which route below owns the task. Do not start downloads, long training, Docker, Seven cluster jobs, or model conversion until the user explicitly approves the required data, hardware, credentials, and side effects.

## Route map

| User request | Read |
| --- | --- |
| Install/import check, `path.conf`, local/docker/seven modes, command preview, GPU discovery, Horovod/TF-Plus, AutoML text adapters | [execution-config](sub-skills/execution-config/SKILL.md) |
| Pick a learner, set pruning/sparsification/quantization/distillation/RL flags, understand algorithm trade-offs | [compression-learners](sub-skills/compression-learners/SKILL.md) |
| Add a custom dataset/model helper/run script, understand built-in CIFAR/ImageNet/Pascal VOC/Fashion-MNIST data contracts | [custom-models-data](sub-skills/custom-models-data/SKILL.md) |
| Export checkpoints to PB/TFLite, validate conversion artifacts, troubleshoot quantized/channel-pruned export, mobile deployment, inference timing | [deployment-conversion](sub-skills/deployment-conversion/SKILL.md) |
| Check whether this skill matches a checkout, source commit, or supported evidence | [repo provenance](references/repo-provenance.md) |
| Cross-cutting architecture and capability overview | [overview](references/overview.md) |
| Cross-cutting failures involving TF1, optional GPU/multi-GPU, source checkout style, data/model downloads, or stale docs | [troubleshooting](references/troubleshooting.md) |

## PocketFlow capability map

- Learners: full precision, channel pruning, remastered/GPU channel pruning, discrimination-aware channel pruning, weight sparsification, uniform quantization, TensorFlow quantization-aware training, non-uniform quantization.
- Data/model contracts: `AbstractDataset`, `AbstractModelHelper`, built-in CIFAR-10/ImageNet/Pascal VOC helpers, and a Fashion-MNIST-style custom example pattern.
- Execution modes: local, Docker, and Tencent Seven cluster, all mediated by `path.conf` and TensorFlow flags.
- Deployment: checkpoint-to-PB/TFLite export, channel-pruned graph transformation, quantized export, graph collection editing, inference timing, and mobile handoff notes.
- Automation: learner-internal DDPG search and a small AutoML text bridge for weight-sparsification hparams/results.

## Bundled root helper

Use [check_pocketflow_skill.py](scripts/check_pocketflow_skill.py) to statically inspect a PocketFlow checkout and optionally test TensorFlow 1.x imports. Sub-skill helpers provide deeper config, command, learner, skeleton, and conversion checks.

## Safety boundaries

- Treat full training/evaluation as long-running and data/model dependent.
- Treat official local launcher behavior as GPU-oriented because it uses `nvidia-smi` for idle GPU selection.
- Treat Docker, Seven, HDFS, pretrained model downloads, and Android app work as environment-specific and approval-gated.
- Do not assume TensorFlow 2 compatibility.
- Do not claim performance or hardware verification unless the actual data, checkpoint, and backend were run in the user's task environment.
