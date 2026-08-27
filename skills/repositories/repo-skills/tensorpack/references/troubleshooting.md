# Tensorpack cross-cutting troubleshooting

## Purpose

Use this guide for install/import/backend failures before routing to a focused
sub-skill. For workflow-specific failures, continue into the nearest
sub-skill's `references/troubleshooting.md`.

## Quick triage

| Symptom | Likely cause | First recovery |
| --- | --- | --- |
| `ModuleNotFoundError: msgpack_numpy` | Base Tensorpack dependency missing or partial install. | Reinstall Tensorpack package dependencies; run `scripts/check_tensorpack_env.py --require-tf` if training/prediction is needed. |
| `Failed to import tensorflow.` printed during import | TensorFlow is absent; DataFlow-only work may still run, but training/prediction/export will not. | Install a TensorFlow package compatible with the user's Python and desired CPU/GPU backend. |
| TF2 eager/graph errors, missing `tf.Session`, or unexpected eager tensors | Tensorpack workflow is TF1 graph-oriented. | Use `from tensorpack import tfv1 as tf` and call `tf.disable_eager_execution()` before graph construction. |
| OpenCV import failure or image augmentation failures | `cv2` is optional but required by many image augmentors/examples. | Install OpenCV or avoid image-specific DataFlow/vision routes. |
| Serializer class is a dummy or raises import error | Optional serializer backend missing (`lmdb`, `h5py`, TensorFlow, `diskcache`, `pyarrow`). | Use DataFlow serializer smoke script in the dataflow sub-skill and install only the needed backend. |
| Checkpoint restore warns variables are only in graph or only in checkpoint | Variable names differ; Tensorpack restore is exact-name based. | Inspect weights with `sub-skills/inference-export/scripts/inspect_checkpoint.py`; rename graph variables or remap parameters. |
| Training appears slow but input queue is nearly empty | DataFlow/preprocessing bottleneck. | Route to `sub-skills/dataflow/references/workflows.md#performance-diagnosis`. |
| Training appears slow while input queue is full | TensorFlow graph/backend bottleneck, not DataFlow. | Route to training performance and GPU notes. |
| Multi-GPU run changes effective batch size or learning-rate schedule | Tensorpack feeds one input batch per tower/GPU. | Adjust total batch size, learning rate, and `steps_per_epoch`; route to training troubleshooting. |
| Caffe conversion cannot import `caffe` or `protoc` | Optional Caffe toolchain missing. | Treat conversion as optional; install Caffe/protobuf tools only when the user explicitly needs that conversion. |
| Faster R-CNN / COCO / RL / TIMIT example cannot start | Domain-specific data/dependencies missing. | Use `references/examples-catalog.md` to enumerate data, weights, optional packages, and backend needs before running anything. |

## Install and import checks

Run the root diagnostic first when the environment is unknown:

```bash
python scripts/check_tensorpack_env.py --json
python scripts/check_tensorpack_env.py --require-tf --require-cv2
```

Use `--require-gpu` only when the user explicitly needs CUDA/GPU verification.
A visible GPU in the host is not enough: the TensorFlow package must actually
see a GPU device.

## TensorFlow version and graph mode

Tensorpack was built for TensorFlow graph mode. Current TensorFlow 2 packages can
work through compatibility APIs, but common mistakes are:

1. importing TensorFlow directly and using TF2 eager semantics;
2. creating Keras/TF2 objects that do not respect TF1 variable scopes;
3. building the graph before disabling eager execution;
4. mixing training and inference graphs through an imported metagraph.

Preferred setup for Tensorpack trainer code:

```python
from tensorpack import tfv1 as tf
tf.disable_eager_execution()
```

Then continue with the training or inference-export sub-skill.

## Optional dependency boundaries

Do not install all optional dependency groups reflexively. Use the task to pick
the smallest set:

- DataFlow LMDB: `lmdb`.
- HDF5 serialization: `h5py`.
- Image augmentation or most vision examples: OpenCV.
- PyArrow serialization: `pyarrow` and an explicit serializer environment
  variable.
- Faster/Mask R-CNN: COCO data, pycocotools, scipy, OpenCV, pretrained weights,
  GPU recommended.
- RL Atari: Gym/Gymnasium Atari stack and ROM/license handling.
- TIMIT: licensed data plus `bob.ap` and audio conversion tools.
- Caffe conversion: Caffe Python bindings, `protoc`, `.prototxt`, and
  `.caffemodel` files.

## Backend verification

This generated skill documents GPU and distributed workflows, but CPU is the
only required verified backend. When the user asks for CUDA, Horovod, BytePS,
NCCL, or benchmark-scale training:

1. Check actual TensorFlow device visibility, not only `nvidia-smi`.
2. Confirm TensorFlow/CUDA/cuDNN/Horovod/BytePS version compatibility.
3. Confirm dataset and pretrained weights are available.
4. Run a small API or graph smoke before any long training job.
5. State clearly when GPU behavior is unverified.

## Data and artifact safety

- Tensorpack examples often download data or expect large local datasets. Ask
  before triggering downloads or long training.
- Many scripts write logs/checkpoints under a working directory. Prefer a user
  supplied scratch directory and do not overwrite existing artifacts without
  confirmation.
- Visualization flows may require DISPLAY or image output paths; route no-DISPLAY
  failures to inference-export troubleshooting.

## When to refresh this skill

Read `references/repo-provenance.md`. Refresh if the Tensorpack commit, package
version, dependency metadata, public module imports, examples, or current
checkout dirty state differs from the recorded snapshot.
