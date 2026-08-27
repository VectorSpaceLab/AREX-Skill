# Conditioning and Guidance API Reference

This reference covers guidance-specific APIs in `denoising-diffusion-pytorch` 2.3.1. Install `denoising-diffusion-pytorch` and import from `denoising_diffusion_pytorch`.

## Classifier-free guidance module

```python
from denoising_diffusion_pytorch.classifier_free_guidance import (
    Unet as CFGUnet,
    GaussianDiffusion as CFGGaussianDiffusion,
)
```

### `classifier_free_guidance.Unet`

```python
CFGUnet(dim, num_classes, cond_drop_prob=0.5, init_dim=None, out_dim=None,
        dim_mults=(1, 2, 4, 8), channels=3, learned_variance=False,
        learned_sinusoidal_cond=False, random_fourier_features=False,
        learned_sinusoidal_dim=16, attn_dim_head=32, attn_heads=4)
```

Forward call: `model(x, time, classes, cond_drop_prob=None)`.

- `x` is BCHW image tensor.
- `classes` is an integer tensor shaped `(batch,)` with values in `[0, num_classes - 1]`.
- `cond_drop_prob` controls the probability of replacing class embeddings with a learned null embedding during training.
- The paired CFG diffusion wrapper asserts that `random_or_learned_sinusoidal_cond` is false; do not enable learned/random sinusoidal conditioning here.

### `classifier_free_guidance.GaussianDiffusion`

```python
CFGGaussianDiffusion(model, *, image_size, timesteps=1000, sampling_timesteps=None,
                     objective='pred_noise', beta_schedule='cosine',
                     ddim_sampling_eta=1.0, offset_noise_strength=0.0,
                     min_snr_loss_weight=False, min_snr_gamma=5,
                     use_cfg_plus_plus=False)
```

Methods:

```python
loss = diffusion(img, classes=labels, loss_reduction='mean')
samples = diffusion.sample(classes=labels, cond_scale=6.0, rescaled_phi=0.7)
mixed = diffusion.interpolate(x1, x2, classes=labels, t=None, lam=0.5)
```

- `sample()` returns one image per class label with shape `(labels.shape[0], channels, image_size, image_size)`.
- `cond_scale > 1` strengthens the conditioned direction.
- `rescaled_phi > 0` blends variance-rescaled guidance to reduce overexposure at high guidance scales.
- `use_cfg_plus_plus=True` changes the CFG sampler prediction path and is an advanced sampling option, not a training-loss switch.

## External classifier-gradient guidance module

```python
from denoising_diffusion_pytorch.guided_diffusion import Unet, GaussianDiffusion
```

This path uses an unconditional image diffusion model plus a user-supplied gradient function.

```python
sample = diffusion.sample(batch_size=4, cond_fn=classifier_cond_fn,
                          guidance_kwargs={'classifier': classifier,
                                           'y': labels,
                                           'classifier_scale': 1.0})
```

`cond_fn(x, t, **guidance_kwargs)` must return a tensor gradient with the same shape, device, and floating dtype family as `x`. A typical value is `grad(log p(y | x_t))`:

```python
def classifier_cond_fn(x, t, classifier, y, classifier_scale=1.0):
    with torch.enable_grad():
        x_in = x.detach().requires_grad_(True)
        logits = classifier(x_in, t)
        log_probs = logits.log_softmax(dim=-1)
        selected = log_probs[range(len(logits)), y.view(-1)]
        grad = torch.autograd.grad(selected.sum(), x_in)[0]
    return grad * classifier_scale
```

Treat external guidance as a sampling-time operation; the unconditional training loss does not consume labels directly.

## `XMWrapper` multi-candidate loss

```python
from denoising_diffusion_pytorch import XMWrapper
xm = XMWrapper(flow_model, candidates=2, max_batch_size=None,
               random_time_method='random_times', random_time_kwarg='times')
loss = xm(batch_tensor)
```

Behavior:

- `candidates` must be at least 1.
- If `candidates == 1`, it forwards directly to `flow_model`.
- If `candidates > 1`, it finds the first batch tensor, repeats batch-shaped tensor inputs to `(batch * candidates, ...)`, evaluates loss, groups back to `(batch, candidates)`, and returns the mean minimum candidate loss.
- If the call does not include `random_time_kwarg` (default `times`), the wrapper calls `flow_model.random_times(batch)` by default. Base image and 1D diffusion wrappers expose this; CFG/guided wrappers do not.
- `max_batch_size` chunks the expanded candidate batch to reduce memory.
- `xm.sample(*args, **kwargs)` forwards unchanged to `flow_model.sample(...)`; candidates affect loss calls, not sampling.
