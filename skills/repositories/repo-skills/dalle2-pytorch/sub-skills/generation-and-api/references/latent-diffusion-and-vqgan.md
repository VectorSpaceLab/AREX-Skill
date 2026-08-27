# Latent diffusion and VQGAN guidance

DALLE2-pytorch 1.15.6 can run decoder stages in latent space by attaching `VQGanVAE` objects to `Decoder(vae=...)`. Treat this as an optional advanced generation path, not the default smoke-test path.

## When to use latent diffusion

Use latent diffusion when you intentionally want one or more decoder Unets to denoise VQGAN feature maps instead of RGB pixels, usually to reduce pixel-space compute at high resolution. A common pattern is:

- Unet 1: base latent diffusion.
- Unet 2: latent or pixel-space super-resolution.
- Later Unets: pixel-space high-resolution refinement.

The `vae` tuple aligns by Unet position. Missing entries are padded with a null VAE, meaning pixel-space diffusion for those stages.

## Minimal object relationship

```python
from dalle2_pytorch import VQGanVAE, Unet, Decoder

vae1 = VQGanVAE(
    dim=64,
    image_size=256,
    layers=4,
    use_vgg_and_gan=False,  # safer for experiments that should not download VGG weights
)

unet1 = Unet(dim=64, image_embed_dim=512, cond_dim=128, dim_mults=(1, 2, 4))
unet2 = Unet(dim=64, image_embed_dim=512, cond_dim=128, dim_mults=(1, 2, 4))

decoder = Decoder(
    unet=(unet1, unet2),
    image_sizes=(64, 256),
    vae=(vae1,),          # latent diffusion for unet1; unet2 uses pixel-space default
    timesteps=1000,
    sample_timesteps=(250, 50),
    predict_x_start_for_latent_diffusion=True,
)
```

The actual dimensions, codebook size, and Unet widths must match the trained checkpoint. The example is a relationship sketch, not a recommendation for high-quality outputs.

## `VQGanVAE` public constructor

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

Key points:

- `vae_type='resnet'` and `vae_type='vit'` are the recognized families.
- `use_vgg_and_gan=True` constructs a VGG16 perceptual model by default and may download torchvision weights. Use `use_vgg_and_gan=False` for no-network architecture experiments.
- `encoded_dim` determines the channel width passed to the latent Unet. The decoder internally casts each Unet to the VAE encoded channel width for latent stages.
- `copy_for_eval()` removes discriminator/perceptual components from the evaluation copy used by the decoder.
- `encode(...)` maps images/features to latent feature maps. `decode(...)` vector-quantizes and decodes latent feature maps back to image space.

## Decoder behavior with `vae`

Inside `Decoder.sample(...)` and `Decoder.forward(...)`:

1. Each decoder stage chooses the VAE aligned to the current Unet.
2. If the VAE is a real `VQGanVAE`, the stage is treated as latent diffusion.
3. The sampling shape becomes `[batch, vae.encoded_dim, encoded_h, encoded_w]` instead of `[batch, channels, image_size, image_size]`.
4. Low-resolution conditioning images are encoded through the VAE when needed.
5. Denoised latent maps are decoded before moving to the next stage.

When `predict_x_start_for_latent_diffusion=True`, `Decoder` sets `predict_x_start=True` for stages whose VAE is a real `VQGanVAE`. Keep this setting consistent with training.

## Training caveat: `VQGanVAETrainer`

The package includes `VQGanVAETrainer`, but future agents should not run it by default:

- It is a long-running image autoencoder/GAN training loop.
- It creates datasets from an image folder and writes results/checkpoints.
- If its results folder already contains files, it prompts interactively before deletion: `do you want to clear previous experiment checkpoints and results?`.
- It can instantiate VGG/perceptual and GAN components, increasing compute and download requirements.

If the task is to train VQGAN or integrate VQGAN training into a full experiment, route to training/config guidance and require explicit budget, data, device, and output-location decisions first.

## Practical checklist

Before attaching a VQGAN VAE to a trained decoder:

- Confirm each VAE architecture exactly matches the checkpoint training config.
- Confirm `len(unets) == len(image_sizes)` and VAE tuple order follows the same Unet order.
- Confirm latent Unet checkpoints were trained with the VAE encoded channel count, not raw RGB channel count.
- Avoid no-network environments when `use_vgg_and_gan=True` unless VGG weights are cached.
- Prefer a GPU for any meaningful latent diffusion sampling or VQGAN training.
- Do not treat the tiny CPU runtime checker as proof that latent diffusion will be performant or high-quality.
