# Tensorpack training example recipes

This catalog summarizes Tensorpack training example families as reusable
patterns. It is intentionally self-contained: do not assume the original example
files are available at runtime. If a user has the example bundle separately,
treat the command shapes below as reference commands; otherwise re-create the
needed pattern in a new script using [workflows.md](workflows.md) and
[api-reference.md](api-reference.md).

Verification status meanings:

- **bundled smoke**: covered by the generated fake-data helper.
- **CPU candidate**: small CPU-native behavior was selected for later integrated
  verification, subject to dataset/cache availability.
- **documentation only**: large data, optional dependencies, GPU, credentials,
  or long training make default execution inappropriate.
- **route elsewhere**: training touches the family, but another sub-skill owns
  detailed dataflow or inference/export guidance.

## Quick routing table

| Family | Command shape to adapt | Data/deps/backend | Verification status | Route owner |
| --- | --- | --- | --- | --- |
| Minimal fake-data training | `python minimal_training_smoke.py --workdir <DIR> --steps-per-epoch 2 --max-epoch 1` | Tensorpack + TensorFlow CPU; no network/data. | bundled smoke | training |
| Basic MNIST ConvNet | `python <mnist-convnet> [--gpu 0] [--load <CKPT_OR_NPZ>]` | MNIST dataset; may download/cache; CPU feasible. | CPU candidate via small MNIST/native test when data is available; otherwise fake-data smoke. | training + dataflow |
| Basic CIFAR/SVHN ConvNet | `python <cifar-or-svhn-convnet> [--gpu 0]` | Dataset download/cache; CPU feasible but slow for full training. | documentation only for full metrics. | training + dataflow |
| ImageNet ResNet | `python <imagenet-resnet> --data <ILSVRC_DIR> -d 50 [--gpu 0,1,2,3] [--load <NPZ_OR_CKPT>]`; evaluation adds `--eval`. | ILSVRC layout, OpenCV, large storage; GPU strongly recommended. | documentation only; no performance claim without ImageNet/GPU. | training + dataflow + inference-export |
| CIFAR ResNet | `python <cifar-resnet> --gpu 0,1 [-n <DEPTH_UNITS>] [--load <CKPT>]` | CIFAR dataset; examples often assume GPU/NCHW; CPU may fail on unsupported NCHW ops. | documentation only for benchmark. | training |
| ImageNet model zoo variants | `python <imagenet-model> --data <ILSVRC_DIR> [--eval --load <NPZ>] [model flags]` | ILSVRC, OpenCV; GPU for realistic training/eval. | documentation only. | training + inference-export |
| Faster/Mask R-CNN | `python <detection-train> --config KEY=VALUE ... [--load <WEIGHTS>]`; prediction/eval use matching config and checkpoint. | COCO or custom registered dataset, pycocotools, scipy, GPU recommended/required for useful training. | documentation only. | training + dataflow + inference-export |
| GAN families | `python <gan-script> [--gpu 0] [--load <CKPT>]`; sampling usually adds `--sample`. | MNIST for simple variants; image-to-image/CycleGAN/CelebA/cityscapes need external image datasets and OpenCV. | documentation only; fake-data helper covers framework mechanics only. | training |
| Atari DQN | `python <dqn-train> --env <ROM_OR_GYM_ENV> [--algo DQN|Double|Dueling]`; play/eval add `--task play|eval --load <MODEL>`. | Gym/ALE/ROMs, OpenCV, large replay memory, long training; GPU useful. | documentation only. | training |
| Atari A3C | `python <a3c-train> --env <ROM_OR_GYM_ENV> [--gpu 0,1]`; eval/play use task flags and loaded model. | Gym/ALE/ROMs, multiprocessing, OpenCV, CPU/GPU resources. | documentation only. | training |
| TIMIT CTC speech | Build LMDBs: `python <timit-prep> build --dataset <TIMIT_SPLIT> --db <OUT.mdb>`; train: `python <timit-train> --train train.mdb --test test.mdb --stat stats.data`. | Licensed TIMIT data, LMDB, audio feature dependencies, TensorFlow CTC/RNN APIs. | documentation only; dataflow owns LMDB prep pattern. | dataflow + training |
| Char-RNN | `python <char-rnn> train --corpus <TEXT>`; sampling uses `sample --load <MODEL> --start <TEXT>`. | Plain text corpus; TF1 RNN APIs; CPU feasible for small corpus. | documentation only. | training + inference-export |
| Penn Treebank LSTM | `python <ptb-lstm> [--gpu 0] [--load <CKPT>]` | PTB text files, may download/cache, TF1 RNN APIs. | documentation only. | training |
| Tensorpack + Keras | `python <keras-example> ...` only after checking wrapper caveats. | Keras/TensorFlow compatibility; variable-scope behavior is experimental. | documentation only; not recommended default path. | training |
| HED / Spatial Transformer / Similarity / Saliency training variants | Family-specific train commands with dataset/model flags; saliency/CAM often has inference mode too. | External datasets/weights; GPU and visualization dependencies depending on family. | documentation only. | training + inference-export |
| Caffe model conversion examples | Conversion/prediction command shape: `python -m tensorpack.utils.loadcaffe <prototxt> <caffemodel> <out.npz>` then load `.npz` for inference. | Caffe Python bindings, prototxt, caffemodel; mostly inference/export, not training. | route elsewhere. | inference-export |

## Minimal fake-data training

Use this when the user needs to prove Tensorpack is importable and can execute a
one-epoch graph training loop without network, downloads, datasets, or GPU.

Command:

```bash
python ../scripts/minimal_training_smoke.py --workdir /tmp/tensorpack-smoke --steps-per-epoch 2 --max-epoch 1
```

What it covers:

- `ModelDesc.inputs/build_graph/optimizer`;
- Tensorpack symbolic layers (`Conv2D`, `FullyConnected`, `argscope`);
- moving summaries and parameter summaries;
- `TrainConfig`, `SimpleTrainer`, `launch_train_with_config`;
- `ModelSaver`, `InferenceRunner`, `ScalarStats`, and a simple learning-rate
  schedule.

What it does not cover:

- real dataset correctness;
- multi-GPU/distributed behavior;
- checkpoint transfer from a user model;
- benchmark speed or accuracy.

## Basic supervised image demos

### MNIST ConvNet pattern

Command shape:

```bash
python <mnist-convnet> [--gpu 0] [--load <CHECKPOINT_OR_NPZ>]
```

Core pattern:

- `inputs()` defines image and integer-label tensors.
- `build_graph()` normalizes image tensors, chains `Conv2D`, `MaxPooling`,
  `FullyConnected`, computes sparse softmax cross entropy, adds moving summary
  for loss/error/accuracy, and returns total cost.
- `optimizer()` builds an exponentially decayed learning rate.
- `TrainConfig` uses `ModelSaver`, `InferenceRunner`, `ScalarStats` or
  `ClassificationError`, and `SimpleTrainer`.

Data/deps/backends:

- MNIST data may be downloaded or read from cache.
- CPU is enough for parser/small smoke; full training is slower.
- If a task only needs framework mechanics, prefer the bundled fake-data helper.

Verification status: CPU candidate when MNIST data/cache is available; otherwise
use the fake-data smoke.

### CIFAR/SVHN ConvNet pattern

Command shape:

```bash
python <cifar-or-svhn-convnet> [--gpu 0] [--load <CHECKPOINT>]
```

Use for small RGB supervised classification recipes. Watch for:

- dataset download/cache behavior;
- OpenCV/image augmentation dependencies;
- CPU speed limits;
- examples using `channels_first`/NCHW, which can fail on CPU depending on the
  TensorFlow build.

Verification status: documentation only for full accuracy.

## ResNet and ImageNet families

### ImageNet ResNet

Command shapes:

```bash
python <imagenet-resnet> --data <ILSVRC_DIR> -d 50 --gpu 0,1,2,3
python <imagenet-resnet> --data <ILSVRC_DIR> -d 50 --load <RESNET_NPZ_OR_CKPT> --eval
python <imagenet-resnet> --data <ILSVRC_DIR> -d 50 --fake
```

Training pattern:

- Determine number of towers from visible GPUs.
- Divide global batch by tower count; each tower receives a full per-tower
  batch, not a slice of one global tensor.
- Scale base learning rate by global batch size.
- Use `ScheduledHyperParamSetter` for warmup and step/epoch schedules.
- Add `InferenceRunner` or data-parallel inference for validation.
- Prefer `SyncMultiGPUTrainerReplicated` or a documented multi-GPU trainer.

Data/deps/backends:

- Requires ILSVRC directory structure.
- OpenCV and a performant DataFlow or TF data input are important.
- GPU is strongly recommended for real training/evaluation.

Verification status: documentation only. The `--fake` style is useful for graph
and throughput debugging but does not prove ImageNet accuracy.

### CIFAR ResNet

Command shape:

```bash
python <cifar-resnet> --gpu 0,1 [-n <NUM_UNITS>] [--load <CHECKPOINT>] [--logdir <DIR>]
```

Important caveats:

- Some CIFAR ResNet code asserts GPU availability or uses `channels_first`.
- Batch size is often specified per GPU.
- Full paper-like metrics require the exact dataset, schedule, and GPU setup.

Verification status: documentation only.

### ImageNet model zoo variants

Families include ShuffleNet, AlexNet, VGG, Inception-BN, ResNet variants, and
low-bitwidth DoReFa-style models.

Command shapes:

```bash
python <imagenet-model> --data <ILSVRC_DIR> --eval --load <MODEL_NPZ> [model flags]
python <imagenet-model> --flops [model flags]
```

Use these recipes to recover model/backbone choices, `argscope` patterns,
`data_format` decisions, and evaluation flags. Do not claim verified
performance without supplied ImageNet data, model weights, and matching GPU
backend.

## Detection and segmentation: Faster/Mask R-CNN

Command shapes:

```bash
python <detection-train> --config KEY=VALUE KEY=VALUE ... [--load <WEIGHTS>]
python <detection-predict> --predict image1.jpg image2.jpg --load <CHECKPOINT> --config SAME_AS_TRAINING
python <detection-predict> --evaluate output.json --load <CHECKPOINT> --config SAME_AS_TRAINING
```

Training pattern:

- A central config controls dataset, model variant, FPN/C4 mode, trainer, GPU
  count, LR schedule, evaluation period, and checkpoint period.
- Data registration must match COCO/custom dataset layout before training.
- Schedule may mix step-based warmup and epoch-based LR changes.
- `PeriodicCallback(ModelSaver(...), every_k_epochs=...)`,
  `ScheduledHyperParamSetter`, throughput/memory trackers, and evaluation
  callbacks are typical.
- Horovod may be selected by config; otherwise replicated multi-GPU trainer is
  typical.

Data/deps/backends:

- COCO or registered custom dataset; pycocotools and scipy-like dependencies.
- GPU is effectively required for useful training.
- Prediction/evaluation belongs mostly to inference-export.

Verification status: documentation only.

## GAN families

Families include DCGAN, InfoGAN, Conditional GAN, WGAN/Improved WGAN/BEGAN,
image-to-image, CycleGAN, and DiscoGAN-like examples.

Command shapes:

```bash
python <gan-script> [--gpu 0] [--load <CHECKPOINT>]
python <gan-script> --sample --load <CHECKPOINT>
```

Training pattern:

- Some examples use custom `ModelDesc`/trainer classes because GAN iterations
  are not always one-cost-one-optimizer.
- Generator/discriminator functions must respect variable reuse; decorators or
  explicit `tf.variable_scope(..., reuse=...)` patterns are common.
- Sampling modes are inference/export-like and should route to inference-export
  if the user only wants generated images from a checkpoint.

Data/deps/backends:

- MNIST variants are the simplest; other variants require image datasets,
  OpenCV, and longer training.
- CPU can build many graphs but useful training/sampling is often GPU-oriented.

Verification status: documentation only; fake-data smoke covers only the generic
Tensorpack training machinery.

## Reinforcement learning: DQN and A3C

### DQN

Command shapes:

```bash
python <dqn-train> --env <BREAKOUT_ROM_OR_GYM_ENV> [--algo DQN|DoubleDQN|DuelingDQN]
python <dqn-train> --env <BREAKOUT_ROM_OR_GYM_ENV> --task play --load <MODEL>
python <dqn-train> --env <BREAKOUT_ROM_OR_GYM_ENV> --task eval --load <MODEL> --num-eval 50
```

Pattern and caveats:

- Uses experience replay and large replay memory.
- Environment wrappers resize, stack frames, and handle Atari reset semantics.
- `steps_per_epoch` may represent environment transitions divided by update
  frequency, not dataset passes.
- Dependencies include Gym/ALE/ROMs and OpenCV; licensing/setup can block runs.

Verification status: documentation only.

### A3C

Command shapes:

```bash
python <a3c-train> --env <ROM_OR_GYM_ENV> [--gpu 0,1]
python <a3c-train> --env <ROM_OR_GYM_ENV> --task eval --load <MODEL> [--episode 100]
```

Pattern and caveats:

- Uses simulator processes/threads and async-style training logic.
- GPU count affects predictor threads and trainer choice.
- Multiprocessing cleanup and Gym/ALE versions matter.

Verification status: documentation only.

## Speech and NLP

### TIMIT CTC

Command shapes:

```bash
python <timit-prep> build --dataset <TIMIT_TRAIN_DIR> --db train.mdb
python <timit-prep> build --dataset <TIMIT_TEST_DIR> --db test.mdb
python <timit-prep> stat --db train.mdb
python <timit-train> --train train.mdb --test test.mdb --stat stats.data [--gpu 0] [--load <CHECKPOINT>]
```

Pattern:

- Dataflow creates LMDB and normalization statistics.
- Model uses variable-length sequences, CTC loss, greedy decoding in training,
  and beam search in inference mode.
- Optimizer often wraps Adam with global norm clipping and gradient summaries.

Data/deps/backends:

- TIMIT is licensed/non-public.
- Audio feature dependencies and LMDB are required.
- CPU can document the command path but real training needs the dataset and
  compatible TF1 RNN/CTC APIs.

Verification status: documentation only. Data preparation details route to
`../dataflow/SKILL.md`.

### Char-RNN

Command shapes:

```bash
python <char-rnn> train --corpus <TEXT_FILE> [--gpu 0] [--load <CHECKPOINT>]
python <char-rnn> sample --load <CHECKPOINT> --start "seed text" --num 500 --temperature 1.0
```

Pattern:

- Custom `RNGDataFlow` samples sequence windows from a text corpus.
- Model uses TF1 RNN cells and persistent hidden-state variables/placeholders.
- Sampling/prediction mode should route to inference-export if the user only
  wants generated text.

Verification status: documentation only.

### Penn Treebank LSTM

Command shape:

```bash
python <ptb-lstm> [--gpu 0] [--load <CHECKPOINT>]
```

Pattern:

- Shows TF reader pipeline use instead of a Tensorpack DataFlow.
- May download PTB files if absent.
- Uses TF1 RNN APIs, dropout conditioned on training mode, state variables, and
  validation/test perplexity callbacks.

Verification status: documentation only.

## Tensorpack + Keras

Command shape:

```bash
python <keras-example> [example-specific flags]
```

Use only when the user explicitly asks for Keras integration or has existing
Keras model code to reuse. Important caveats:

- Tensorpack's Keras wrapper is experimental.
- Keras models may not respect TensorFlow variable-scope reuse like Tensorpack
  towers expect.
- Learning phase may need a dedicated callback/hook so training and inference
  towers see the right Keras phase.
- If the user only wants a new Tensorpack script, prefer native Tensorpack
  `ModelDesc` and layers or plain TF symbolic functions.

Verification status: documentation only.

## Other vision recipes

| Family | Command shape | Notes | Route owner |
| --- | --- | --- | --- |
| HED edge detection | `python <hed> --view`; train/load variants use `--load <MODEL>`; inference uses `--run <IMAGE>`. | Requires BSDS-like data and VGG/pretrained weights; may download data; visualization/inference routes elsewhere. | training + inference-export |
| Spatial Transformer | `python <spatial-transformer> [--load <MODEL> --view]` | MNIST addition-style demo; dataset/cache needed. | training |
| Similarity learning | `python <similarity> --algorithm siamese|cosine|triplet|softtriplet|center`; visualization adds `--visualize --load <CHECKPOINT>`. | MNIST-like data and embedding visualization. | training + inference-export |
| Saliency/CAM | `python <cam-resnet> --data <ILSVRC_DIR> [--load <MODEL>] [--gpu 0,1]`; CAM/inference adds `--cam`. | Training/eval needs ImageNet; saliency visualization routes to inference-export. | training + inference-export |
| Super-resolution / optical flow / dynamic filters | family-specific trainer/eval flags | External datasets/weights and GPU recommended. | training + inference-export |

## How to adapt a recipe safely

1. Identify the example family and read its row above.
2. Ask whether the user has the required dataset, optional dependencies, and
   backend hardware. Do not silently assume downloads, COCO/ImageNet/TIMIT, ROMs,
   Caffe bindings, or Horovod.
3. Recreate only the needed training pattern in a new script: `ModelDesc`, input
   source, callbacks, trainer, and schedule.
4. For data construction/performance, route to `../dataflow/SKILL.md`.
5. For loading pretrained weights, checkpoint inspection, prediction, or export,
   route to `../inference-export/SKILL.md`.
6. Start with CPU/fake-data or a tiny fixture check when possible, then require
   the real data/backend before claiming task-level success.
7. State verification status explicitly: parser/smoke, CPU candidate, or full
   dataset/backend reproduction.
