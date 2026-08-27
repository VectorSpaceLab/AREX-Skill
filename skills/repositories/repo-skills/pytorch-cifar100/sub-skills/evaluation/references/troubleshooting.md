# Evaluation troubleshooting

## Missing or wrong weights path

Symptoms:

- `FileNotFoundError`
- `No such file or directory`
- The command builder rejects the path

Fixes:

1. Check that the user provided a checkpoint file; checkpoints are not bundled.
2. Run the builder without executing evaluation:

   ```bash
   python skills/disco/pytorch-cifar100/sub-skills/evaluation/scripts/build_eval_command.py \
     --net <name> --weights <path> --explain
   ```

3. If you are drafting a command before the checkpoint exists, pass `--allow-missing-weights` to the builder and make the missing-file assumption explicit.
4. Ensure the path points to a `.pth`-style file, not a run folder.

## Unsupported net name

Symptoms:

- The evaluator prints `the network name you have entered is not supported yet` and exits.
- The command builder reports an invalid `--net`.

Fixes:

1. Use the exact CLI names accepted by the repository network factory.
2. Run `--list-nets` on the command builder.
3. Remember that result-table labels are not always CLI names. For example, the evaluator CLI uses names such as `vgg16` and `wideresnet`.
4. Route architecture-selection questions to `model-zoo` when the user is not just fixing a spelling issue.

## Mismatched architecture keys or tensor sizes

Symptoms:

- `Missing key(s) in state_dict`
- `Unexpected key(s) in state_dict`
- `size mismatch`
- Errors mentioning classifier or final-layer shapes

Likely causes:

- `-net` does not match the training architecture.
- The file contains a full training checkpoint dictionary instead of a plain state_dict.
- The state_dict was saved from a DataParallel model and keys are prefixed with `module.`.
- The classifier was changed to a class count other than CIFAR-100's 100 classes.

Fixes:

1. Infer the original net from the checkpoint folder and filename, then rerun with that exact `-net`.
2. If the file is a wrapper checkpoint, extract the nested model state_dict into a separate file before using `test.py`.
3. If keys are prefixed or the classifier was modified, either convert the state_dict to match the repository model or use a matching model definition. Do not silently ignore missing keys for a reported evaluation.

## CIFAR-100 download or dataset failures

Symptoms:

- Network timeout while downloading CIFAR-100.
- Permission errors under `./data`.
- Dataset files appear in an unexpected directory.

Facts and fixes:

- The evaluator uses `torchvision.datasets.CIFAR100(root='./data', train=False, download=True)`.
- Run from the repository root if you want the dataset under the repository's `data` directory.
- If the environment has no internet, pre-populate torchvision's CIFAR-100 layout under `./data` or run once in a network-enabled environment.
- Ensure the process can create and read `./data`.

## CUDA unavailable or out of memory

Symptoms:

- `Torch not compiled with CUDA enabled`
- `CUDA error`
- `RuntimeError: CUDA out of memory`
- Failure when `-gpu` is present

Fixes:

1. Omit `-gpu` for CPU evaluation.
2. Verify `torch.cuda.is_available()` before using GPU.
3. Reduce `-b`; the default `16` is safer than large batches.
4. For CUDA memory pressure, close other GPU processes and rerun with a smaller batch.
5. Expect verbose CUDA memory summaries when `-gpu` is enabled; they are normal unless paired with an error.

## CUDA-saved checkpoint on a CPU-only machine

Symptom:

- Deserialization fails before `load_state_dict`, often with a message about loading a CUDA tensor while CUDA is unavailable.

Cause:

- The evaluator calls `torch.load(args.weights)` without `map_location='cpu'`.

Fixes:

- Evaluate in an environment with CUDA available, or create a CPU-mapped copy of the state_dict in a separate conversion step using a compatible PyTorch install. Keep the converted file separate from the original checkpoint.

## Top-k or output-shape errors

Symptoms:

- `selected index k out of range`
- Shape errors around `output.topk(5, 1, ...)`
- Label expansion or equality comparison errors

Likely causes:

- The model output is not a two-dimensional classification tensor shaped like `[batch, classes]`.
- The model has fewer than 5 classes or was modified away from CIFAR-100 classification.
- The selected architecture returns an unexpected structure instead of logits.

Fixes:

1. Confirm the repository model with the selected net name produces logits for 100 classes.
2. Confirm the checkpoint belongs to the unmodified CIFAR-100 model.
3. Route model-output modification questions to `model-zoo`; do not report Top-1/Top-5 metrics from an incompatible output shape.

## Torch serialization compatibility

Symptoms:

- Errors or warnings from `torch.load` on newer or older PyTorch versions.
- Security warnings about pickle-backed loading.
- Failures after moving checkpoints across PyTorch releases.

Fixes:

1. Prefer evaluating with a PyTorch/torchvision pair compatible with the one used to save the checkpoint.
2. If conversion is necessary, load the checkpoint in a trusted environment and save a plain state_dict compatible with the evaluator.
3. Treat untrusted checkpoint files as executable pickle input; only load checkpoints from trusted sources.
