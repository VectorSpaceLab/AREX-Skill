# Evaluation workflows

## Canonical evaluator command

The repository evaluator is invoked as:

```bash
python test.py -net <name> -weights <path> [-gpu] [-b B]
```

Required arguments:

- `-net <name>`: CLI model name accepted by the repository network factory.
- `-weights <path>`: path to a PyTorch state_dict file for that exact architecture.

Optional arguments:

- `-gpu`: disabled by default. When present, the evaluator moves the model, images, and labels to CUDA and prints CUDA memory summaries.
- `-b B`: test dataloader batch size. Default is `16`.

Build commands safely with the bundled helper before running them:

```bash
python skills/disco/pytorch-cifar100/sub-skills/evaluation/scripts/build_eval_command.py \
  --net resnet18 \
  --weights checkpoint/resnet18/<run-folder>/resnet18-200-best.pth \
  --batch-size 16 \
  --explain
```

The helper prints a command; it does not execute evaluation.

## What `test.py` does

The evaluator performs this sequence:

1. Parses `-net`, `-weights`, optional `-gpu`, and optional `-b`.
2. Builds the selected network through the repository network factory. If `-gpu` is set, the model is moved to CUDA during construction.
3. Creates a CIFAR-100 test dataloader using normalized test images from `torchvision.datasets.CIFAR100(root='./data', train=False, download=True)`. The transform is `ToTensor()` plus normalization with the repository CIFAR-100 mean/std constants.
4. Loads the checkpoint with `net.load_state_dict(torch.load(args.weights))`.
5. Prints the network module tree, switches to `eval()`, and enters a `torch.no_grad()` loop over the test loader.
6. For each batch, computes `output.topk(5, dim=1)`, compares top-1 and top-5 predictions against labels, and accumulates correct counts.
7. Prints final Top-1 error, Top-5 error, and raw parameter count.

The test dataloader is constructed with `num_workers=4` and uses the helper's default `shuffle=True`. Because the evaluator aggregates over the full test set, shuffled test order does not change the final error values.

## Metric interpretation

Final stdout contains lines shaped like:

```text
Top 1 err:  <value>
Top 5 err:  <value>
Parameter numbers: <integer>
```

Interpretation:

- `Top 1 err` is `1 - top1_correct / 10000` on the CIFAR-100 test set.
- `Top 5 err` is `1 - top5_correct / 10000`; it should usually be less than or equal to Top-1 error.
- The printed values are fractions. Convert to percentages by multiplying by 100: `0.2439` means `24.39%` Top-1 error and `75.61%` Top-1 accuracy.
- `Parameter numbers` is `sum(p.numel() for p in net.parameters())`; it is a raw count, not millions, memory use, or trainable-only metadata.
- Lower error is better. Compare results only when the checkpoint, net name, dataset split, and preprocessing are the same.

Some PyTorch versions print tensor-like values for the errors. Treat the numeric scalar inside the tensor as the same fraction.

## Data and filesystem side effects

Evaluation does not train or save model weights, but it can modify the working tree:

- CIFAR-100 is downloaded into `./data` relative to the directory where the command is run.
- The first run may require network access and enough disk space for torchvision's CIFAR-100 files.
- Running from the repository root is safest because `test.py` imports local modules and uses a relative `./data` dataset root.
- Checkpoints are not bundled. The user must provide a valid weights path.

## CPU, GPU, and batch-size choices

Default to CPU unless the user explicitly wants CUDA evaluation and the environment has a compatible GPU build of PyTorch.

- **CPU path:** omit `-gpu`. This avoids CUDA availability and memory issues, but large networks can be slow.
- **GPU path:** include `-gpu`. The evaluator will call `.cuda()` on model and tensors and print `torch.cuda.memory_summary()` during and after evaluation. Verify CUDA availability first; otherwise the run will fail early.
- **Batch size:** default is `16`. Larger batches can improve throughput but use more memory; smaller batches are safer for OOM-prone GPUs and memory-constrained CPUs.
- **Workers:** the evaluator hardcodes `num_workers=4`; there is no CLI flag for worker count.

## Validation sequence before running

1. Confirm the target net is one of the evaluator-supported CLI names. Use the helper's `--list-nets` when in doubt.
2. Confirm the weights file exists and is not a directory.
3. Confirm the weights were saved from the same architecture name, for example `resnet18` weights with `-net resnet18`.
4. Prefer a `*-best.pth` checkpoint for final reporting, or a `*-regular.pth` checkpoint when analyzing a specific epoch or when no best checkpoint exists.
5. Decide CPU/GPU and batch size based on hardware, memory, and whether the checkpoint can be deserialized on the target device.
6. Run the printed command from the repository root and watch for an initial CIFAR-100 download.
