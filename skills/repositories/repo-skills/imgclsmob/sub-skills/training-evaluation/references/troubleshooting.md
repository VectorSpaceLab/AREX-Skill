# Training and evaluation troubleshooting

Use the smallest safe correction first. The dataset checker is filesystem-only;
it does not import MXNet, PyTorch, torchvision, or another framework, and it
never downloads data. A checker result is not proof that images, records,
weights, or optimizer state can be decoded by a training/evaluation entrypoint.

## Install and import failures

### `--help` fails with an import or shared-library error

The four entrypoints import their framework and project utilities before
`argparse` can print help. Classify this as an environment/import block, not a
dataset failure. Check the interpreter and package installation in the same
environment that will run the command; do not enable downloads or start
training to repair it. The standalone layout check remains usable because it
has no framework imports:

```bash
python scripts/check_dataset_layout.py --help
```

For a missing `mxnet`, `torch`, `torchvision`, or native library, use the
project's verified CPU environment or route backend-specific installation to
[framework-compatibility](../../framework-compatibility/SKILL.md). Avoid
installing an unrelated CUDA build merely because a machine has a GPU. A
successful `--help` parse proves only that imports and argument construction
succeeded; it does not validate a model, checkpoint, or dataset.

### The installed package appears to be the wrong version

Run the command with the intended interpreter and keep its package metadata
and logs together. Do not mix a system `python`, a virtual-environment
`python`, and a different `pip`. Re-run the entrypoint's help with the exact
flags intended for the bounded check. If import errors remain, stop at the
environment boundary rather than changing model or dataset flags.

## Dataset layout and configuration

### `ImageNet1K` reports missing `train/` or `val/`

`ImageNet1K` is the folder layout. Point `--data-dir` at the directory that
directly contains both split directories, not at `train/` itself and not at a
parent containing an extra `imagenet/` layer. The checker requires exactly
1000 class directories under each split:

```bash
python scripts/check_dataset_layout.py \
  --dataset ImageNet1K \
  --data-dir /data/imagenet \
  --backend auto
```

The command must return `ok` before launching a real CLI. A root containing
`train.rec`/`val.rec` is not a valid `ImageNet1K` folder root. Use
`--dataset ImageNet1K_rec` with a Gluon command only when all four non-empty
record/index files are present.

### `ImageNet1K_rec` reports missing record files

The Gluon record root must contain all four non-empty files directly under
`--data-dir`: `train.rec`, `train.idx`, `val.rec`, and `val.idx`. Do not pass a
folder-layout root or use `train_pt.py`/`eval_pt.py` for this dataset. For
PyTorch, select `--dataset ImageNet1K` and provide `train/` and `val/` class
directories.

### The checker reports `ambiguous_imagenet_layout`

Both folder split directories and record files were found. Choose one explicit
contract and pass a root containing only the artifacts needed for that
contract. This avoids silently selecting the wrong dataset class.

### CUB or a split loads incorrectly

`CUB200_2011` requires these paths directly under `--data-dir`:

```text
images.txt
image_class_labels.txt
train_test_split.txt
images/<class-name>/<image-file>
```

The checker verifies required files and the `images/` directory, but does not
parse metadata rows or decode every referenced image. If it returns `ok` and
loading still fails, inspect the first missing or unreadable path under
`images/`. CUB uses 200 classes; use `--no-aux` only when the selected model and
checkpoint require that model-extra behavior.

### CIFAR or SVHN would download

`CIFAR10`, `CIFAR100`, and `SVHN` use backend-native caches. Their real dataset
wrappers may download when local data is absent, so an empty root is not safe
for an offline run. The checker returns `missing_local_data` for an empty root
and `indeterminate_native_cache` for a non-empty root; it never calls a
downloader:

```bash
python scripts/check_dataset_layout.py --dataset CIFAR10 --data-dir /data/cifar10
python scripts/check_dataset_layout.py --dataset CIFAR100 --data-dir /data/cifar100
python scripts/check_dataset_layout.py --dataset SVHN --data-dir /data/svhn
```

Populate or verify the cache outside the bounded check, then run the selected
framework's integrity check with downloading explicitly disabled. For SVHN,
the expected split artifacts are `train_32x32.mat` and `test_32x32.mat`; CIFAR
cache names are backend-specific. A non-empty directory is only a presence
check, not proof that the framework can decode the cache.

### Dataset, class count, or root configuration is wrong

Dataset names are case-sensitive: `ImageNet1K`, `ImageNet1K_rec`, `CIFAR10`,
`CIFAR100`, `SVHN`, and `CUB200_2011`. Do not use `ImageNet-1K` or a display
label. `--data-dir` overrides the preset root. `--work-dir` only contributes
the default root; it does not relocate an explicitly supplied `--data-dir`.

The default class counts are ImageNet `1000`, CIFAR10/SVHN `10`, CIFAR100
`100`, and CUB `200`. Use `--num-classes N` only when the local checkpoint and
dataset genuinely use that count. Use `--in-channels N` only for a matching
input format. A layout pass cannot prove model-head compatibility; route
model and checkpoint shape checks to [model-inference](../../model-inference/SKILL.md).

### `test_metric_names` or a composite metric is missing

For the listed classification metainfo objects, use `--data-subset val` as the
held-out evaluation route. Several objects do not define separate test metric
names. `Top1Error` and `TopKError(top_k=5)` are errors, so lower is better; do
not report them as accuracies. The `--calc-flops-only` flag still constructs
the data source, so it does not bypass a bad `--data-dir`.

## CLI misuse and bounded CPU operation

### `unrecognized arguments` or `unrecognized dataset`

Select the dataset before relying on dataset-specific help and use the exact
entrypoint-specific flags from the CLI reference. All four commands require
`--model NAME`. Common flags include `--dataset NAME`, `--data-dir DIR`,
`--num-gpus N`, `--num-data-workers N` (or `-j N`), `--batch-size N`,
`--resume FILE`, and `--use-pretrained`. Evaluation uses `--data-subset val`
or `--data-subset test`; Gluon uses `--not-show-progress`, while PyTorch uses
`--show-progress`. Do not copy a flag from one framework's command to the
other without checking its entrypoint.

Use the bundled planner first to validate the dataset/framework/flag plan
without importing a backend:

```bash
python scripts/build_command.py --framework pytorch --mode eval \
  --dataset ImageNet1K --data-dir /data/imagenet --model resnet18
```

A later framework-specific help check may still be useful in an environment
that provides the repository CLI, but it does not validate a dataset or
checkpoint. Do not use `--all` or `--use-pretrained` for an offline check:
both can request provider weights.

### CPU process is too large, stalls, or exhausts memory

Use the exact common flags `--num-gpus=0`, `--num-data-workers 0`, and a small
`--batch-size` such as `1`, `4`, or `8`. At zero GPUs the helpers use CPU and
do not multiply the batch size by a GPU count. Keep Gluon `--not-show-progress`
when a clean log is useful; PyTorch progress is already opt-in unless
`--show-progress` is supplied. Reduce `--batch-size` before changing the model
or claiming a dataset problem.

### GPU is selected but unavailable or mismatched

`--num-gpus N` controls the requested device count; it does not install or
validate a CUDA runtime. Start with `--num-gpus=0` for a bounded CPU check. If
the GPU path is required, verify the installed framework build, visible device
count, and compatible driver/runtime in that environment before retrying. Do
not infer CUDA support from CPU Gluon or CPU PyTorch success, and route
CUDA/vendor-backend questions to [framework-compatibility](../../framework-compatibility/SKILL.md).

## Checkpoint and resume failures

### Gluon cannot open `--resume`

`--resume FILE` is a local model-parameter file, normally `.params`. It must
exist and match the selected model and class count. `--resume-state FILE` is a
separate Gluon trainer/optimizer state, normally `.states`; it is not a
replacement for `--resume`. When continuing a complete saved run, pass both
flags and set the intended 1-based `--start-epoch N` explicitly.

### PyTorch reports missing keys or unexpected `module.` keys

`--resume FILE` is normally a local `.pth` model checkpoint or a dictionary
containing `state_dict`. If keys are wrapped by `DataParallel`, add the exact
evaluation flag `--remove-module`; it only removes the `module.` wrapper. It
does not repair a different model name, class count, or tensor shape. For a
single-CPU evaluation, also use `--num-gpus=0`.

### PyTorch training state resumes at the wrong epoch

`--resume-state FILE` is the training state containing `epoch`, `state_dict`,
and `optimizer`; `--resume FILE` remains the model checkpoint. The training
CLI also receives explicit `--start-epoch N`, so set it deliberately rather
than assuming the state-file epoch controls the loop. Do not substitute
`--resume-state` for `--resume`.

### A GPU-created optimizer state will not load on CPU

A model-only PyTorch checkpoint can be mapped to CPU with
`--num-gpus=0`. Training-state loading has fewer remapping controls. Obtain a
CPU-compatible state artifact or convert it outside the bounded offline check;
do not claim that a successful model load proves GPU optimizer-state
portability. The same boundary applies to Gluon `.states` files.

### An offline command unexpectedly contacts a network

Remove `--use-pretrained` and `--all`, use a locally validated `--data-dir`,
and ensure `--resume FILE` points to a local file. The pretrained provider path
and missing native CIFAR/SVHN caches are the common causes. The dataset checker
itself never contacts a network.

## Optional backend boundary

TensorFlow, Keras, Chainer, legacy Tensorpack, and CUDA- or vendor-specific
behavior are not established by this classification sub-skill. Route those
requests to [framework-compatibility](../../framework-compatibility/SKILL.md).
Do not substitute a CPU Gluon or PyTorch result as proof for an optional
backend. If installation or import work is needed for one of those backends,
record it as an environment requirement before constructing a training command.
