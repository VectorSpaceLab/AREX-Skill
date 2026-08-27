# Training troubleshooting

## Required CUDA paths

Symptoms:

- `AssertionError: Torch not compiled with CUDA enabled`
- `RuntimeError: CUDA error ...`
- Failure soon after trainer construction or display batch creation

Training has no CPU flag. It calls `.cuda()` on the trainer, fixed display tensors, each batch, MUNIT style tensors, UNIT noise tensors, CUDA synchronization, and VGG preprocessing tensors. Use `../environment-and-setup/` to verify the legacy CUDA/PyTorch runtime before launching. Do not attempt a full training run as a parser or static check.

## Missing or invalid config

Symptoms:

- `FileNotFoundError` or `IOError` for the YAML path
- YAML loader error before trainer construction
- `KeyError` for a config key such as `max_iter`, `display_size`, `gen`, `dis`, or a loss weight
- Modern PyYAML error similar to `load() missing 1 required positional argument: 'Loader'`

Actions:

1. Use the dry-run helper to check the config path and required keys.
2. Route schema/path repair to `../data-and-configuration/`.
3. Keep all common keys when reducing a config for smoke testing.
4. For `--trainer UNIT`, add UNIT KL keys (`recon_kl_w`, `recon_kl_cyc_w`) and verify architecture compatibility; the bundled demo configs are MUNIT-oriented.
5. For PyYAML compatibility, prefer a legacy-compatible environment or a minimal local patch to use safe loading only after the user accepts code changes.

## `display_size` larger than dataset

Symptoms:

- `IndexError` during startup while creating display batches
- Failure before the first training iteration even though data loaders were created

The entrypoint indexes `dataset[i]` for `i in range(display_size)` on train and test datasets for both domains. Set `display_size` no larger than each of `trainA`, `trainB`, `testA`, and `testB` lengths. This is independent of `batch_size`. For full dataset counting and list-file repair, use `../data-and-configuration/`.

## Resume cannot find checkpoints

Symptoms:

- `TypeError`, `NoneType`, or file-load error from attempting to load the latest generator/discriminator
- `FileNotFoundError` for `optimizer.pt`
- Resume starts from the wrong iteration

Actions:

1. Confirm `--output_path` and the current config filename stem recreate the previous output directory.
2. Confirm `outputs/<model_name>/checkpoints` exists below that output root.
3. Confirm matching `gen_XXXXXXXX.pt`, `dis_XXXXXXXX.pt`, and `optimizer.pt` files exist.
4. Avoid renaming snapshots without preserving the eight-digit suffix.
5. Do not resume a `MUNIT` trainer from `UNIT` checkpoints, or from a config with changed generator/discriminator dimensions.

## VGG model side effects when `vgg_w > 0`

Symptoms:

- Training attempts a network command for VGG weights.
- Failure mentioning `vgg16.t7`, `vgg16.weight`, `load_lua`, Dropbox, or `wget`.
- Import failure for `torch.utils.serialization.load_lua` in modern PyTorch.

When `vgg_w` is positive, trainer construction calls a VGG loader rooted at `<output_path>/models`. If `vgg16.weight` is absent and `vgg16.t7` is absent, the legacy helper attempts to run `wget` to fetch the Torch7 model before converting it. For restricted or offline runs, either set `vgg_w: 0` or prepare the expected VGG file under the run output root before launch. Runtime setup and legacy compatibility belong to `../environment-and-setup/`.

## Logs or outputs are not where expected

Symptoms:

- Tensorboard shows no events in the checked directory.
- Images or checkpoints appear under `./outputs` instead of the intended run directory.
- Resume fails after changing only the output path.

Actions:

- Remember `--output_path` is the run root, not the final model directory.
- The model subdirectory is the config filename stem.
- Use a dedicated explicit output path for every experiment.
- Keep the same `--output_path` and config stem for resume, or copy the previous output subtree into the new location.

## `tensorboardX` import failure

Symptoms:

- Immediate import error before help/training completes.
- No training loop is entered.

The training entrypoint imports `tensorboardX` at module import time. Install or activate the legacy environment that includes `tensorboardX`, or route environment repair to `../environment-and-setup/`. The dry-run helper does not import `tensorboardX` and can still build commands for review.

## Old PyTorch/runtime warnings

Expected classes of warnings in non-original runtimes:

- Learning-rate scheduler ordering warnings in modern PyTorch because the loop calls scheduler steps before optimizer steps in each iteration.
- Deprecated `Variable` usage warnings.
- PyYAML loader warnings or errors depending on PyYAML version.
- Removed Torch7 loader APIs if VGG conversion is triggered.
- CUDA capability/runtime mismatches on newer GPUs when using the old PyTorch/CUDA baseline.

Treat warnings as evidence of legacy-runtime mismatch unless they are known benign in the chosen environment. Do not silence them by launching a full run; first decide whether to use the documented legacy stack, containerize, or patch for modernization.

## Demo script hazards

The demo shell workflows are not safe validation commands. They may remove dataset directories, download archives, extract files, crop images with ImageMagick, and start full training. Use them only as reference recipes and adapt their final `python train.py --config ...` command through the dry-run helper.

## CUDA memory pressure

Symptoms:

- Out-of-memory during display sampling, generator/discriminator update, or VGG loss.

Levers:

- Reduce `batch_size`.
- Reduce `display_size`.
- Reduce `new_size`, `crop_image_height`, or `crop_image_width` if consistent with the task.
- Reduce model capacity keys only with architecture/checkpoint implications understood through `../model-internals/`.
- Set `vgg_w: 0` if perceptual loss is not required.
