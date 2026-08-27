# DALLE2-pytorch generation API reference

This reference covers the public package API for `dalle2-pytorch` 1.15.6. Install with `pip install dalle2-pytorch` and import from `dalle2_pytorch`.

## Core object graph

| Object | Role | Inputs it needs | Outputs it produces |
| --- | --- | --- | --- |
| CLIP or clip adapter | Encodes prompt tokens and/or images into latent embeddings, and sometimes token-level text encodings. | Text token IDs and images. Public adapters may download pretrained CLIP weights. | `text_embed`, optional `text_encodings`, `image_embed`. |
| `DiffusionPriorNetwork` | Transformer denoiser inside the prior. | Noised image embedding, diffusion timestep, CLIP text embedding, optional text encodings. | Predicted image embedding or denoising target. |
| `DiffusionPrior` | Diffusion process mapping text/text embeddings to CLIP image embeddings. | Either `text` plus a CLIP adapter, or precomputed `text_embed` / `image_embed` for training loss. | Image embedding samples from `.sample(...)`; scalar training loss from `.forward(...)`. |
| `Unet` | Image diffusion denoiser used by the decoder. | Noised image/latent tensor, timestep, image embedding, optional text encodings, optional low-res conditioning. | Denoising prediction for one decoder stage. |
| `Decoder` | Diffusion process mapping CLIP image embeddings to images. | `image_embed` for sampling unless `unconditional=True`; images plus embeddings for forward loss. | Image tensor samples from `.sample(...)`; scalar training loss from `.forward(...)`. |
| `DALLE2` | Thin chain of prior then decoder. | Prompt string/list or token tensor; trained prior and decoder. | Image tensor or PIL image(s). |

Object relationship summary: CLIP/adapter produces embeddings; the prior maps text/text embedding to an image embedding; the decoder maps an image embedding to an image; `DALLE2` chains prior and decoder. Cascaded decoders use ordered Unets from low to high resolution, with matching `image_sizes`.

## Public constructor signatures

The signatures below are the inspected public signatures most future agents need. Many classes accept additional keyword arguments; keep architecture parameters compatible with the checkpoint or config that produced the weights.

### `DALLE2`

```python
DALLE2(prior, decoder, prior_num_samples=2)
```

- `prior` must be a `DiffusionPrior`.
- `decoder` must be a `Decoder`.
- `prior_num_samples` repeats each prompt for prior sampling and keeps the image embedding with highest prompt similarity. OpenAI's common default is two samples.
- Main call: `dalle2(text, cond_scale=1., prior_cond_scale=1., return_pil_images=False)`.
- If `text` is a string or list of strings, `DALLE2.forward` tokenizes using the package's simple tokenizer. Token tensors are also accepted.

### `DiffusionPriorNetwork`

```python
DiffusionPriorNetwork(
    dim,
    num_timesteps=None,
    num_time_embeds=1,
    num_image_embeds=1,
    num_text_embeds=1,
    max_text_len=256,
    self_cond=False,
    **kwargs,
)
```

Common `**kwargs` include transformer parameters such as `depth`, `dim_head`, `heads`, `ff_mult`, `normformer`, `attn_dropout`, and `ff_dropout`.

Important invariants:

- `dim` must match the CLIP image/text latent dimension used by `DiffusionPrior.image_embed_dim`.
- `num_timesteps=None` uses continuous timestep embeddings; setting it to the diffusion `timesteps` count uses a discrete embedding table.
- `max_text_len` should agree with the CLIP/tokenizer context length when `condition_on_text_encodings=True`.
- `self_cond=True` changes the denoising network state and must match trained checkpoints.

### `DiffusionPrior`

```python
DiffusionPrior(
    net,
    clip=None,
    image_embed_dim=None,
    image_size=None,
    image_channels=3,
    timesteps=1000,
    sample_timesteps=None,
    cond_drop_prob=0.0,
    text_cond_drop_prob=None,
    image_cond_drop_prob=None,
    loss_type='l2',
    predict_x_start=True,
    predict_v=False,
    beta_schedule='cosine',
    condition_on_text_encodings=True,
    sampling_clamp_l2norm=False,
    sampling_final_clamp_l2norm=False,
    training_clamp_l2norm=False,
    init_image_embed_l2norm=False,
    image_embed_scale=None,
    clip_adapter_overrides=dict(),
)
```

Use cases:

- With a CLIP/adapter: pass token IDs to `prior.sample(text, num_samples_per_batch=2, cond_scale=1., timesteps=None)`.
- Without CLIP: pass `image_embed_dim` and use `.forward(text_embed=..., image_embed=...)` for CPU-safe or precomputed-embedding loss checks. Sampling without CLIP is not the normal high-level route because `.sample` expects `self.clip.embed_text(...)`.
- `sample_timesteps < timesteps` enables DDIM-style faster sampling.
- `cond_scale != 1` is only valid when the model was trained with both text and image conditional dropout (`text_cond_drop_prob > 0` and `image_cond_drop_prob > 0`, or a suitable `cond_drop_prob`).

### `Unet`

```python
Unet(
    dim,
    image_embed_dim=None,
    text_embed_dim=None,
    cond_dim=None,
    dim_mults=(1, 2, 4, 8),
    channels=3,
    cond_on_text_encodings=False,
    cond_on_image_embeds=False,
    ...,
)
```

Full constructor has many architecture options. The highest-impact ones are:

- `image_embed_dim`: required when conditioning on image embeddings. In decoder construction, the first Unet is automatically cast to condition on image embeddings unless `unconditional=True`.
- `text_embed_dim` plus `cond_on_text_encodings=True`: required if decoder sampling should cross-attend to CLIP text encodings.
- `cond_dim`: conditioning-token width. It must be compatible with `num_image_tokens` and `num_time_tokens`; a safe rule is to leave it at the default or choose a divisor-compatible value. Tiny smoke tests use `cond_dim=8` for `dim=16` to avoid token-shape mismatch with the default four image tokens and two time tokens.
- `dim_mults`: controls down/up resolutions and memory. Large `(1, 2, 4, 8)` models are not CPU smoke tests.
- `lowres_cond` and `lowres_noise_cond`: decoder may cast these automatically for cascaded Unets. Do not hand-load weights across different low-resolution conditioning settings unless they were trained with those settings.
- `checkpoint_during_training=True` trades compute for memory during training only.

### `Decoder`

```python
Decoder(
    unet,
    clip=None,
    image_size=None,
    image_sizes=None,
    vae=(),
    timesteps=1000,
    sample_timesteps=None,
    image_cond_drop_prob=0.1,
    text_cond_drop_prob=0.5,
    unconditional=False,
    ...,
)
```

Important invariants:

- Supply exactly one of `image_size`, `image_sizes`, or `clip` from which image size can be derived.
- `unet` may be one `Unet` or a tuple/list of Unets. When multiple Unets are used, `image_sizes` must have exactly one resolution per Unet.
- `image_sizes` are sorted and treated as the cascade order from low to high resolution. The first Unet generates the base resolution; later Unets super-resolve from the previous output.
- `Decoder.sample(...)` needs `image_embed` unless `unconditional=True`.
- `cond_scale` can be a scalar or one value per Unet. Values other than `1` require decoder training with conditional dropout.
- `learned_variance`, `predict_x_start`, `predict_v`, `beta_schedule`, `sample_timesteps`, and VAE choices must match checkpoint training settings.

### CLIP adapters

```python
OpenAIClipAdapter(name='ViT-B/32')
OpenClipAdapter(name='ViT-B/32', pretrained='laion400m_e32')
```

- `OpenAIClipAdapter` uses the `clip-anytorch` package and OpenAI CLIP model names such as `ViT-B/32` or `ViT-L/14`.
- `OpenClipAdapter` uses `open-clip-torch` model/pretrained pairs such as `OpenClipAdapter('ViT-H/14')` with the default pretrained setting or an explicit compatible pretrained tag.
- Both adapters can download weights and therefore may need network access or a pre-populated cache. Do not use them in no-network smoke tests unless the weights are already cached.
- Adapter properties used by prior/decoder include `dim_latent`, `image_size`, `image_channels`, and `max_text_len`.
- The package also exports `CLIP` from `x_clip`; passing that object to prior/decoder wraps it in an internal adapter.

### `VQGanVAE`

```python
VQGanVAE(
    dim,
    image_size,
    channels=3,
    layers=4,
    l2_recon_loss=False,
    use_hinge_loss=True,
    vgg=None,
    vq_codebook_dim=256,
    vq_codebook_size=512,
    vq_decay=0.8,
    vq_commitment_weight=1.0,
    vq_kmeans_init=True,
    vq_use_cosine_sim=True,
    use_vgg_and_gan=True,
    vae_type='resnet',
    discr_layers=4,
    **kwargs,
)
```

Use `VQGanVAE` as optional latent-diffusion VAE entries in `Decoder(vae=(...))`. See [latent-diffusion-and-vqgan.md](latent-diffusion-and-vqgan.md) before enabling it.

## Forward and sampling shape notes

- Prior training loss without CLIP: `prior(text_embed=torch.randn(batch, dim), image_embed=torch.randn(batch, dim))`.
- Decoder training loss without CLIP: `decoder(images, image_embed=torch.randn(batch, image_embed_dim))`, where `images` is `[batch, channels, H, W]` in `[0, 1]` by default.
- Decoder sampling: `decoder.sample(image_embed=image_embed, text=token_ids_or_none, cond_scale=...)` returns image tensors.
- Inpainting sampling: additionally pass `inpaint_image` `[batch, channels, H, W]` and `inpaint_mask` `[batch, H, W]` boolean. `True` means keep that inpaint-image region.
- Chained generation: `dalle2("prompt", cond_scale=2., prior_cond_scale=1.)` returns one image tensor for a single prompt, a batch tensor for prompt lists, or PIL images if `return_pil_images=True`.
