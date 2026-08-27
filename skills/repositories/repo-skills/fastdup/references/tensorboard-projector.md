# TensorBoard projector workflow

This reference covers `fastdup.tensorboard_projector.export_to_tensorboard_projector_inner(...)`.

## Purpose

The helper writes embedding metadata and TensorBoard projector artifacts so you can inspect an embedding space visually.

## Main inputs

- `imglist`: image paths in the same row order as the feature matrix
- `features`: `float32` feature matrix
- `log_dir`: output directory for TensorBoard files
- `sample_size`: number of rows to visualize
- `d`: feature width, which must match `features.shape[1]`
- `with_images`: whether to register a sprite image

## Main outputs

- TensorFlow embedding checkpoint files
- `meta.tsv`
- `sprite.png` when sprites are enabled
- TensorBoard projector configuration files written by the projector plugin

## Common failure modes

- TensorFlow is not installed
- the feature width does not match `d`
- the image list and feature matrix are misaligned
- the log directory cannot be created

## Recommended use

Use the bundled smoke script only when TensorFlow is already installed in the inspection environment. Otherwise keep this as a documented optional workflow.
