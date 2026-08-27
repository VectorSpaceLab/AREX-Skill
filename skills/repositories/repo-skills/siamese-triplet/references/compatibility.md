# Compatibility Notes

## Torchvision dataset attributes

The repository notebooks and wrappers were written against older torchvision dataset objects that expose:

- `train`
- `train_data`
- `train_labels`
- `test_data`
- `test_labels`

Newer torchvision versions often use `data` and `targets` instead. If you are using a modern dataset object, add a tiny compatibility shim or a fake dataset fixture that exposes the legacy attributes expected by the wrappers.

## Input shapes

- The default embedding backbone expects grayscale images shaped like `1×28×28`.
- The dataset wrappers convert arrays to PIL grayscale images before applying a transform.
- If you use a custom dataset, make sure the transform returns a tensor with the expected channel and spatial dimensions.

## Embedding and plotting assumptions

- The notebooks assume a 2D embedding for plotting.
- If you change the embedding dimension, update the notebook-style plotting helper and any smoke checks that assert a 2D output.

## Device notes

- CPU is fully sufficient for the generated skill's smoke checks.
- CUDA is optional. The host used to distill this skill had a CUDA-capable PyTorch build and passed a tiny tensor allocation smoke, but the skill does not require CUDA for normal usage.
- `EmbeddingNetL2` divides by the embedding norm without an epsilon guard. If you adapt the code for custom inputs that can collapse to all zeros, watch for `NaN` or inf values.
