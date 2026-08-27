# Training workflows

## Main function

The bundled concrete training entrypoint is `runtime/train.py`. Run it through `scripts/run_training.py` so the working directory and `PYTHONPATH` point at the packaged runtime mirror:

```bash
python sub-skills/training/scripts/run_training.py --dry-run -- --weights '' --cfg models/yolov4-p5.yaml --data data/coco.yaml --hyp data/hyp.scratch.yaml --img-size 896 896 --batch-size 16
```

The training function centers on:

- `train(hyp, opt, device, tb_writer=None)`

The function:

- writes `hyp.yaml` and `opt.yaml` into the run directory,
- builds the model from a YAML file or checkpoint,
- constructs train and validation dataloaders,
- runs optimizer, scheduler, EMA, and AMP logic,
- calls the evaluation routine at epoch boundaries,
- writes checkpoints and result plots,
- optionally evolves hyperparameters.

## Important inputs

- `--weights` for fine-tuning or resume.
- `--cfg` for training from a YAML architecture definition.
- `--data` for the dataset YAML.
- `--hyp` for the hyperparameter YAML.
- `--epochs`, `--batch-size`, `--img-size`, and `--device` for run sizing.
- `--rect`, `--cache-images`, `--multi-scale`, `--sync-bn`, `--adam`, `--single-cls`, `--resume`, and `--evolve` for run behavior.

## Default output tree

A successful run produces a directory with:

- `hyp.yaml`
- `opt.yaml`
- `results.txt`
- `weights/last.pt`
- `weights/best.pt`
- `train_batch*.jpg`
- `results.png` when plotting is enabled

## Decision points

### Scratch vs. fine-tune

- Use the YAML model path when you want to start from architecture only.
- Use checkpoint weights when you want to reuse learned parameters.
- Let the hyperparameter file match the chosen regime (`hyp.scratch.yaml` or `hyp.finetune.yaml`).

### Single GPU vs. DDP

- Single-GPU runs are simpler and easier to debug.
- DDP requires device count, world-size, and batch-size coordination.
- `sync_bn` only matters when DDP is active.

### Training settings that change behavior

- `rect` changes how images are grouped and padded.
- `cache_images` trades memory for loader speed.
- `multi_scale` changes the per-batch input size.
- `noautoanchor` skips anchor checks.
- `notest` skips epoch-end evaluation until the final epoch.

## Post-epoch logic

At the end of each epoch, the training loop may:

- run the evaluation routine,
- append to `results.txt`,
- update TensorBoard scalars,
- save `last.pt` and `best.pt`,
- strip optimizer state from saved checkpoints when appropriate,
- plot training curves after the run.

## Hyperparameter evolution

`--evolve` changes the run into a search loop that mutates the hyperparameters and writes results to the evolution files instead of behaving like a standard training run.

## Useful checks before a long run

- The runtime bundle is complete: `python scripts/check_runtime_bundle.py`.
- The dataset YAML resolves.
- The model YAML or checkpoint resolves.
- The image size is stride-compatible.
- The batch size fits the device count.
- The environment can import the model stack.
- The validation split is available if you expect epoch-end evaluation.

Use `scripts/prepare_training_run.py` for a safe plan check, then use `scripts/run_training.py --dry-run -- ...` to preview the concrete bundled `runtime/train.py` command before removing `--dry-run`.
