---
name: tensorpack
description: "Use Tensorpack, a TF1-compatible TensorFlow training interface
  with DataFlow, trainers, callbacks, prediction, checkpoints, export, and
  example workflow guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tensorpack repo skill

Use this repo skill when a task names Tensorpack or clearly needs its graph-mode
TensorFlow training interface, pure-Python DataFlow pipeline, callbacks,
checkpoint utilities, model export, or documented example workflow patterns.
Tensorpack is TF1-oriented: even under a TensorFlow 2 package, guide users toward
`tensorpack.tfv1` / `tf.compat.v1` graph code and explicit eager-mode handling.

## Start here

1. Read [`references/repo-overview.md`](references/repo-overview.md) for the
   package topology, dependency tiers, TensorFlow compatibility, and public
   module map.
2. Read [`references/repo-provenance.md`](references/repo-provenance.md) before
   deciding whether this skill is current for another checkout.
3. Use [`scripts/check_tensorpack_env.py`](scripts/check_tensorpack_env.py) for a
   safe import and optional-dependency diagnostic.
4. If the task names a source example family or paper/model recipe, read
   [`references/examples-catalog.md`](references/examples-catalog.md) and then
   route to the owning sub-skill.
5. If the user reports an install/import/backend/data failure before you know
   the owning workflow, read [`references/troubleshooting.md`](references/troubleshooting.md).

## Route by task

| User intent or signal | Read |
| --- | --- |
| Data loading, augmentation, serializers, dataset loaders, `DataFlow`, `QueueInput`, input queue speed, `MultiProcessRunnerZMQ`, `LMDBSerializer`, `imgaug` | [`sub-skills/dataflow/SKILL.md`](sub-skills/dataflow/SKILL.md) |
| Model definitions, `ModelDesc`, `TrainConfig`, trainers, callbacks, summaries, symbolic layers, multi-GPU/distributed training, training example recipes | [`sub-skills/training/SKILL.md`](sub-skills/training/SKILL.md) |
| `PredictConfig`, `OfflinePredictor`, `SmartInit`, checkpoint/`.npz` inspection, Caffe conversion, SavedModel export, compact graph export, inference example patterns | [`sub-skills/inference-export/SKILL.md`](sub-skills/inference-export/SKILL.md) |
| Broad example-family lookup across basics, ResNet/ImageNet, Faster/Mask R-CNN, GAN, RL, speech, NLP, Caffe, saliency/CAM, Keras | [`references/examples-catalog.md`](references/examples-catalog.md) |
| Unknown install/import/runtime failure | [`references/troubleshooting.md`](references/troubleshooting.md), then the nearest sub-skill troubleshooting guide |

## Use this skill when

- The user asks about Tensorpack APIs such as `DataFlow`, `ModelDesc`,
  `TrainConfig`, `SimpleTrainer`, `InferenceRunner`, `OfflinePredictor`,
  `SmartInit`, `ModelExporter`, `argscope`, `LinearWrap`, or Tensorpack model
  layers.
- The user needs to build or debug a graph-mode TensorFlow training loop while
  keeping data loading, callbacks, summaries, validation, checkpointing, and
  export consistent with Tensorpack conventions.
- The user has Tensorpack checkpoint or model-zoo weights and needs variable
  names, shape matching, `.npz` conversion, prediction, or export.
- The task is to adapt a Tensorpack example pattern, while preserving dataset,
  optional dependency, and CPU/GPU verification limits.

## Avoid this skill when

- The request is ordinary PyTorch, JAX, modern `tf.keras`, or TensorFlow 2 eager
  training with no Tensorpack dependency.
- The user wants a full benchmark or paper-performance reproduction but has not
  supplied the exact dataset, pretrained weights, hardware, and optional
  dependencies; provide implementation guidance and state verification limits.
- The task is general TensorFlow Serving, container orchestration, or MLOps
  deployment beyond Tensorpack export artifact creation.
- The request is only about maintaining this repository checkout rather than
  using Tensorpack as a package; use a repository-maintenance skill if available.

## Install and import guidance

Tensorpack's package dependencies include NumPy, six, termcolor, tabulate, tqdm,
msgpack/msgpack-numpy, pyzmq, and psutil. TensorFlow is required for training,
models, prediction, checkpoints, and export; DataFlow can be used as a pure
Python data pipeline without full TensorFlow workflows. OpenCV is optional but
important for image augmentation and most vision examples.

Public install patterns from the project evidence:

```bash
pip install --upgrade git+https://github.com/tensorpack/tensorpack.git
# or pin an exact Tensorpack source/release version for reproducible research
```

Minimal import check:

```bash
python - <<'PY'
import tensorpack
print("tensorpack", tensorpack.__version__)
from tensorpack.dataflow import FakeData, BatchData
from tensorpack import tfv1 as tf
print("tf compat", tf.__name__)
PY
```

For TF2 runtimes, disable eager execution before graph construction when the
workflow uses Tensorpack trainers or graph APIs:

```python
from tensorpack import tfv1 as tf
tf.disable_eager_execution()
```

## Safe helper

Run the bundled environment diagnostic from the root of this skill directory or
by giving its full path:

```bash
python scripts/check_tensorpack_env.py --json
python scripts/check_tensorpack_env.py --require-tf --require-cv2
```

It reports installed Tensorpack/TensorFlow versions, optional dependency status,
and visible TensorFlow GPU devices. It does not download data, train, write
outside normal stdout, or inspect original source files.

## Verification status

This generated skill was constructed with a CPU inspection and smoke environment.
Core package imports, DataFlow construction, TensorFlow graph construction, and
selected helper parser checks were verified. CUDA/multi-GPU, Horovod/BytePS,
Caffe, Atari/Gym, COCO, TIMIT, and large-dataset example workflows are documented
as optional or data/backend-dependent; do not claim they are verified unless the
user supplies and verifies the required stack.

## Hard boundaries

- Keep runtime answers self-contained. Do not require future agents to open or
  run original Tensorpack source files, docs, examples, or scripts.
- Link only to files inside this generated skill tree when giving reusable
  instructions. Source evidence paths live in provenance and review artifacts,
  not as runtime dependencies.
- Do not reveal private environment prefixes, activation commands, local checkout
  paths, or package installation locations in user-facing answers.
- Respect the user's current request: this skill was generated for local use and
  should not be imported unless a later user explicitly requests import.
