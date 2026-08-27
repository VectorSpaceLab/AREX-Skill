# DeblurGAN inference workflows

## Recommended portable command

Use the bundled wrapper rather than the source `test.py` when you want a reusable command line:

```bash
python scripts/run_inference.py \
  --repo-root <path-to-DeblurGAN-checkout> \
  --dataroot <path-to-single-image-folder> \
  --model test \
  --dataset_mode single \
  --learn_residual \
  --which_epoch latest \
  --gpu_ids -1
```

## Common flags

The source option parser exposes these useful groups for inference:

- Input layout: `--dataroot`, `--dataset_mode single`, `--batchSize 1`, `--nThreads 1`, `--serial_batches`, `--no_flip`.
- Checkpoint selection: `--checkpoints_dir`, `--name`, `--which_epoch`.
- Output control: `--results_dir`, `--phase`, `--how_many`, `--aspect_ratio`.
- Model behavior: `--model test`, `--which_model_netG`, `--learn_residual`, `--gpu_ids`.

## Result layout

The wrapper saves results under:

```text
results/<name>/<phase>_<which_epoch>/
  index.html
  images/
```

The HTML helper expects the output directory to be writable.

## CPU fallback

For CPU-only inspection or smoke checks, set `--gpu_ids -1`.

That keeps the model on CPU while still using the same generator checkpoint and folder layout.

## Source-script mismatch to remember

The shipped `test.py` imports `SSIM` from an external `ssim` package even though the repository already ships a local `util.metrics.SSIM` helper. The bundled wrapper follows the local route so the inference workflow does not hinge on that external import path.

## Smoke usage

When you only want to confirm the wiring:

- Use a tiny single-image folder.
- Keep `how_many` at 1 or another small number.
- Set `--gpu_ids -1` if you want the CPU path.
- Ensure the checkpoint exists before starting the run.
