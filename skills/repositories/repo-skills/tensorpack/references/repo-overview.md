# Tensorpack overview

## Purpose

Read this for the broad Tensorpack package map, compatibility assumptions,
dependency tiers, and route selection before opening a focused sub-skill.

## What Tensorpack is

Tensorpack is a graph-mode TensorFlow training interface focused on fast,
flexible research workflows. Its key operating surfaces are:

- **DataFlow**: pure-Python iterable data pipelines that can be used alone or fed
  into Tensorpack trainers.
- **Training interface**: `ModelDesc`, `TrainConfig`, trainers, callbacks,
  monitors, summaries, and graph-building utilities.
- **Prediction/export**: `PredictConfig`, predictors, `SmartInit`, checkpoint
  and `.npz` loading, plus SavedModel and compact graph export.
- **Example recipes**: large, research-oriented examples for vision, RL, speech,
  NLP, Caffe conversion, saliency/CAM, Keras integration, and model export.

Tensorpack is not a generic model wrapper. It lets users write TensorFlow graph
code directly, use any compatible symbolic library, and rely on Tensorpack for
input latency hiding, training loops, callback scheduling, checkpointing, and
common layers/helpers.

## TensorFlow compatibility

- Tensorpack is TF1-graph-oriented.
- In TensorFlow 2 runtimes, Tensorpack uses `tf.compat.v1` through
  `tensorpack.tfv1`.
- Disable eager execution before building Tensorpack trainer graphs when needed:

```python
from tensorpack import tfv1 as tf
tf.disable_eager_execution()
```

- Many examples were updated to tolerate TF2 compatibility mode, but older or
  domain-specific examples may still depend on TF1-era symbols, graph behavior,
  or optional TensorFlow internals.
- DataFlow can be used without TensorFlow for pure Python data processing, but
  importing top-level Tensorpack may still probe TensorFlow availability.

## Package topology

| Module family | Role | Primary route |
| --- | --- | --- |
| `tensorpack.dataflow` | DataFlow base classes, sources, wrappers, serializers, parallel runners/mappers, remote/ZMQ utilities. | `sub-skills/dataflow/` |
| `tensorpack.dataflow.dataset` | Dataset loaders for MNIST, Fashion-MNIST, CIFAR, SVHN, ILSVRC12, BSDS500, Caltech silhouettes, TinyImageNet, Places. | `sub-skills/dataflow/` |
| `tensorpack.dataflow.imgaug` | Image augmentors, deterministic transforms, coordinate transforms, composition. | `sub-skills/dataflow/` |
| `tensorpack.input_source` | Bridge between DataFlow/TensorFlow input producers and trainer tensors: feed, queue, staging, dataset, tensor, ZMQ inputs. | `sub-skills/dataflow/` plus `training` for trainer context |
| `tensorpack.train` | `TrainConfig`, trainers, training loop, tower trainers, launch helpers, auto-resume config. | `sub-skills/training/` |
| `tensorpack.callbacks` | Model saving, inference runners, hyperparameter schedules, monitors, profiling, summary/metric hooks, debugging callbacks. | `sub-skills/training/` |
| `tensorpack.models` | Common TF symbolic layers (`Conv2D`, `FullyConnected`, `BatchNorm`, pooling, dropout), `argscope`, `LinearWrap`. | `sub-skills/training/` |
| `tensorpack.tfutils` | Session init, checkpoint variable manipulation, summaries, optimizer helpers, tower context, graph utilities. | `training` or `inference-export` by task |
| `tensorpack.predict` | `PredictConfig`, online/offline/feedfree predictors, dataset and multi-tower prediction helpers. | `sub-skills/inference-export/` |
| `tensorpack.utils` | Logging, serialization, filesystem, GPU/NVML helpers, Caffe loading, visualization, concurrency utilities. | route by nearest workflow |
| `tensorpack.contrib` | Experimental integrations, notably Keras bridging. | `sub-skills/training/` with caveats |

## Dependency tiers

### Base package

The package metadata requires NumPy, six, termcolor, tabulate, tqdm, msgpack,
msgpack-numpy, pyzmq, and psutil. These are expected for normal Tensorpack
imports and DataFlow utilities.

### TensorFlow-dependent workflows

Training, callbacks, Tensorpack layers, `InputSource`, checkpoint utilities,
predictors, and export require TensorFlow. For current environments, prefer a
TensorFlow version that still supports `tf.compat.v1` graph mode and test the
exact APIs used by the task.

### Common optional dependencies

| Dependency | Used by |
| --- | --- |
| OpenCV (`cv2`) | image augmentors, dataset/image examples, Caffe/image inference demos |
| `lmdb` | `LMDBSerializer`, LMDB datasets, TIMIT and ImageNet-style serialized pipelines |
| `h5py` | `HDF5Serializer` |
| `pyarrow` | optional serializer backend via `TENSORPACK_SERIALIZE=pyarrow` or `TENSORPACK_ONCE_SERIALIZE=pyarrow` |
| `diskcache` | optional `DiskCacheSerializer`/data cache utility |
| `matplotlib`, `scipy`, `scikit-learn` | example or analysis workflows, not required for core training |
| `python-prctl` | Linux process cleanup in some RL examples |

### Domain-specific optional dependencies

| Domain | Typical requirements |
| --- | --- |
| Caffe conversion | Caffe Python bindings, `protoc`, `.prototxt`, `.caffemodel`, often OpenCV |
| Faster/Mask R-CNN | COCO data, pycocotools, scipy, OpenCV, pretrained weights, GPU recommended |
| RL Atari | Gym/Gymnasium Atari extras or legacy Gym, accepted ROMs, optional GPU, optional `python-prctl` |
| TIMIT speech | Licensed TIMIT data, `bob.ap`, scipy, LMDB, wav conversion tools |
| ImageNet / large vision | ImageNet layout, model-zoo weights for eval/finetune, many CPU cores, GPU recommended |
| Keras integration | TensorFlow/Keras versions compatible with TF1 graph/tower variable scopes; experimental |

## No console entry points

Installed package metadata exposes no console scripts. Operational commands come
from Python APIs or bundled helpers in this generated skill tree.

## Route selection examples

- "How do I batch and prefetch an image dataset?" -> `dataflow`.
- "How do I write a Tensorpack training script with validation and checkpoints?" -> `training`.
- "How do I list variables in a Tensorpack checkpoint or load `.npz` model-zoo weights?" -> `inference-export`.
- "How do I export a Tensorpack model for Serving?" -> `inference-export`.
- "Can I reproduce Faster R-CNN on COCO?" -> root example catalog, then `training` and `inference-export`, while surfacing GPU/data/dependency limits.

## Verification baseline

The generated skill's required backend is CPU for core package operations. The
inspection environment verified Tensorpack 0.11 with TensorFlow CPU 2.12,
OpenCV, LMDB, HDF5, DataFlow iteration, and simple graph/layer construction.
GPU and large-dataset example routes are documented but not treated as verified.
