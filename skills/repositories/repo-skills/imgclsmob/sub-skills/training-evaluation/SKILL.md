---
name: training-evaluation
description: "Build safe dataset-aware training and evaluation commands for the
  verified Gluon and PyTorch classification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and evaluation

Use this sub-skill when the request concerns ImageNet1K, CIFAR10, CIFAR100,
SVHN, or CUB200_2011 data layout, `train_gl.py`/`eval_gl.py`,
`train_pt.py`/`eval_pt.py`, metrics, batch/device sizing, or checkpoint
resume behavior. This sub-skill documents classification workflows only; do
not turn it into a full training run.

## Route first

- Use [model-inference](../model-inference/SKILL.md) to choose and construct a
  model, select `resnet18`-style names, or diagnose model/checkpoint shape and
  device loading.
- Use [framework-compatibility](../framework-compatibility/SKILL.md) for
  TensorFlow, Keras, Chainer, legacy Tensorpack, or other optional backend
  claims. CPU Gluon and CPU PyTorch/pytorchcv are the verified core; do not
  infer CUDA or optional-backend support from this sub-skill.

## Safe operating procedure

1. Select the exact dataset name and layout. `ImageNet1K` means folder layout;
   `ImageNet1K_rec` is the Gluon-only MXNet record layout. Read
   [datasets and layouts](references/datasets-and-layouts.md).
2. Run the no-network preflight before a real command:

   ```bash
   python scripts/check_dataset_layout.py --dataset ImageNet1K --data-dir /data/imagenet --backend pytorch
   ```

   Replace `/data/imagenet` with the user's local data root. The checker only
   inspects filesystem structure; it never downloads data or imports a
   framework. A nonzero result means stop and fix the root/layout rather than
   launching a CLI.
3. Construct the command from [the CLI reference](references/cli-reference.md).
   Start with `--num-gpus=0`, `--num-data-workers 0`, and a conservative
   `--batch-size` on CPU. Omit `--use-pretrained`, `--all`, and any other
   network-dependent option for offline work. For CIFAR10, CIFAR100, and
   SVHN, an `indeterminate_native_cache` result means only that a local cache
   exists; the selected framework must still verify its cache with downloads
   disabled.
4. Run `--help` first. Help parsing does not construct a model, open a data
   loader, download weights, or start training. Do not use help output as proof
   that a dataset or checkpoint is valid.
5. For evaluation, prefer `--data-subset val` for these classification
   metainfo objects. The scripts use the held-out split for `val`; several
   listed metainfo objects do not define separate `test_metric_names`.
6. Record the selected dataset, root, framework, checkpoint type, device,
   effective batch size, metric names, and validation result. Do not claim an
   accuracy value without running the evaluation against a real local dataset.

## Checkpoint and command boundaries

- Gluon training separates model parameters (`--resume`, normally a
  `.params` file) from optimizer state (`--resume-state`, normally a `.states`
  file). PyTorch evaluation loads a model checkpoint through `--resume`,
  normally `.pth`; PyTorch training uses `--resume-state` for a state object
  containing `epoch`, `state_dict`, and `optimizer`.
- `--start-epoch` is an explicit 1-based control in both training CLIs. Passing
  a state file does not remove the need to choose the intended start epoch.
- A local `--resume` is distinct from `--use-pretrained`: the latter can ask a
  model provider to obtain weights. For no-network operation, use a local
  checkpoint and omit `--use-pretrained`.
- Use [troubleshooting](references/troubleshooting.md) when the layout,
  metric, checkpoint, or CPU/device assumptions fail.

## Output contract

Return a command plan, not a long-running experiment: dataset/layout decision,
preflight result, exact CLI flags, expected metric/checkpoint behavior, and the
next bounded check. Link model construction and optional backend questions as
specified above.
