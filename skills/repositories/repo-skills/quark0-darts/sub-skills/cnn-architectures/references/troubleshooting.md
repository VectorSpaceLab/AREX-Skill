# CNN DARTS troubleshooting

Use this matrix for convolutional DARTS search, CIFAR-10 train/test, and ImageNet train/test failures. Cross-cutting setup guidance belongs in root references when available; this file focuses on CNN-specific symptoms and source-backed causes.

## Fast triage by symptom

| Symptom | Likely cause | What to tell the user |
| --- | --- | --- |
| `SyntaxError` points at `async=True` | Modern Python treats `async` as a reserved keyword; the native scripts were written for legacy PyTorch/Python syntax. | This is a legacy-runtime or porting issue, not a data/checkpoint issue. Use a compatible legacy runtime or port all deprecated PyTorch constructs, not only this one keyword. |
| `no gpu device available` then exit | Runner checks `torch.cuda.is_available()` and exits. | Native CNN workflows require CUDA. CPU-only is not a faithful execution path. |
| Import/API errors involving `Variable`, `volatile`, `.data[0]`, `clip_grad_norm`, or `.cuda(async=True)` | Modern PyTorch API incompatibility. | The source targets PyTorch 0.3.1/torchvision 0.2.0. A modern port must update several APIs together. |
| Out-of-memory during search, especially with `--unrolled` | Second-order unrolled search builds an unrolled model and Hessian-vector product path; default batch size may be too large. | For smoke, omit `--unrolled` or reduce `--batch_size`, `--init_channels`, and `--layers`. For real paper-like search, use adequate legacy CUDA memory. |
| Out-of-memory during CIFAR/ImageNet training | Large defaults: CIFAR `batch_size=96`, `layers=20`, `init_channels=36`; ImageNet `batch_size=128`, `layers=14`, `init_channels=48`; auxiliary head and drop-path training add memory. | Reduce batch size first. For smoke only, reduce channels/layers/epochs. Do not compare smoke metrics to paper metrics. |
| CIFAR download or data errors | CIFAR root is `--data`, default `../data` relative to `cnn/`; torchvision download may fail or be unavailable. | Verify working directory, writable data root, network/cache state, and torchvision legacy compatibility. |
| ImageNet `FileNotFoundError`, empty dataset, or class-index errors | ImageNet must be an ImageFolder tree with `train/` and `val/` class subdirectories. | Create `--data/train/<class>/...` and `--data/val/<class>/...`; the scripts do not download ImageNet. |
| CIFAR checkpoint load has missing/unexpected keys | `test.py` expects a raw state dict matching `--arch`, `--init_channels`, `--layers`, and `--auxiliary`. | Use the same settings as training/pretrained README. Pretrained CIFAR command uses `--auxiliary`. |
| ImageNet checkpoint load errors with `state_dict` | `test_imagenet.py` expects a dictionary checkpoint containing a `state_dict` key. | Do not pass a raw CIFAR-style state dict. For DataParallel-trained checkpoints, handle `module.` prefixes if needed. |
| `NameError` or attribute error for `--arch` | The runner evaluates `genotypes.<arch>` and the variable is missing or misspelled. | Select an existing CNN genotype or add a valid CNN genotype. Route schema/catalog details to `../genotypes-and-visualization/`. |
| `KeyError` in operations registry | Genotype contains an operation name not in the CNN `OPS` registry. | Use supported CNN op names. Remember search primitives are a subset of the fixed-genotype operation registry. |
| `AttributeError: ... drop_path_prob` in manual model use | The fixed networks expect the caller to assign `model.drop_path_prob`; runner scripts do this before forward passes. | Set `model.drop_path_prob = 0.0` for evaluation or a scheduled value for training before calling the model. |
| Single-run CIFAR result differs from README | cuDNN back-prop nondeterminism and search/training variance. | Report multiple independent runs. README says a single CIFAR training run is misleading. |

## Legacy Python/PyTorch/CUDA constraints

The CNN scripts are source-compatible with the original legacy stack, not with modern default ML environments.

Source-backed legacy constructs include:

- `.cuda(async=True)` for non-blocking transfers. This is a syntax error in modern Python.
- `Variable(..., volatile=True)` for inference.
- `loss.data[0]` and `prec1.data[0]` scalar extraction.
- `nn.utils.clip_grad_norm(...)` old naming/API behavior.
- Drop-path masks allocated as `torch.cuda.FloatTensor(...)`, making drop-path CUDA-specific.
- Global CUDA assumptions such as `torch.cuda.set_device(args.gpu)` and early exit when no GPU exists.

If the user asks for a modern port, advise that replacing `async=True` with `non_blocking=True` is only one step. A complete port also needs modern autograd/no-grad handling, scalar extraction, checkpoint compatibility checks, and memory retuning. Keep port-specific guidance separate from source-backed original behavior.

The README explicitly names PyTorch 0.3.1 and torchvision 0.2.0 and warns that PyTorch 0.4 is unsupported and would lead to OOM. Treat this as a strong runtime compatibility constraint.

## CUDA and device failures

### `no gpu device available`

All CNN runners begin with a CUDA availability check and exit if false. Do not recommend CPU-only native runs for the original scripts.

### Invalid GPU id

The scripts call `torch.cuda.set_device(args.gpu)` with default GPU `0`. If the host has fewer GPUs, the user must select a valid id. In multi-process or shared hosts, also ensure the process sees the intended device.

### cuDNN nondeterminism

The scripts set `cudnn.benchmark = True`, seed NumPy, seed PyTorch, and seed CUDA, but the README still warns that CIFAR-10 final results vary due to nondeterministic cuDNN back-prop kernels. Seeds do not make a single run paper-representative.

## CIFAR-10 data issues

Native CIFAR runners use torchvision `CIFAR10` with `download=True`:

- `train_search.py` downloads/uses only the training split, then splits indices by `--train_portion` into weight-training and architecture-validation queues.
- `train.py` downloads/uses the training split for training and the test split for validation logging.
- `test.py` downloads/uses the test split.

Common fixes:

1. Confirm the command is run from `cnn/` or use an explicit `--data` path.
2. Confirm the data root is writable for download/extraction.
3. If the host blocks network downloads, pre-stage CIFAR-10 in the expected torchvision layout or use a cache compatible with the legacy torchvision version.
4. Do not interpret CIFAR `valid_acc` in `train.py` as a held-out validation split; it is measured on the CIFAR test split in the source runner.

## ImageNet data issues

ImageNet runners use torchvision `ImageFolder` and never download the dataset.

Expected layout under `--data`:

```text
imagenet/
  train/
    class_a/
      image1.JPEG
      ...
    class_b/
      ...
  val/
    class_a/
      image1.JPEG
      ...
    class_b/
      ...
```

Troubleshooting points:

- `train_imagenet.py` reads both `train/` and `val/`.
- `test_imagenet.py` reads only `val/`.
- The validation transform assumes normal ImageNet-sized images: resize to 256, center crop 224.
- The ImageNet network ends in `AvgPool2d(7)`, so unusual input sizes can break shape assumptions.
- The README recommends manually preparing ImageNet, preferably on SSD. Slow disks can bottleneck training.

## Pretrained checkpoint failures

### CIFAR pretrained evaluation

Documented command:

```bash
cd cnn && python test.py --auxiliary --model_path cifar10_model.pt
```

Requirements:

- The file must be a raw model state dict, not a checkpoint dictionary.
- `--arch` should match the pretrained genotype; README default is `DARTS`.
- `--init_channels=36` and `--layers=20` should match the pretrained model.
- `--auxiliary` should be enabled for the README pretrained model because checkpoint keys may include the auxiliary tower.

If the user sees missing or unexpected keys, compare these settings first. If the file is missing, report the missing external pretrained artifact rather than trying to train a replacement.

### ImageNet pretrained evaluation

Documented command:

```bash
cd cnn && python test_imagenet.py --auxiliary --model_path imagenet_model.pt
```

Requirements:

- The file must be a checkpoint dictionary with a `state_dict` field.
- `--arch DARTS`, `--init_channels=48`, `--layers=14`, and `--auxiliary` should match the README pretrained model.
- The validation set must exist under `--data/val`.

If a checkpoint was produced by `train_imagenet.py --parallel`, its state dict may have DataParallel `module.` prefixes. The native `test_imagenet.py` does not wrap the model in DataParallel, so key-prefix conversion may be required before loading.

## OOM and memory tuning

### Search OOM

Most likely causes:

- `--unrolled` is enabled, which constructs an unrolled model and uses a Hessian-vector product.
- Batch size is too high for the GPU.
- Legacy PyTorch memory behavior differs from modern expectations.

Tuning order:

1. For a smoke run, remove `--unrolled`.
2. Reduce `--batch_size`.
3. Reduce `--init_channels` or `--layers` only for smoke/debugging, not for paper-comparable search.
4. Keep CUDA memory clear between failed runs.

### CIFAR training OOM

Tuning order:

1. Reduce `--batch_size` below the default 96.
2. Disable `--auxiliary` for a wiring smoke if checkpoint compatibility is not being tested.
3. Reduce `--init_channels` or `--layers` only for smoke/debugging.
4. Keep `--cutout` decisions separate from memory; Cutout is an augmentation, not the main memory driver.

### ImageNet training OOM

Tuning order:

1. Reduce `--batch_size` below the default 128.
2. Consider `--parallel` only if multiple legacy-compatible GPUs are available and checkpoint prefix handling is acceptable.
3. Reduce `--init_channels` or `--layers` only for smoke/debugging.
4. Avoid claiming paper ImageNet results from small-scale smoke settings.

## Auxiliary, Cutout, and drop-path confusion

### Auxiliary towers

- CIFAR and ImageNet fixed networks create auxiliary heads only when `--auxiliary` is set.
- During training, the auxiliary loss is added with `--auxiliary_weight` default `0.4`.
- During evaluation, the network still returns `(logits, logits_aux)`, but `logits_aux` is ignored.
- Checkpoint compatibility can depend on whether the auxiliary modules existed when the checkpoint was saved. README pretrained evaluation enables `--auxiliary` for both CIFAR and ImageNet.

### Cutout

- Cutout exists only in the CIFAR transform helper.
- `--cutout` affects CIFAR training transforms and, through transform construction, can be accepted by search/train/test scripts.
- The CIFAR validation/test transform does not apply Cutout.
- ImageNet runners do not use the CIFAR Cutout helper.

### Drop path

- Fixed-genotype cells apply drop path only during training and only to non-identity operations.
- CIFAR training linearly ramps `model.drop_path_prob` from 0 to `--drop_path_prob` across epochs; default max is `0.2`.
- ImageNet training also linearly ramps if `--drop_path_prob` is set, but the default is `0`.
- Test scripts assign `model.drop_path_prob`, then call `model.eval()`, so drop path is inactive.
- Manual model use must set `drop_path_prob` before forward.

## Genotype and architecture-name errors

The native runners use `eval("genotypes.%s" % args.arch)`. Consequences:

- Misspelled names fail at runtime.
- Names must be CNN genotype variables, not RNN genotypes.
- A genotype edge op name must exist in the CNN operations registry.
- Search-derived genotypes have normal/reduce cells and concat lists; fixed networks expect those exact fields.

Route detailed schema/catolog/DOT questions to `../genotypes-and-visualization/`.

## Metric interpretation mistakes

- `train_search.py` validation accuracy is measured on a split of CIFAR training data and is used for architecture optimization. It is not a final model metric.
- `train.py` logs `valid_acc` on CIFAR test data in the source runner. For rigorous studies, reserve a true validation protocol rather than repeatedly selecting on the test set.
- README CIFAR result guidance is statistical: `2.76 +/- 0.09%` average test error over 10 independent runs. Do not claim this from one run.
- README pretrained CIFAR metric is `2.63%` test error with `3.3M` parameters.
- README pretrained ImageNet metric is `26.7%` top-1 error and `8.7%` top-5 error with `4.7M` parameters.

## Safe response patterns

When a future user asks for help, choose one of these patterns:

- **Modern syntax failure:** "This fails before training because the script uses legacy PyTorch syntax (`async=True`). Use a legacy runtime or plan a full port; data/checkpoints are not the first issue."
- **Missing GPU:** "The native CNN runner exits without CUDA. We can build a command and inspect files, but not run the original workflow faithfully on CPU."
- **Checkpoint mismatch:** "First identify whether this is CIFAR raw state dict or ImageNet checkpoint dict, then align `--arch`, channels, layers, and auxiliary setting."
- **Search-to-train question:** "Use search to produce/select a genotype, then train that genotype from scratch with `train.py`; do not report search validation as final performance."
- **Full-result request without artifacts:** "The planned command is source-backed, but the metric requires the external dataset/checkpoint and legacy CUDA runtime. Report those gaps explicitly."
