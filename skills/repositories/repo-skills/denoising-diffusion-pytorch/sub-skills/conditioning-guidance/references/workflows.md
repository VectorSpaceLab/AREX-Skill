# Conditioning and Guidance Workflows

Use these recipes after the base image or sequence model has a passing direct loss/sample smoke.

## Classifier-free guidance loss and sample

```python
import torch
from denoising_diffusion_pytorch.classifier_free_guidance import Unet, GaussianDiffusion

num_classes = 10
model = Unet(dim=8, dim_mults=(1,), channels=1, num_classes=num_classes,
             cond_drop_prob=0.5)
diffusion = GaussianDiffusion(model, image_size=8, timesteps=8,
                              sampling_timesteps=4, beta_schedule='cosine')
images = torch.rand(2, 1, 8, 8)
classes = torch.tensor([0, 3], dtype=torch.long)
loss = diffusion(images, classes=classes)
samples = diffusion.sample(classes=classes, cond_scale=2.0, rescaled_phi=0.7)
assert samples.shape == images.shape
```

Use larger `cond_scale` only after basic samples are stable. `rescaled_phi` can reduce overexposure at strong guidance.

## External classifier-gradient guidance

```python
import torch
import torch.nn as nn
from denoising_diffusion_pytorch.guided_diffusion import Unet, GaussianDiffusion

class Classifier(nn.Module):
    def __init__(self, image_size, num_classes):
        super().__init__()
        self.linear = nn.Linear(image_size * image_size, num_classes)
    def forward(self, x, t):
        return self.linear(x.flatten(1))

def cond_fn(x, t, classifier, y, classifier_scale=1.0):
    with torch.enable_grad():
        x_in = x.detach().requires_grad_(True)
        logits = classifier(x_in, t)
        selected = logits.log_softmax(dim=-1)[range(len(logits)), y.view(-1)]
        grad = torch.autograd.grad(selected.sum(), x_in)[0]
    return grad * classifier_scale

model = Unet(dim=8, dim_mults=(1,), channels=1)
diffusion = GaussianDiffusion(model, image_size=8, timesteps=8)
labels = torch.tensor([1, 1])
images = diffusion.sample(batch_size=2, cond_fn=cond_fn,
                          guidance_kwargs={'classifier': Classifier(8, 3),
                                           'y': labels,
                                           'classifier_scale': 1.0})
```

The gradient returned by `cond_fn` must match `x` in shape and device.

## XMWrapper around a base diffusion

Use `XMWrapper` for multi-candidate training loss over a base diffusion/flow model. First follow the image or sequence sub-skill to build the base model, then wrap it:

```python
import torch
from denoising_diffusion_pytorch import Unet1D, GaussianDiffusion1D, XMWrapper

model = Unet1D(dim=8, dim_mults=(1,), channels=1)
diffusion = GaussianDiffusion1D(model, seq_length=8, timesteps=8, sampling_timesteps=4)
xm = XMWrapper(diffusion, candidates=2, max_batch_size=2)
seq = torch.rand(2, 1, 8)
loss = xm(seq)
assert torch.isfinite(loss).item()
```

Memory grows approximately with `batch * candidates` for tensors repeated by the wrapper. Use `max_batch_size` to chunk candidate evaluation.

## Safe smoke script

From the generated skill root:

```bash
python sub-skills/conditioning-guidance/scripts/smoke_conditioning_guidance.py --quick --device cpu --candidates 2 --max-batch-size 2
```

The smoke validates finite XM loss and a tiny CFG loss/sample. It performs no training or data loading.
