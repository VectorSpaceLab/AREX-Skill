# NN API reference

This reference covers the Jittor training-related APIs that matter most when authoring a model or porting a training loop.

## Core layers and containers

| API | Verified signature | Notes |
| --- | --- | --- |
| `nn.Linear` | `Linear(in_features, out_features, bias=True)` | Dense layer used in the scratch training examples. |
| `nn.Conv` | `Conv(in_channels, out_channels, kernel_size, stride=1, padding=0, dilation=1, groups=1, bias=True)` | 2D convolution. |
| `nn.Conv1d` | `Conv1d(in_channels, out_channels, kernel_size, stride=1, padding=0, dilation=1, groups=1, bias=True)` | 1D convolution. |
| `nn.Conv3d` | `Conv3d(in_channels, out_channels, kernel_size, stride=1, padding=0, dilation=1, groups=1, bias=True)` | 3D convolution. |
| `nn.ConvTranspose` | `ConvTranspose(in_channels, out_channels, kernel_size, stride=1, padding=0, output_padding=0, groups=1, bias=True, dilation=1)` | Transposed 2D convolution. |
| `nn.BatchNorm` | `BatchNorm(num_features, eps=1e-05, momentum=0.1, affine=True, is_train=True, sync=True)` | Training-mode normalization layer. |
| `nn.LayerNorm` | `LayerNorm(normalized_shape, eps: float = 1e-05, elementwise_affine: bool = True)` | Normalization helper for features. |
| `nn.GroupNorm` | `GroupNorm(num_groups, num_channels, eps=1e-05, affine=True, is_train=True)` | Group normalization. |
| `nn.Dropout` | `Dropout(p=0.5, is_train=False)` | Mode-sensitive regularization. |
| `nn.Sequential` | `Sequential(*args)` | Container for chained modules. |
| `nn.Parameter` | `Parameter(data, requires_grad=True)` | Explicit parameter wrapper when you need it. |
| `nn.ParameterList` | `ParameterList(*args)` | Holds an ordered parameter collection. |

## Activations and losses

| API | Verified signature | Notes |
| --- | --- | --- |
| `nn.relu` | `relu(x)` | Functional ReLU helper. This release also exposes module-style `Relu`/`ReLU` helpers. |
| `nn.cross_entropy_loss` | `cross_entropy_loss(output, target, weight=None, ignore_index=None, reduction='mean')` | Canonical classification loss. |
| `nn.mse_loss` | `mse_loss(output, target, reduction='mean')` | Standard regression loss. |
| `nn.bce_loss` | `bce_loss(output, target, weight=None, reduction='mean')` | Binary cross-entropy. |
| `nn.l1_loss` | `l1_loss(output, target, reduction='mean')` | Absolute-error loss. |
| `nn.binary_cross_entropy_with_logits` | `binary_cross_entropy_with_logits(output, target, weight=None, reduction='mean')` | Logit-space BCE helper. |

## Optimizers and schedulers

| API | Verified signature | Notes |
| --- | --- | --- |
| `nn.SGD` / `optim.SGD` | `SGD(params, lr, momentum=0, weight_decay=0, dampening=0, nesterov=False)` | Most useful simple optimizer for smoke tests. |
| `optim.Adam` | `Adam(params, lr, eps=1e-08, betas=(0.9, 0.999), weight_decay=0)` | Adaptive optimizer with standard defaults. |
| `optim.AdamW` | `AdamW(params, lr, eps=1e-08, betas=(0.9, 0.999), weight_decay=0)` | AdamW variant. |
| `optim.RMSprop` | `RMSprop(params, lr=0.01, eps=1e-08, alpha=0.99)` | RMSProp variant. |
| `optim.Adan` | `Adan(params, lr=0.001, betas=(0.98, 0.92, 0.99), eps=1e-08, weight_decay=0.0, max_grad_norm=0.0)` | Additional adaptive optimizer. |
| `optim.StepLR` | `StepLR(optimizer, step_size, gamma=0.1, last_epoch=-1)` | Simple epoch-step schedule. |
| `optim.MultiStepLR` | `MultiStepLR(optimizer, milestones=[], gamma=0.1, last_epoch=-1)` | Piecewise step schedule. |
| `optim.ExponentialLR` | `ExponentialLR(optimizer, gamma, last_epoch=-1)` | Exponential decay. |
| `optim.CosineAnnealingLR` | `CosineAnnealingLR(optimizer, T_max, eta_min=0, last_epoch=-1)` | Cosine decay. |
| `optim.ReduceLROnPlateau` | `ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=10, verbose=False, threshold=0.0001, threshold_mode='rel', cooldown=0, min_lr=0, eps=1e-08)` | Metric-driven schedule. |

## Common training semantics

- `Module.execute` is the Jittor forward path. Do not name the main method `forward` and expect it to be called automatically.
- `parameters()` returns the trainable state you should pass to an optimizer.
- `optimizer.step(loss)` is the compact path for a normal training step.
- `optimizer.backward(loss)` is the accumulation path; follow it with `optimizer.step()` when you want to batch multiple mini-steps.
- Call `model.train()` before training and `model.eval()` before validation or inference.
- Use `loss.mean()` or another reduction so `jt.grad` gets a scalar objective.

## Tiny training shape pattern

```python
import jittor as jt
from jittor import nn

model = nn.Sequential(nn.Linear(1, 8), nn.Relu(), nn.Linear(8, 1))
opt = nn.SGD(model.parameters(), 0.1)

x = jt.float32([[0.0], [1.0]])
y = jt.float32([[1.0], [3.0]])
loss = ((model(x) - y) ** 2).mean()
opt.step(loss)
```

That pattern is the smallest useful training loop to keep in mind while reading the recipe and troubleshooting references.