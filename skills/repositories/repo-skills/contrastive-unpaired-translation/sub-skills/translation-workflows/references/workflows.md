# Translation workflows

This page describes the verified CUT, FastCUT, and SinCUT workflows exposed by `train.py` and `test.py`.

## Training flow

1. Parse `TrainOptions`.
2. Build the dataset with `create_dataset(opt)`.
3. Build the model with `create_model(opt)`.
4. Create the `Visualizer`.
5. Run the epoch/iteration loop, calling `model.data_dependent_initialize(data)` on the first batch.
6. Save checkpoints under `checkpoints/<name>/`.
7. Emit visdom updates and HTML pages when the display options are enabled.

### Common training command

```bash
python train.py \
  --dataroot /path/to/data \
  --name my_cut_run \
  --model cut \
  --CUT_mode CUT
```

### FastCUT variant

Use the same command but set `--CUT_mode FastCUT`. The code switches the default NCE weighting and the FastCUT-specific regularization settings inside `CUTModel.modify_commandline_options`.

### SinCUT single-image training

SinCUT is the single-image path built on `models/sincut_model.py`.

```bash
python train.py \
  --model sincut \
  --name my_single_image_run \
  --dataroot /path/to/single-image-data
```

SinCUT assumes one image in `trainA` and one image in `trainB`. Its defaults switch to `dataset_mode=singleimage`, `netG=stylegan2`, `netD=stylegan2`, `preprocess=zoom_and_patch`, and a single-patch contrastive setup.

## Testing flow

1. Parse `TestOptions`.
2. Force batch size 1, no shuffling, no flipping, and no visdom display.
3. Build the dataset and model.
4. Load the checkpoint from `checkpoints/<name>/<epoch>_net_<model>.pth`.
5. Save HTML results under `results/<name>/<phase>_<epoch>/`.

### Common test command

```bash
python test.py \
  --dataroot /path/to/data \
  --name my_cut_run \
  --model cut \
  --epoch latest
```

### Pretrained inference

The repository's pretrained launcher presets are still just command strings. For a real run, point `--name`, `--epoch`, and `--checkpoints_dir` at the checkpoint directory, then choose the matching `--phase` and `--results_dir`.

Example pattern:

```bash
python test.py \
  --dataroot /path/to/data \
  --name pretrained_run \
  --model cut \
  --epoch latest \
  --results_dir /path/to/results
```

## Output conventions

| Workflow | Output location | Notes |
| --- | --- | --- |
| Training | `checkpoints/<name>/web/` | HTML snapshots and images appear here when HTML logging is enabled. |
| Training logs | `checkpoints/<name>/loss_log.txt` | Written by `util.visualizer.Visualizer`. |
| Testing | `results/<name>/<phase>_<epoch>/` | Contains HTML output and per-image subdirectories. |
| Checkpoints | `checkpoints/<name>/<epoch>_net_<model>.pth` | The suffix depends on the model family. |

## Important model details

- `CUTModel.modify_commandline_options` defines the CUT/FastCUT NCE and GAN options.
- `SinCUTModel.modify_commandline_options` overrides the dataset, network, and preprocessing defaults for the single-image path.
- `BaseOptions` converts `--gpu_ids` into a list and switches to CPU when the flag is set to `-1`.
- `BaseModel.load_networks` can load from `--pretrained_name` during training or from the run's own `checkpoints_dir` during test-time inference.
- `Visualizer` uses visdom only when `display_id > 0`; otherwise HTML logging remains the main visual output.

## What to read together with this page

- `references/cli-reference.md` for the exact verified option families.
- `references/troubleshooting.md` for checkpoint, visdom, and backend failures.
- `scripts/check_runtime.py` for a safe import smoke check.

## Verification notes

The import and help checks used to validate this page were:
- `python train.py --help`
- `python test.py --help`
- imports of `train`, `test`, `models.cut_model`, `models.sincut_model`, `data.unaligned_dataset`, and `data.singleimage_dataset`
