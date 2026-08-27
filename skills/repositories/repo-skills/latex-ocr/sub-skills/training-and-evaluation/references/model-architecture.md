# Model Architecture Notes

## High-Level Structure

LaTeX-OCR maps equation images to LaTeX tokens with an encoder-decoder model:

- encoder: either a hybrid ResNetV2 + Vision Transformer encoder or a pure ViT
  wrapper;
- decoder: an `x_transformers` autoregressive Transformer decoder;
- tokenizer: `PreTrainedTokenizerFast` loaded from tokenizer JSON;
- optional image resizer: a small ResNetV2 classifier predicting a better width
  for preprocessing.

## Hybrid Encoder

The hybrid encoder builds a ResNetV2 backbone and wraps it with a timm hybrid
Vision Transformer embedding. `patch_size` must be a multiple of the backbone
minimum patch size derived from `backbone_layers`.

## ViT Encoder

The ViT encoder rearranges images into fixed-size patches and uses learned
positional embeddings sized by `max_width`, `max_height`, and `patch_size`.
Changing these dimensions affects compatibility with existing checkpoints.

## Decoder Generation

The model starts from repeated BOS tokens and calls decoder generation until EOS
or `max_seq_len`. `temperature` controls sampling entropy, which is why repeated
OCR predictions can vary.

## Compatibility Warning

Checkpoint compatibility depends on architecture fields, tokenizer vocabulary,
image dimensions, and token ids. When changing any of those, expect old weights
to fail to load or produce invalid predictions.
