# Image Generation Workflows

These recipes use synthetic tensors and public API only. Replace tiny dimensions with real `BaseUnet64`, `SRUnet256`, or `SRUnet1024` profiles only on suitable CUDA hardware. A shape-correct sample from untrained random weights is an API check, not a quality result.

## 1. Tiny unconditional API smoke, no text or network path

Use the bundled helper when you only need to verify imports, construction, a loss call, and optional sampling:

From this sub-skill directory, or after resolving the bundled script path:

```bash
python scripts/tiny_image_smoke.py --device auto
python scripts/tiny_image_smoke.py --device cpu --skip-sample
python scripts/tiny_image_smoke.py --family elucidated --num-sample-steps 2
```

Equivalent minimal pattern:

```python
import torch
from imagen_pytorch import Unet, Imagen

unet = Unet(
    dim=8,
    dim_mults=(1, 1),
    num_resnet_blocks=1,
    layer_attns=False,
    layer_cross_attns=False,
    attn_heads=2,
    cond_on_text=False,
)

imagen = Imagen(
    unets=(unet,),
    image_sizes=(16,),
    timesteps=2,
    condition_on_text=False,
    cond_drop_prob=0.0,
)

images = torch.rand(2, 3, 16, 16)
loss = imagen(images, unet_number=1)
loss.backward()

samples = imagen.sample(batch_size=2, cond_scale=1.0, use_tqdm=False)
assert samples.shape == (2, 3, 16, 16)
```

Key safety points:

- Set `condition_on_text=False` on the wrapper and `cond_on_text=False` on the tiny unet.
- Do not pass `texts` or `text_embeds` in unconditional mode.
- Keep `cond_scale=1.0`; classifier-free guidance is for trained conditional models.

## 2. Text-conditioned training with precomputed embeddings

Use precomputed embeddings to avoid text-string encoding during model calls. Route the actual T5/HF embedding production to [data-and-text-conditioning](../../data-and-text-conditioning/SKILL.md).

```python
import torch
from imagen_pytorch import Unet, Imagen

device = "cuda" if torch.cuda.is_available() else "cpu"
text_dim = 768
seq_len = 256
batch = 4

unet1 = Unet(
    dim=32,
    cond_dim=512,
    text_embed_dim=text_dim,
    dim_mults=(1, 2, 4),
    num_resnet_blocks=1,
    layer_attns=(False, True, True),
    layer_cross_attns=(False, True, True),
    attn_heads=4,
)
unet2 = Unet(
    dim=32,
    cond_dim=512,
    text_embed_dim=text_dim,
    dim_mults=(1, 2, 4),
    num_resnet_blocks=(1, 1, 2),
    layer_attns=(False, False, True),
    layer_cross_attns=(False, False, True),
    attn_heads=4,
)

imagen = Imagen(
    unets=(unet1, unet2),
    image_sizes=(64, 128),
    text_embed_dim=text_dim,
    timesteps=(1000, 1000),
    noise_schedules=("cosine", "linear"),
    pred_objectives=("noise", "noise"),
    cond_drop_prob=0.1,
).to(device)

images = torch.rand(batch, 3, 128, 128, device=device)
text_embeds = torch.randn(batch, seq_len, text_dim, device=device)
text_masks = torch.ones(batch, seq_len, dtype=torch.bool, device=device)

for unet_number in (1, 2):
    loss = imagen(
        images,
        text_embeds=text_embeds,
        text_masks=text_masks,
        unet_number=unet_number,
    )
    loss.backward()
```

Sampling with the same embedding dimension:

```python
with torch.no_grad():
    samples = imagen.sample(
        text_embeds=text_embeds[:2],
        text_masks=text_masks[:2],
        cond_scale=3.0,
        use_tqdm=False,
    )
assert samples.shape == (2, 3, 128, 128)
```

Use `texts=[...]` only when T5 model/tokenizer access and cache behavior are intentional.

## 3. Super-resolution-only branch with a `NullUnet` placeholder

Use `NullUnet` when the base generator is unavailable and only the upsampler should be trained. The placeholder keeps cascade indexing and image sizes aligned, but it must be skipped for training and sampling.

```python
import torch
from imagen_pytorch import NullUnet, SRUnet256, Imagen

device = "cuda" if torch.cuda.is_available() else "cpu"
text_dim = 768

base_placeholder = NullUnet()
upsampler = SRUnet256(
    text_embed_dim=text_dim,
    cond_dim=512,
    layer_cross_attns=(False, False, False, True),
)

imagen = Imagen(
    unets=(base_placeholder, upsampler),
    image_sizes=(64, 256),
    text_embed_dim=text_dim,
    timesteps=(250, 250),
    cond_drop_prob=0.1,
).to(device)

high_res = torch.rand(2, 3, 256, 256, device=device)
text_embeds = torch.randn(2, 256, text_dim, device=device)

loss = imagen(high_res, text_embeds=text_embeds, unet_number=2)
loss.backward()

low_res = torch.rand(2, 3, 64, 64, device=device)
sr_samples = imagen.sample(
    text_embeds=text_embeds,
    start_at_unet_number=2,
    start_image_or_video=low_res,
    cond_scale=3.0,
    use_tqdm=False,
)
assert sr_samples.shape == (2, 3, 256, 256)
```

Avoid these mistakes:

- Do not call `imagen(..., unet_number=1)` when unet 1 is `NullUnet`.
- Do not call `imagen.sample(...)` from stage 1 when stage 1 is `NullUnet`.
- Do not set `start_at_unet_number=2` without a low-resolution `start_image_or_video` batch.

## 4. `ElucidatedImagen` / Karras sampling

`ElucidatedImagen` uses the same image/text contracts as `Imagen`, but controls sampling with Karras-style sigma parameters rather than DDPM timesteps.

```python
import torch
from imagen_pytorch import Unet, ElucidatedImagen

device = "cuda" if torch.cuda.is_available() else "cpu"
text_dim = 768

unet = Unet(
    dim=32,
    text_embed_dim=text_dim,
    cond_dim=512,
    dim_mults=(1, 2, 4),
    num_resnet_blocks=1,
    layer_attns=(False, True, True),
    layer_cross_attns=(False, True, True),
    attn_heads=4,
)

imagen = ElucidatedImagen(
    unets=(unet,),
    image_sizes=(64,),
    text_embed_dim=text_dim,
    cond_drop_prob=0.1,
    num_sample_steps=8,
    sigma_min=0.002,
    sigma_max=80,
    sigma_data=0.5,
    rho=7,
    P_mean=-1.2,
    P_std=1.2,
    S_churn=80,
    S_tmin=0.05,
    S_tmax=50,
    S_noise=1.003,
).to(device)

images = torch.rand(2, 3, 64, 64, device=device)  # must be torch.float
text_embeds = torch.randn(2, 256, text_dim, device=device)
loss = imagen(images, text_embeds=text_embeds, unet_number=1)
loss.backward()

samples = imagen.sample(
    text_embeds=text_embeds,
    cond_scale=3.0,
    sigma_min=0.002,
    sigma_max=80,
    use_tqdm=False,
)
```

Per-unet Karras parameters are tuples:

```python
ElucidatedImagen(
    unets=(unet1, unet2),
    image_sizes=(64, 256),
    text_embed_dim=text_dim,
    num_sample_steps=(64, 32),
    sigma_max=(80, 160),
    cond_drop_prob=0.1,
)
```

## 5. Sampling outputs and controls

Common image-only sampling patterns:

```python
# Tensor output from final cascade stage, shape (B, C, H, W)
images = imagen.sample(text_embeds=text_embeds, cond_scale=3.0)

# PIL output for saving individual images
pil_images = imagen.sample(
    text_embeds=text_embeds,
    cond_scale=3.0,
    return_pil_images=True,
)
pil_images[0].save("sample.png")

# Inspect every cascade stage
stage_outputs = imagen.sample(
    text_embeds=text_embeds,
    return_all_unet_outputs=True,
    cond_scale=(3.0, 2.0),
)

# Stop after the base generator
base_only = imagen.sample(
    text_embeds=text_embeds,
    stop_at_unet_number=1,
)

# Image inpainting
inpaint_images = torch.rand(2, 3, 128, 128, device=device)
inpaint_masks = torch.ones(2, 128, 128, dtype=torch.bool, device=device)
inpainted = imagen.sample(
    text_embeds=text_embeds,
    inpaint_images=inpaint_images,
    inpaint_masks=inpaint_masks,
    inpaint_resample_times=5,
    cond_scale=3.0,
)
```

Sampling controls to remember:

- `init_images` and `skip_steps` can be scalars or per-unet tuples for partial denoising starts.
- `lowres_sample_noise_level` defaults to the wrapper value (`0.2`) and affects low-resolution conditioning for upsamplers.
- `cfg_remove_parallel_component=True` and `cfg_keep_parallel_frac=0.0` are the default classifier-free guidance adjustment knobs.
- `use_one_unet_in_gpu=True` moves one unet at a time during CUDA sampling to reduce memory pressure; leave it enabled unless you need all unets resident.

