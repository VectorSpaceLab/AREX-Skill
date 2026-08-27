# DALLE-pytorch API reference

This reference distills the public API and live inspection facts for `dalle-pytorch` version `1.6.6`.

## Imports

```python
from dalle_pytorch import DALLE, CLIP, DiscreteVAE
from dalle_pytorch import OpenAIDiscreteVAE, VQGanVAE
from dalle_pytorch.tokenizer import tokenizer, HugTokenizer, ChineseTokenizer, YttmTokenizer
from dalle_pytorch.loader import TextImageDataset
```

`OpenAIDiscreteVAE` and `VQGanVAE` are importable classes, but their constructors may download weights/configs and have version constraints. Do not instantiate them as a harmless import check.

## `DiscreteVAE`

Signature observed from the installed package:

```python
DiscreteVAE(
    image_size=256,
    num_tokens=512,
    codebook_dim=512,
    num_layers=3,
    num_resnet_blocks=0,
    hidden_dim=64,
    channels=3,
    smooth_l1_loss=False,
    temperature=0.9,
    straight_through=False,
    reinmax=False,
    kl_div_loss_weight=0.0,
    normalization=((0.5, 0.5, 0.5, 0), (0.5, 0.5, 0.5, 1)),
)
```

Important behavior:

- `image_size` must be a power of two.
- `num_layers >= 1`; image token map size is `image_size // (2 ** num_layers)`.
- `forward(img, return_loss=True)` returns the reconstruction/codebook loss.
- `forward(img, return_loss=True, return_recons=True)` returns `(loss, reconstructions)`.
- `forward(img, return_logits=True)` returns codebook logits before Gumbel-softmax sampling.
- `get_codebook_indices(images)` returns flattened hard visual token ids of shape `(batch, image_seq_len)`.
- `decode(img_seq)` maps flattened token ids back to image tensors.

Tiny CPU smoke:

```python
import torch
from dalle_pytorch import DiscreteVAE

vae = DiscreteVAE(image_size=8, num_tokens=16, codebook_dim=8, num_layers=1, hidden_dim=8)
images = torch.randn(2, 3, 8, 8)
loss, recons = vae(images, return_loss=True, return_recons=True)
indices = vae.get_codebook_indices(images)
assert recons.shape == images.shape
assert indices.shape == (2, 16)
```

## `DALLE`

Signature observed from the installed package:

```python
DALLE(
    *,
    dim,
    vae,
    num_text_tokens=10000,
    text_seq_len=256,
    depth,
    heads=8,
    dim_head=64,
    reversible=False,
    attn_dropout=0.0,
    ff_dropout=0,
    sparse_attn=False,
    attn_types=None,
    loss_img_weight=7,
    stable=False,
    sandwich_norm=False,
    shift_tokens=True,
    rotary_emb=True,
    shared_attn_ids=None,
    shared_ff_ids=None,
    share_input_output_emb=False,
    optimize_for_inference=False,
)
```

Important behavior:

- `vae` must be a `DiscreteVAE`, `OpenAIDiscreteVAE`, or `VQGanVAE` instance.
- The VAE is frozen inside `DALLE`; train the VAE first unless using a pretrained wrapper.
- `num_text_tokens` is internally offset by `text_seq_len` so padding can use unique position-dependent token ids.
- `forward(text, image, return_loss=True)` accepts raw image tensors and calls `vae.get_codebook_indices` internally.
- `forward(text, image_tokens_or_empty, return_loss=False)` returns logits over text + image tokens.
- `null_cond_prob` randomly drops text conditioning for classifier-free guidance training.
- `generate_images(text, filter_thres=..., temperature=..., img=None, num_init_img_tokens=None, cond_scale=..., use_cache=False)` returns generated image tensors, or `(images, scores)` when a `CLIP` scorer is supplied.
- `generate_texts(tokenizer, text=..., filter_thres=..., temperature=...)` completes text tokens, but source code creates CUDA tensors internally; treat this as GPU-oriented.

Tiny models with very small `dim_head` can trigger rotary-embedding math issues in modern `rotary-embedding-torch`. For smoke tests, either use a realistic `dim_head` or set `rotary_emb=False`.

## `CLIP`

Signature observed from the installed package:

```python
CLIP(
    *,
    dim_text=512,
    dim_image=512,
    dim_latent=512,
    num_text_tokens=10000,
    text_enc_depth=6,
    text_seq_len=256,
    text_heads=8,
    num_visual_tokens=512,
    visual_enc_depth=6,
    visual_heads=8,
    visual_image_size=256,
    visual_patch_size=32,
    channels=3,
)
```

Important behavior:

- `forward(text, image, text_mask=None, return_loss=True)` trains a contrastive loss over the batch.
- `forward(..., return_loss=False)` returns same-index text/image similarity scores of shape `(batch,)`.
- `visual_image_size` must be divisible by `visual_patch_size`.
- `DALLE.generate_images(text, clip=clip)` returns images and CLIP scores for ranking.

## VAE wrappers

### `OpenAIDiscreteVAE`

- Constructor asserts installed torch is `< 1.11` / `<= 1.10` according to the source assertion message.
- It downloads OpenAI encoder/decoder pickle files into a user cache if missing.
- Do not use it as the default in modern torch environments without pinning torch appropriately or switching to a custom trained `DiscreteVAE`/VQGAN path.

### `VQGanVAE`

- `VQGanVAE(vqgan_model_path=None, vqgan_config_path=None)` loads Taming Transformers VQGAN.
- With no paths, it downloads the default model and config into a cache.
- With custom paths, both a `.ckpt` model and YAML config are expected.
- The wrapper derives `num_layers`, `image_size`, and `num_tokens` from the loaded config/model.

## Tokenizers

- `tokenizer`: default OpenAI-style byte-pair tokenizer backed by packaged vocabulary data.
- `HugTokenizer(bpe_path)`: loads a HuggingFace `tokenizers` JSON file.
- `YttmTokenizer(bpe_path)`: loads a YouTokenToMe BPE model file; padding id must remain `0` for the training helpers.
- `ChineseTokenizer()`: downloads/loads HuggingFace `bert-base-chinese`; this can need network/cache.

Common method shape:

```python
tokens = tokenizer.tokenize(["a prompt"], context_length=256, truncate_text=False)
text = tokenizer.decode(tokens[0])
```

If text is too long and truncation is disabled, tokenizers raise a runtime error. Use `--truncate_captions` for training data that may exceed `text_seq_len`.

## Data helper

```python
TextImageDataset(folder, text_len=256, image_size=128, truncate_captions=False, resize_ratio=0.75, transparent=False, tokenizer=None, shuffle=False)
```

The dataset recursively matches image files (`.png`, `.jpg`, `.jpeg`, `.bmp`) and text files (`.txt`) by stem. Each text file may contain multiple newline-separated descriptions; one non-empty line is sampled per item.

## Checkpoint payloads

VAE training saves payloads shaped like:

```python
{
  "hparams": vae_params,
  "weights": vae.state_dict(),
}
```

DALL-E training saves payloads shaped like:

```python
{
  "hparams": dalle_params,
  "vae_params": vae_params_or_none,
  "weights": dalle.state_dict(),
  "opt_state": optimizer_state,
  "scheduler_state": scheduler_state_or_none,
  "epoch": epoch,
  "version": "1.6.6",
  "vae_class_name": vae.__class__.__name__,
}
```

DeepSpeed checkpoints may be directories with an auxiliary payload rather than a single ordinary `.pt` file. Route those cases to `distributed-and-backends`.
