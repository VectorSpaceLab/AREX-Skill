# Train/test workflow recipes

Use the data-preparation validator before every recipe. Replace `DATASET_ROOT`, `NAME`, and output paths with deliberate values. Commands below are public entry-point recipes for a target checkout; they do not download data or silently select a device.

The current parser has **no** `--gpu_ids` option. In a CPU-only PyTorch environment, the scripts select CPU automatically. On Linux hosts with a CUDA-capable build, prefix a command with `CUDA_VISIBLE_DEVICES=` to hide GPUs and force the source's automatic CPU path. To limit visible GPUs, prefix with a deliberate value such as `CUDA_VISIBLE_DEVICES=0,1`.

## CycleGAN: unpaired training

Expected layout:

```text
DATASET_ROOT/
  trainA/
  trainB/
  testA/   # optional during training
  testB/   # optional during training
```

Validate and train:

```bash
python sub-skills/data-preparation/scripts/validate_layout.py \
  --mode unaligned --dataroot DATASET_ROOT
CUDA_VISIBLE_DEVICES= python train.py \
  --dataroot DATASET_ROOT \
  --name NAME \
  --model cycle_gan \
  --dataset_mode unaligned
```

The model defaults to two ResNet generators, two discriminators, instance normalization, least-squares GAN loss, no dropout, and an image pool of 50. `--direction BtoA` swaps the semantic input/output domains; it does not rename folders.

## CycleGAN: testing both directions

```bash
python sub-skills/data-preparation/scripts/validate_layout.py \
  --mode unaligned --dataroot DATASET_ROOT --phase test
CUDA_VISIBLE_DEVICES= python test.py \
  --dataroot DATASET_ROOT \
  --name NAME \
  --model cycle_gan \
  --dataset_mode unaligned \
  --epoch latest \
  --num_test 50
```

Use `--results_dir RESULTS_ROOT` to move the HTML result page. The test script loads only the generators for `cycle_gan` and writes an HTML page beneath `<results_dir>/<name>/<phase>_<epoch>/`.

## One-sided generator application

Use `--model test` when only one collection of input images should be translated. The model selects `single` loading automatically, so `--dataroot` points directly to the image folder rather than its parent dataset root.

```bash
python sub-skills/data-preparation/scripts/validate_layout.py \
  --mode single --dataroot INPUT_IMAGES
CUDA_VISIBLE_DEVICES= python test.py \
  --dataroot INPUT_IMAGES \
  --name NAME \
  --model test \
  --model_suffix _A \
  --netG resnet_9blocks \
  --norm instance \
  --no_dropout \
  --direction AtoB \
  --preprocess none
```

`--model_suffix _A` makes the loader seek `latest_net_G_A.pth` (or the selected epoch). Use the suffix that matches the checkpoint's saved generator name. High-resolution one-sided inference is often less memory-intensive because only one generator is loaded.

## pix2pix: paired training and testing

Expected layout:

```text
DATASET_ROOT/
  train/  # side-by-side A|B images
  test/   # side-by-side A|B images
```

Train:

```bash
python sub-skills/data-preparation/scripts/validate_layout.py \
  --mode aligned --dataroot DATASET_ROOT --check-open --check-aligned-width
CUDA_VISIBLE_DEVICES= python train.py \
  --dataroot DATASET_ROOT \
  --name NAME \
  --model pix2pix \
  --dataset_mode aligned \
  --direction BtoA \
  --netG unet_256 \
  --norm batch \
  --pool_size 0
```

The pix2pix defaults are U-Net 256, batch normalization, vanilla GAN loss, no image pool, and `lambda_L1=100`. Explicitly repeat architecture and direction flags at test time.

```bash
CUDA_VISIBLE_DEVICES= python test.py \
  --dataroot DATASET_ROOT \
  --name NAME \
  --model pix2pix \
  --dataset_mode aligned \
  --direction BtoA \
  --netG unet_256 \
  --norm batch \
  --num_test 50
```

## Colorization

Colorization expects natural RGB images, not combined A/B pairs:

```text
COLOR_ROOT/
  train/
  test/
```

```bash
python sub-skills/data-preparation/scripts/validate_layout.py \
  --mode colorization --dataroot COLOR_ROOT --check-open
CUDA_VISIBLE_DEVICES= python train.py \
  --dataroot COLOR_ROOT \
  --name NAME \
  --model colorization \
  --dataset_mode colorization
CUDA_VISIBLE_DEVICES= python test.py \
  --dataroot COLOR_ROOT \
  --name NAME \
  --model colorization \
  --dataset_mode colorization
```

The dataset converts each RGB image to Lab internally: input A is one L channel and target B is two `ab` channels. The colorization model converts visual outputs back to RGB for HTML display.

## Resume and monitor

- Resume from the latest checkpoint with `--continue_train`; set `--epoch_count` when the previous run used a non-default epoch numbering scheme.
- Use `--load_iter N` or `--epoch E` to select a saved checkpoint during test.
- Use `--no_html` to avoid training sample pages. The current implementation logs local loss text and uses W&B only when `--use_wandb` is supplied.
- Do not infer GAN convergence from a single loss curve; inspect periodically generated samples and task-appropriate evaluation.

## DDP and multi-GPU

The README documents `torchrun --nproc_per_node=N train.py ...` for single-machine DDP and recommends a synchronized normalization choice. The current parser accepts `syncbatch`, while some prose uses spellings such as `sync_batch`; the current `BaseModel.setup` guard also contains a contradictory `syncbatch` check. Verify the exact checkout behavior before committing to a DDP run, and keep a single-process GPU or CPU fallback command ready.
