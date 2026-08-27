# Pretrained assets

Pretrained model downloads are network and storage operations. This reference records the repository's accepted model names and checkpoint placement pattern so future agents can plan the operation without reopening source scripts. Do not download a checkpoint unless the user approves the model name, destination, bandwidth/storage budget, and overwrite policy.

## Checkpoint placement

The original helper pattern places a model at:

```text
checkpoints/<model_name>_pretrained/latest_net_G.pth
```

A test command then usually uses `--name <model_name>_pretrained`. If the checkpoint represents a one-sided CycleGAN generator and the saved filename is `latest_net_G.pth`, use `--model test` with no `--model_suffix`. If the checkpoint file is named `latest_net_G_A.pth` or `latest_net_G_B.pth`, pass the matching suffix.

## CycleGAN pretrained names

The CycleGAN download URL pattern is:

```text
http://efrosgans.eecs.berkeley.edu/cyclegan/pretrained_models/<name>.pth
```

Accepted names from the repository script:

```text
apple2orange
orange2apple
summer2winter_yosemite
winter2summer_yosemite
horse2zebra
zebra2horse
monet2photo
style_monet
style_cezanne
style_ukiyoe
style_vangogh
sat2map
map2sat
cityscapes_photo2label
cityscapes_label2photo
facades_photo2label
facades_label2photo
iphone2dslr_flower
```

Typical one-sided CycleGAN application:

```bash
CUDA_VISIBLE_DEVICES= python test.py \
  --dataroot INPUT_IMAGES \
  --name horse2zebra_pretrained \
  --model test \
  --no_dropout
```

Use the data-preparation sub-skill to validate `INPUT_IMAGES` as a `single` data root before running the command.

## pix2pix pretrained names

The pix2pix download URL pattern is:

```text
http://efrosgans.eecs.berkeley.edu/pix2pix/models-pytorch/<name>.pth
```

Accepted names from the repository script:

```text
edges2shoes
sat2map
map2sat
facades_label2photo
day2night
```

For paired pix2pix model testing, keep the dataset orientation and architecture consistent with training. For Facades label-to-photo examples, the repository examples use `--direction BtoA` with the paired Facades layout.

```bash
CUDA_VISIBLE_DEVICES= python test.py \
  --dataroot DATASET_ROOT \
  --name facades_label2photo_pretrained \
  --model pix2pix \
  --dataset_mode aligned \
  --direction BtoA \
  --netG unet_256 \
  --norm batch
```

## Download safety checklist

1. Confirm the exact name appears in the list above; do not guess unsupported names.
2. Confirm whether a matching dataset is already local; many pretrained examples still need an input dataset.
3. Inspect whether `checkpoints/<name>_pretrained/` already exists before overwriting.
4. Decide whether the HTTP URL is reachable from the current environment and whether a proxy/mirror is appropriate for this one command only.
5. Record checkpoint architecture assumptions: `--netG`, `--norm`, `--no_dropout`, `--direction`, and any `--model_suffix`.
6. Run a tiny `--num_test 1` inference before a large batch.
