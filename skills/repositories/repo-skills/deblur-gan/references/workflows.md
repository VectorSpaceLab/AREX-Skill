# DeblurGAN workflows

## 1. Check the environment

Start with the root helper if you are unsure whether the runtime is healthy:

```bash
python scripts/check_deblurgan_env.py --repo-root <path-to-DeblurGAN-checkout> --cuda
```

Use the CPU path instead of `--cuda` if you only need imports and signatures.

## 2. Prepare paired training data

If you have separate blur and sharp folders, build AB pairs with the bundled helper:

```bash
python sub-skills/data-preparation/scripts/combine_pairs.py \
  --fold_A <path-to-blur-folder> \
  --fold_B <path-to-sharp-folder> \
  --fold_AB <path-to-output-folder>
```

Add `--use_AB` when the filenames use the `_A.` / `_B.` naming pattern.

## 3. Train the model

Use the training wrapper so the run is not tied to the source script's hardcoded local path:

```bash
python sub-skills/training/scripts/run_training.py \
  --repo-root <path-to-DeblurGAN-checkout> \
  --dataroot <path-to-paired-data> \
  --name experiment_name \
  --model content_gan \
  --gan_type wgan-gp \
  --learn_residual \
  --resize_or_crop crop \
  --fineSize 256
```

Useful smoke options:

- `--headless` to avoid visdom dependency.
- `--max-steps 1` or another tiny number to cap the run.

## 4. Restore images

Use the inference wrapper for single-image restoration:

```bash
python sub-skills/inference/scripts/run_inference.py \
  --repo-root <path-to-DeblurGAN-checkout> \
  --dataroot <path-to-single-image-folder> \
  --model test \
  --dataset_mode single \
  --learn_residual \
  --which_epoch latest \
  --gpu_ids -1
```

Useful smoke options:

- `--headless` to avoid visdom dependency.
- `--gpu_ids -1` for CPU-only inference.
- `--how_many 1` for the smallest possible run.

## 5. Understand the output trees

- Training checkpoints live under `checkpoints/<name>/`.
- Inference results live under `results/<name>/<phase>_<which_epoch>/`.
- The HTML gallery is written under the results tree and the generator outputs are saved as PNG files.

## 6. Source-vs-wrapper behavior

The source scripts were inspected and then wrapped because they contain hardcoded local values and brittle imports that are not portable across machines.

The generated wrappers keep the repository's behavior but make the commands safer to reuse in a new checkout.
