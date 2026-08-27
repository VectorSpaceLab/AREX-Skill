# CNN DARTS workflows

These recipes are self-contained command-planning notes for the convolutional DARTS workflows. They summarize source-backed behavior from the public CNN README commands and the CNN runner scripts. Commands are conceptual native DARTS commands: assume they are run from a compatible legacy environment with CUDA and from the project root unless the command itself changes into `cnn/`.

Use the root command planner `../../../scripts/darts_command_builder.py` from this reference directory, or `scripts/darts_command_builder.py` from the skill root, to assemble prerequisite-aware commands. Do not copy the original long runner scripts into runtime output.

## Common preflight checklist

1. **Runtime:** Python from the legacy era, PyTorch 0.3.1, torchvision 0.2.0, and CUDA. The CNN scripts call `.cuda(async=True)`, `Variable(..., volatile=True)`, and `loss.data[0]`; modern Python/PyTorch will fail or require a port.
2. **GPU:** Every CNN runner exits early if `torch.cuda.is_available()` is false. CPU-only execution is not a faithful native path.
3. **Working directory:** The documented commands enter `cnn/`. Defaults such as `--data ../data` and `--data ../data/imagenet/` are relative to that directory.
4. **Data:** CIFAR-10 can be downloaded by torchvision into `--data`; ImageNet must already exist as `--data/train/<class>/...` and `--data/val/<class>/...`.
5. **Architecture name:** `--arch` is evaluated as a variable in the CNN genotype module. Built-in CNN default is `DARTS`, an alias for `DARTS_V2`. For catalog/schema work, route to `../genotypes-and-visualization/`.
6. **Checkpoint kind:** CIFAR `test.py` expects a raw model state dict. ImageNet `test_imagenet.py` expects a checkpoint dictionary containing `state_dict`.
7. **Budget:** Full CIFAR training defaults to 600 epochs; ImageNet training defaults to 250 epochs. Smoke commands only validate wiring and should not be reported as paper metrics.

## Workflow decision table

| Goal | Native runner | Dataset | Default model scale | Main outputs | Expected paper signal |
| --- | --- | --- | --- | --- | --- |
| Search for a CNN cell | `train_search.py` | CIFAR-10 train split | `init_channels=16`, `layers=8`, `epochs=50` | `search-*/log.txt`, copied scripts, `weights.pt`, logged genotypes | Logs validation accuracy during search, but this is not final architecture quality. |
| Train/evaluate a fixed CNN genotype on CIFAR-10 | `train.py` | CIFAR-10 train/test | `init_channels=36`, `layers=20`, `epochs=600` | `eval-*/log.txt`, copied scripts, `weights.pt` | README expects average test error around `2.76 +/- 0.09%` over 10 independent runs for the best cell. |
| Evaluate a pretrained CIFAR-10 CNN | `test.py` | CIFAR-10 test | `init_channels=36`, `layers=20` | `test_acc` log | README reports `2.63%` test error and `3.3M` params for the pretrained CIFAR model. |
| Train a fixed CNN genotype on ImageNet | `train_imagenet.py` | ImageNet train/val folders | `init_channels=48`, `layers=14`, `epochs=250` | `eval-*/checkpoint.pth.tar`, `model_best.pth.tar`, log | Long native training; README primarily documents the pretrained ImageNet evaluation metric. |
| Evaluate a pretrained ImageNet CNN | `test_imagenet.py` | ImageNet val folder | `init_channels=48`, `layers=14` | `valid_acc_top1`, `valid_acc_top5` logs | README reports `26.7%` top-1 error and `8.7%` top-5 error, i.e. about `73.3%` top-1 and `91.3%` top-5 accuracy, with `4.7M` params. |

## CIFAR-10 architecture search

### Standard command

```bash
cd cnn && python train_search.py --unrolled
```

Add explicit paths and GPU when presenting a reproducible plan:

```bash
cd cnn && python train_search.py \
  --data ../data \
  --gpu 0 \
  --save EXP \
  --seed 2 \
  --unrolled
```

### Important defaults

| Flag | Default | Effect |
| --- | --- | --- |
| `--data` | `../data` | CIFAR-10 root; torchvision downloads train data if missing. |
| `--batch_size` | `64` | Batch size for both training and validation queues. |
| `--epochs` | `50` | Number of search epochs. |
| `--init_channels` | `16` | Initial search-network channel count. |
| `--layers` | `8` | Number of search cells. |
| `--train_portion` | `0.5` | First half of CIFAR train indices forms the weight-training queue; second half forms the architecture-validation queue. |
| `--learning_rate` / `--learning_rate_min` | `0.025` / `0.001` | SGD cosine-annealed weight learning rate. |
| `--momentum` / `--weight_decay` | `0.9` / `3e-4` | SGD weight optimizer settings. |
| `--arch_learning_rate` / `--arch_weight_decay` | `3e-4` / `1e-3` | Adam settings for architecture parameters. |
| `--unrolled` | off unless set | Uses one-step unrolled validation loss and a Hessian-vector product; increases memory. |
| `--grad_clip` | `5` | Clips weight gradients. |
| `--cutout` / `--cutout_length` | off / `16` | Search script accepts the flag and applies Cutout through CIFAR transforms when enabled. |
| `--save` | `EXP` | Expanded to `search-EXP-<timestamp>`. |
| `--report_freq` | `50` | Log interval in steps. |

### Expected output and interpretation

- Creates `search-<name>-<timestamp>/` with `log.txt`, a `scripts/` copy of local CNN scripts, and `weights.pt` saved each epoch.
- Logs GPU id, parsed args, model parameter size, epoch learning rate, current genotype, architecture softmax weights, `train_acc`, and `valid_acc`.
- The architecture returned by `model.genotype()` is a candidate cell. The README warns that search validation performance does **not** indicate final architecture performance. Train the chosen genotype from scratch before drawing conclusions.
- Different seeds may converge to different local optima. For paper-like selection, repeat search with multiple seeds and compare cells by later evaluation, not by a single search log.

### Safe validation command

Only run this in a compatible legacy CUDA runtime. It validates data loading, CUDA, architecture update wiring, logging, and checkpoint creation; it does not validate paper performance.

```bash
cd cnn && python train_search.py \
  --epochs 1 \
  --batch_size 8 \
  --train_portion 0.1 \
  --report_freq 1 \
  --save smoke \
  --gpu 0
```

If memory is tight, omit `--unrolled` for smoke validation because the default first-order architecture step is cheaper.

## CIFAR-10 fixed-genotype training/evaluation

### Standard command

```bash
cd cnn && python train.py --auxiliary --cutout
```

Explicit command for a named genotype:

```bash
cd cnn && python train.py \
  --data ../data \
  --arch DARTS \
  --auxiliary \
  --cutout \
  --gpu 0 \
  --save EXP \
  --seed 0
```

### Important defaults

| Flag | Default | Effect |
| --- | --- | --- |
| `--arch` | `DARTS` | Fixed CNN genotype variable consumed by the evaluation network. |
| `--data` | `../data` | CIFAR-10 train and test roots; torchvision downloads both splits if missing. |
| `--batch_size` | `96` | Full-evaluation batch size. |
| `--epochs` | `600` | Full CIFAR training schedule length. |
| `--init_channels` | `36` | Initial channel count for the fixed CIFAR network. |
| `--layers` | `20` | Number of cells. Reduction cells occur near one-third and two-thirds depth. |
| `--learning_rate` | `0.025` | SGD initial learning rate with cosine annealing over all epochs. |
| `--momentum` / `--weight_decay` | `0.9` / `3e-4` | SGD optimizer settings. |
| `--auxiliary` / `--auxiliary_weight` | off / `0.4` | Adds an auxiliary classifier at two-thirds depth during training and adds weighted auxiliary loss. README enables it. |
| `--cutout` / `--cutout_length` | off / `16` | Adds Cutout after CIFAR normalization in the training transform. README enables it. |
| `--drop_path_prob` | `0.2` | Linearly ramped from 0 to the flag value across epochs. |
| `--grad_clip` | `5` | Clips gradients. |
| `--save` | `EXP` | Expanded to `eval-EXP-<timestamp>`. |

### Expected output and interpretation

- Creates `eval-<name>-<timestamp>/` with `log.txt`, copied scripts, and `weights.pt` saved each epoch as a raw state dict.
- Logs `train_acc` and `valid_acc` against CIFAR test data in each epoch.
- README expectation for the best cell is an average test error around `2.76 +/- 0.09%` over 10 independent runs. Because cuDNN back-prop kernels are nondeterministic, a single run is not a reliable result.

### Safe validation command

Only run in a compatible legacy CUDA runtime. This checks the fixed-genotype network path and output files, not accuracy.

```bash
cd cnn && python train.py \
  --epochs 1 \
  --batch_size 8 \
  --init_channels 8 \
  --layers 4 \
  --arch DARTS \
  --save smoke \
  --report_freq 1 \
  --gpu 0
```

For a closer workflow smoke, add `--auxiliary --cutout`, but remember auxiliary heads add memory and checkpoint keys.

## CIFAR-10 pretrained evaluation

### Standard command

```bash
cd cnn && python test.py --auxiliary --model_path cifar10_model.pt
```

Recommended explicit form:

```bash
cd cnn && python test.py \
  --data ../data \
  --arch DARTS \
  --auxiliary \
  --model_path cifar10_model.pt \
  --gpu 0
```

### Important defaults

| Flag | Default | Effect |
| --- | --- | --- |
| `--model_path` | `EXP/model.pt` | Path to a raw `state_dict`; README uses `cifar10_model.pt`. |
| `--arch` | `DARTS` | Must match the genotype used by the checkpoint. |
| `--init_channels` / `--layers` | `36` / `20` | Must match the checkpoint. |
| `--auxiliary` | off unless set | Must match checkpoint module keys for pretrained models that include the auxiliary head. README enables it. |
| `--drop_path_prob` | `0.2` | Assigned before evaluation; has no effect while `model.eval()` disables drop-path logic. |
| `--cutout` | off | Accepted for transform construction, but test transform does not use Cutout. |

### Expected output

- Logs model parameter size and `test_acc`.
- README reports `2.63%` test error, equivalent to about `97.37%` top-1 accuracy, with `3.3M` parameters.

### Safe validation

A valid checkpoint is required. First check that the file exists and that it is a raw state dict for the same `--arch`, `--init_channels`, `--layers`, and auxiliary setting. Running without the checkpoint only validates argument parsing if the legacy interpreter can parse the script.

## ImageNet fixed-genotype training

### Standard command

```bash
cd cnn && python train_imagenet.py --auxiliary
```

Recommended explicit form:

```bash
cd cnn && python train_imagenet.py \
  --data ../data/imagenet/ \
  --arch DARTS \
  --auxiliary \
  --gpu 0 \
  --save EXP \
  --seed 0
```

### Important defaults

| Flag | Default | Effect |
| --- | --- | --- |
| `--data` | `../data/imagenet/` | Must contain `train/` and `val/` ImageFolder class subdirectories. |
| `--batch_size` | `128` | Large default; reduce for smoke or small GPUs. |
| `--epochs` | `250` | Full ImageNet schedule length. |
| `--init_channels` / `--layers` | `48` / `14` | ImageNet network scale. |
| `--learning_rate` | `0.1` | SGD initial learning rate. |
| `--weight_decay` | `3e-5` | ImageNet-specific weight decay. |
| `--gamma` / `--decay_period` | `0.97` / `1` | StepLR multiplicative decay every epoch by default. |
| `--label_smooth` | `0.1` | Training loss uses label-smoothed cross entropy. |
| `--auxiliary` / `--auxiliary_weight` | off / `0.4` | README enables auxiliary tower. |
| `--drop_path_prob` | `0` | Defaults to no drop path unless explicitly set; if set, it is linearly ramped by epoch. |
| `--parallel` | off | Wraps model in `DataParallel` for training when enabled. Watch checkpoint key prefixes. |

### Expected output

- Creates `eval-<name>-<timestamp>/` with `log.txt`, copied scripts, `checkpoint.pth.tar`, and `model_best.pth.tar` when validation top-1 improves.
- Logs `valid_acc_top1` and `valid_acc_top5` each epoch.
- Native full training is expensive and dataset-dependent; do not report a smoke run as an ImageNet result.

### Safe validation command

Only run with a tiny ImageNet-like ImageFolder dataset or the real dataset in a compatible legacy CUDA runtime. It validates transforms, forward/backward, checkpoint writing, and class-folder layout.

```bash
cd cnn && python train_imagenet.py \
  --data ../data/imagenet/ \
  --epochs 1 \
  --batch_size 4 \
  --init_channels 8 \
  --layers 2 \
  --arch DARTS \
  --save smoke \
  --report_freq 1 \
  --gpu 0
```

Use an even `--init_channels` value because the ImageNet stem uses `C // 2` channels in its first convolution.

## ImageNet pretrained evaluation

### Standard command

```bash
cd cnn && python test_imagenet.py --auxiliary --model_path imagenet_model.pt
```

Recommended explicit form:

```bash
cd cnn && python test_imagenet.py \
  --data ../data/imagenet/ \
  --arch DARTS \
  --auxiliary \
  --model_path imagenet_model.pt \
  --gpu 0
```

### Important defaults

| Flag | Default | Effect |
| --- | --- | --- |
| `--model_path` | `EXP/model.pt` | Path to a checkpoint dictionary containing `state_dict`. |
| `--arch` | `DARTS` | Must match the checkpoint genotype. |
| `--init_channels` / `--layers` | `48` / `14` | Must match the checkpoint. |
| `--auxiliary` | off unless set | Must match checkpoint keys; README enables it for pretrained model evaluation. |
| `--drop_path_prob` | `0` | Set before evaluation, but drop-path is inactive under `model.eval()`. |

### Expected output

- Logs parameter size, `valid_acc_top1`, and `valid_acc_top5` over the ImageNet validation set.
- README reports `26.7%` top-1 error and `8.7%` top-5 error, approximately `73.3%` top-1 and `91.3%` top-5 accuracy, with `4.7M` parameters.

## Custom CNN genotype workflow

1. Convert the searched or hand-designed CNN cell to a CNN `Genotype` with `normal`, `normal_concat`, `reduce`, and `reduce_concat` fields. Route catalog and schema questions to `../genotypes-and-visualization/`.
2. Add or select a genotype variable name that is visible to the native CNN runners.
3. Use `--arch <NAME>` consistently in `train.py`, `test.py`, `train_imagenet.py`, or `test_imagenet.py`.
4. Keep the model scale and auxiliary setting consistent between training and testing checkpoints.
5. Do not reuse RNN genotype schemas in CNN runners; they are incompatible.

## Reporting guidance

- Search logs are architecture-selection evidence, not final model evidence.
- CIFAR-10 final numbers should be reported across multiple independent training runs because the README explicitly warns about variance from nondeterministic cuDNN back-prop kernels.
- Pretrained metrics require the external pretrained files and exact model settings. If the checkpoint is unavailable, report the planned command and missing artifact rather than inventing a result.
- For modernized ports, clearly separate source-backed original behavior from port-specific modifications.
