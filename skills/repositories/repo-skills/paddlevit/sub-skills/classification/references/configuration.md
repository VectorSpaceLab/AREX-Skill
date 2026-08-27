# Configuration and preprocessing

## Merge order

The common yacs pattern is:

```text
defaults in config.py < YAML from -cfg < supported CLI overrides
```

`get_config()` clones defaults. YAML `BASE` entries are resolved relative to
the YAML file. Keys are case-sensitive and model configs are not portable
between folders. The common ViT-style CLI includes `-cfg`, `-dataset`,
`-data_path`, `-output`, `-batch_size`, `-batch_size_eval`, `-image_size`,
`-accum_iter`, `-pretrained`, `-resume`, `-last_epoch`, `-eval`, and `-amp`.
A falsey CLI value may be ignored by old `if args.value` update code.

## Review before execution

- **DATA:** dataset name, absolute root, image channels/size, crop percent,
  mean/std, workers, train/eval batch sizes.
- **MODEL:** type/name, class count, patch/window/stride geometry, stage/depth/
  head lists, and train/deploy state.
- **TRAIN:** epochs, warmup/LR/weight decay, accumulation, clipping,
  mixup/cutmix/EMA, and AMP.
- **Checkpoint:** pretrained versus resume, plain state dict versus bundle,
  head class count, positional embeddings and generated buffers.

## ImageNet contract

```text
<imagenet>/train_list.txt       # relative/path.jpg integer_label
           /val_list.txt
           /train/<class>/<image>
           /val/<class>/<image>
```

The representative loader asserts both list files, joins relative paths to the
root, converts images to RGB, and returns normalized `[3,H,W]` tensors. Train
uses random resized crop + horizontal flip; validation resizes the short edge
to `floor(IMAGE_SIZE/CROP_PCT)`, center-crops, tensorizes, then normalizes.
Tensor values must be in `[0,1]` before normalization. Preserve the selected
checkpoint recipe rather than assuming one mean/std: the ViT default is
`[0.5,0.5,0.5]`, while many model configs use conventional ImageNet values.

## ABAW and MAE

ABAW uses aligned face-frame directories plus `Train_Set` and `Validation_Set`
annotation files, not ImageNet list files. `all`, `coarse`, and `negative`
produce 8, 5, and 4 classes respectively; original/remapped `-1` entries are
skipped. Match `MODEL.NUM_CLASSES` to `class_type`.

MAE has separate pretraining and classifier-finetuning configs, including
encoder/decoder fields and `MASK_RATIO`. Its tests cover yacs merge, dataset
contracts, reconstruction/mask shapes, embeddings, attention, MLP, encoder,
and scheduler/utilities. Do not use a pretraining YAML as a generic classifier
config.
