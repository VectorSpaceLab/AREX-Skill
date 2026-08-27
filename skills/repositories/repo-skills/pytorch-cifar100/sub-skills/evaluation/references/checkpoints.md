# Checkpoints for evaluation

## Where training writes checkpoints

Training saves state_dict files under the relative checkpoint root configured as:

```text
checkpoint/<net>/<timestamp>/<net>-<epoch>-<type>.pth
```

Distilled checkpoint facts:

- `checkpoint` is the configured checkpoint root.
- `<net>` is the CLI net argument used for training, such as `vgg16`, `resnet18`, or `mobilenetv2`.
- `<timestamp>` is a run folder formatted from the training start time.
- `<epoch>` is the integer epoch number.
- `<type>` is either `best` or `regular`.
- Regular checkpoints are written every `SAVE_EPOCH=10` epochs.
- Best checkpoints are written after the second learning-rate milestone (`epoch > 120` with the default milestones `[60, 120, 160]`) whenever validation accuracy improves.
- The default training schedule is `EPOCH=200`, so final-run candidates often include late regular checkpoints and one or more best checkpoints.

The README's test example uses a user-supplied path:

```bash
python test.py -net vgg16 -weights path_to_vgg16_weights_file
```

No pretrained checkpoint is bundled by this skill or by the evaluator workflow.

## Expected file content

The evaluator expects a plain PyTorch state_dict compatible with the selected model:

```python
net.load_state_dict(torch.load(args.weights))
```

Training saves exactly `net.state_dict()` with `torch.save(net.state_dict(), weights_path)`. The evaluator does not expect a wrapper dictionary containing optimizer state, epoch, scheduler state, or nested `model` keys. It also does not rewrite key names.

Expected properties of a good evaluation checkpoint:

- It is a readable file, not a directory.
- It contains tensor keys matching the model created by the selected `-net` argument.
- It targets 100 CIFAR-100 classes, matching the repository models' default outputs.
- It was not saved from a different architecture, a DataParallel wrapper with `module.` prefixes, or a modified classifier head unless the evaluator model is modified in the same way.

## Architecture and weights matching

The most important validation rule is: **the `-net` value must match the architecture that produced the state_dict**.

Examples:

- Use `-net resnet18` for a checkpoint saved from training with `-net resnet18`.
- Use `-net vgg16` for the repository's VGG16-BN implementation, because the CLI name is `vgg16` even though the factory constructs a batch-normalized VGG16 variant.
- Use `-net wideresnet` for the repository's WideResNet CLI name; result tables may describe it more specifically, but the evaluator accepts the CLI name.

When the checkpoint path follows the training pattern, infer the likely net from both the parent folder and the filename prefix. If they disagree, ask the user which architecture actually produced the weights before running evaluation.

For a full list of accepted evaluator names, run:

```bash
python skills/disco/pytorch-cifar100/sub-skills/evaluation/scripts/build_eval_command.py --list-nets
```

## Choosing best versus regular checkpoints

Use this decision order:

1. **Final model reporting:** prefer the latest `*-best.pth` in the intended run folder. Best checkpoints are saved when test accuracy improves after the default mid-training milestone.
2. **Epoch-specific analysis:** use the matching `*-regular.pth` for that epoch.
3. **No best file exists:** use the latest regular checkpoint, but report that it is not a best-accuracy checkpoint.
4. **Multiple run folders exist:** choose the run folder intentionally; the newest folder is not automatically the best experiment.

The repository helper for best checkpoints chooses the latest `best` file by epoch within a folder. The helper for most-recent weights chooses the highest-epoch matching file. Evaluation itself does not perform this selection; the user passes a concrete `-weights` path.

## Safe storage and path cautions

- Keep user checkpoints outside generated skill files; do not embed weights in documentation or scripts.
- Quote paths that contain spaces when running shell commands.
- Prefer a stable checkpoint copy for published evaluation so future training does not overwrite or delete it.
- Avoid committing large checkpoint files or downloaded CIFAR-100 data unless the project explicitly wants them versioned.
- When evaluating from outside the repository root, remember that `test.py` still uses local imports and the relative dataset root `./data`; changing the working directory changes where CIFAR-100 downloads.
- A CUDA-saved state_dict may require CUDA during `torch.load` because the evaluator does not pass `map_location`. If evaluating on a CPU-only machine fails during deserialization, create a CPU-mapped copy in a separate conversion step or evaluate in a CUDA-capable environment.
