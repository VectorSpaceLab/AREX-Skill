# Tensorpack example catalog

## Purpose

Read this when the user names a Tensorpack example family, paper/model recipe,
or domain workflow. This catalog summarizes source-evidence patterns and routes
without requiring the original example checkout. If the user supplies an actual
checkout containing Tensorpack examples, confirm the user-provided paths before
running anything.

## Verification labels

- **Bundled smoke available**: this generated skill includes a safe helper that
  exercises the pattern on tiny synthetic data.
- **CPU-native candidate**: a native test/example can often be run after setup,
  but may need data cache or extra approval.
- **Documentation only**: the workflow depends on large data, pretrained weights,
  hardware, credentials/licensed data, or domain packages and is not verified by
  default.

## Basic and starter workflows

| Family / entry signal | Workflows | Requirements | Route | Verification |
| --- | --- | --- | --- | --- |
| Basic training / MNIST-style convnet | `ModelDesc`, Tensorpack layers, `TrainConfig`, validation callbacks, summaries, model saving. | TensorFlow graph mode; MNIST-style data may need dataset cache/network. | `sub-skills/training/` | Bundled fake-data training smoke; MNIST native candidate optional. |
| TensorFlow layers variant | Shows that standard TF symbolic functions can live inside Tensorpack training. | TensorFlow graph mode. | `sub-skills/training/` | Documentation only. |
| CIFAR/SVHN toy convnets | Small classification training with dataset loaders. | Dataset cache/download; TensorFlow. | `training` + `dataflow` | Documentation only unless data present. |
| Starter boilerplate | Minimal `ModelDesc`, fake data, callbacks, `SmartInit` pattern. | TensorFlow CPU is enough. | `sub-skills/training/scripts/minimal_training_smoke.py` | Bundled smoke available. |
| Export demo | Fake-data train, separate inference graph, SavedModel, compact graph, apply modes. | TensorFlow CPU is enough; OpenCV not required in the bundled helper. | `sub-skills/inference-export/scripts/export_model_demo.py` | Bundled smoke available. |
| Experimental Keras bridge | Use a Keras model or Keras layers inside Tensorpack trainers. | Compatible TF/Keras graph-mode behavior; fragile variable scopes. | `sub-skills/training/references/example-recipes.md` | Documentation only. |

## Vision training and inference families

| Family / entry signal | Workflows | Requirements | Route | Verification |
| --- | --- | --- | --- | --- |
| ResNet and ImageNet classification | ImageNet data layout, DataFlow pipelines, multi-GPU training, `.npz` model-zoo eval, Caffe-converted ResNet loading. | ImageNet, optional pretrained weights, GPU recommended; CPU only for small/fake checks. | `training`, `dataflow`, `inference-export` | Documentation only by default. |
| ImageNet model variants | AlexNet, VGG, Inception-BN, ShuffleNet, DoReFa-style ImageNet classification recipes. | ImageNet, many CPU cores for data, GPU recommended. | `training` + `dataflow` | Documentation only. |
| Faster/Mask R-CNN | COCO train/eval/predict, FPN/Cascade/Mask settings, config overrides, compact/Serving export. | COCO, pycocotools/scipy/OpenCV, pretrained weights, GPU strongly recommended. | `training` + `inference-export` | Documentation only. |
| GAN family | DCGAN, InfoGAN, Conditional GAN, WGAN/WGAN-GP, BEGAN, pix2pix, CycleGAN, DiscoGAN. | TensorFlow; datasets vary; GPU recommended for useful training. | `training` | Documentation only; MNIST variants may become CPU-native candidates if bounded. |
| DoReFa-Net / quantization | Low-bitwidth CNN training and ImageNet/SVHN variants. | TensorFlow, scipy, ImageNet/SVHN, GPU recommended. | `training` | Documentation only. |
| HED edge detection | BSDS-style data, VGG initialization, training/view/inference heatmaps. | Dataset, pretrained VGG weights, OpenCV, GPU recommended. | `training` + `inference-export` | Documentation only. |
| Spatial Transformer | MNIST addition training and visualization. | TensorFlow, MNIST-style data/model weights for view mode. | `training` + `inference-export` | Documentation only. |
| Saliency and CAM | Guided-ReLU saliency and class activation maps with ResNet-style models. | Pretrained weights, ImageNet/image inputs, OpenCV, optional DISPLAY. | `inference-export` | Documentation only. |
| Similarity learning | Siamese/cosine/triplet/center-loss MNIST embeddings and visualization. | TensorFlow, MNIST, optional visualization stack. | `training` | Documentation only. |
| SuperResolution / EnhanceNet | COCO/VGG-backed training, LMDB option, apply mode. | COCO zip/LMDB, VGG19 weights, TensorFlow, GPU recommended. | `training`, `dataflow`, `inference-export` | Documentation only. |
| Dynamic Filter Networks | Steering-filter training and TensorBoard image output. | TensorFlow, GPU optional/recommended. | `training` | Documentation only. |
| Caffe model conversion/loading | Convert Caffe weights to `.npz`, load AlexNet/VGG/CPM-style models, run image inference. | Caffe Python bindings, `protoc`, model files, OpenCV. | `inference-export` | Documentation only; Caffe is optional and unverified. |

## Reinforcement learning families

| Family / entry signal | Workflows | Requirements | Route | Verification |
| --- | --- | --- | --- | --- |
| Deep Q-Network / Atari | DQN, Double-DQN, Dueling-DQN train/play/eval with Atari ROM or Gym Atari environment. | Gym/Gymnasium Atari stack, ROM/license, TensorFlow, GPU recommended for useful training. | `training` | Documentation only. |
| A3C Gym Atari | Multi-GPU A3C train/play/video dump patterns. | Gym Atari environment, TensorFlow, GPU strongly recommended; `python-prctl` helps Linux cleanup. | `training` | Documentation only. |

## Speech and NLP families

| Family / entry signal | Workflows | Requirements | Route | Verification |
| --- | --- | --- | --- | --- |
| TIMIT CTC | Convert NIST WAV to WAV, extract MFCC, build LMDB, compute stats, train/test CTC model. | Licensed TIMIT data, `bob.ap`, scipy, LMDB, conversion tools. | `dataflow` + `training` | Documentation only. |
| Char-RNN | Train on `input.txt`, sample generated text. | Text corpus, TensorFlow. | `training` + `inference-export` | Documentation only. |
| Penn Treebank LSTM | Stateful RNN language model and TF reader pipeline. | PTB-style data, TensorFlow. | `training` + `dataflow` | Documentation only. |

## How to answer example requests

1. Identify whether the user wants training, data preparation, prediction/export,
   or a dependency/data-layout explanation.
2. State required data, optional dependencies, and backend assumptions before
   giving a command shape or code skeleton.
3. Prefer bundled smoke helpers when the user only needs to validate Tensorpack
   installation or understand the API shape.
4. For large research examples, do not promise reproduction from CPU smoke tests.
   Ask for exact data, weights, GPU count, TensorFlow version, and expected
   metric/runtime if the user wants performance reproduction.
5. If the user provides a checkout with the original example files and asks to
   run them, first verify the path, dependency list, dataset location, GPU/CPU
   expectation, and side effects. Otherwise, keep guidance self-contained.

## Route summary

- Data layout, augmentation, serialization, input speed -> `sub-skills/dataflow/`.
- Model/trainer/callback/summary/example training logic -> `sub-skills/training/`.
- Checkpoint/npz/prediction/export/conversion -> `sub-skills/inference-export/`.
