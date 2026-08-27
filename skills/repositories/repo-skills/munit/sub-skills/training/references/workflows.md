# Training workflows

## Preflight sequence before any long run

1. Confirm the runtime first. MUNIT training expects the legacy CUDA/PyTorch stack and has many unconditional `.cuda()` calls. Use `../environment-and-setup/` for dependency and backend checks.
2. Validate dataset and YAML layout. Use `../data-and-configuration/` to verify folder/list paths, train/test domain folders, image counts, crop/resize keys, and list-file semantics.
3. Build a dry-run command with `scripts/munit_train_command.py`. Treat warnings as blockers for unattended runs.
4. Review trainer/config compatibility. Use `MUNIT` with the bundled configs unless a UNIT-specific config includes KL weights.
5. Launch full training only after explicit authorization, with a long-running process manager and enough GPU memory. The training loop exits only after `iterations >= max_iter`.

## New MUNIT training run

Typical safe planning command from this sub-skill directory:

```bash
python scripts/munit_train_command.py \
  --repo-root /path/to/user/munit-checkout \
  --config configs/demo_edges2handbags_folder.yaml \
  --output-path runs/demo_edges2handbags \
  --trainer MUNIT
```

The helper prints the real command but does not run it. A user-approved training command has this shape:

```bash
python train.py --config configs/demo_edges2handbags_folder.yaml --output_path runs/demo_edges2handbags --trainer MUNIT
```

Operational notes:

- `--config` controls the model name through its filename stem. A config named `demo_edges2handbags_folder.yaml` writes model artifacts under `outputs/demo_edges2handbags_folder` within the chosen output path.
- `--output_path` defaults to the current directory if omitted, but an explicit run directory is safer for multiple experiments.
- `--trainer MUNIT` builds two AdaIN generators and two multi-scale discriminators. It is the only trainer compatible with the bundled demo configs without adding new loss keys.
- The first output side effect after data/model setup is a tensorboardX writer under `logs/<model_name>` and `outputs/<model_name>` subfolders for images/checkpoints.

## Resume a stopped run

Resume uses the same config stem and output path as the previous run:

```bash
python scripts/munit_train_command.py \
  --repo-root /path/to/user/munit-checkout \
  --config configs/demo_edges2handbags_folder.yaml \
  --output-path runs/demo_edges2handbags \
  --trainer MUNIT \
  --resume
```

Expected checkpoint directory:

```text
<output_path>/outputs/<model_name>/checkpoints/
```

It must contain at least:

- `gen_XXXXXXXX.pt`
- `dis_XXXXXXXX.pt`
- `optimizer.pt`

where `XXXXXXXX` is an eight-digit iteration. The resume loader picks the lexicographically last generator and discriminator filename containing `gen` or `dis`, loads optimizer state, reconstructs schedulers at the parsed iteration, and prints `Resume from iteration N`.

## Distilled training loop

The training entrypoint performs the following sequence:

1. Parse `--config`, `--output_path`, `--resume`, and `--trainer`.
2. Load YAML config and read `max_iter` plus `display_size`.
3. Set `config['vgg_model_path']` to the chosen output path.
4. Instantiate `MUNIT_Trainer` or `UNIT_Trainer`, then call `trainer.cuda()`.
5. Build train/test data loaders for both domains.
6. Create fixed display batches by indexing the first `display_size` samples from train/test datasets, then moving those tensors to CUDA.
7. Create tensorboardX writer and output subfolders; copy the config to `outputs/<model_name>/config.yaml`.
8. If `--resume`, load checkpoint state and resume iteration count; otherwise start from zero.
9. For paired batches from domain A and B loaders: update learning rate, move images to CUDA, run discriminator update, run generator update, synchronize CUDA, log losses, save image grids/HTML, snapshot weights, increment iteration, and exit when `max_iter` is reached.

## Demo shell scripts as reference only

The demo training shell scripts combine dataset download, archive extraction, optional ImageMagick cropping/splitting, and full training. They are useful examples of dataset preparation plus final command shape, but should not be run blindly by an agent because they perform network downloads, mutate dataset directories, and launch full training.

Adapt them manually as follows:

- Treat the download/crop commands as a data-preparation recipe to be reviewed by the user and routed through `../data-and-configuration/`.
- Keep the final command shape: `python train.py --config <yaml>`.
- Prefer adding `--output_path <run-dir>` explicitly so repeated experiments do not collide.
- Use the dry-run helper before starting the real command.

## Reducing a config for a bounded smoke plan

For a tiny user-approved smoke run, preserve all required keys and adjust only safe run-control values:

- Lower `max_iter` to a small positive number.
- Lower `image_display_iter`, `image_save_iter`, `snapshot_save_iter`, and `log_iter` to values consistent with the smoke duration.
- Keep `display_size` no larger than each train/test dataset length.
- Keep `batch_size` valid for both loaders; the loop zips domain A and B loaders and uses `drop_last=True`.
- Keep crop/resize compatible with image dimensions.

Do not use smoke reduction to bypass the CUDA/runtime requirement; even a one-iteration training run enters CUDA paths.
