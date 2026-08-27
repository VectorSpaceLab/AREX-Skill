# Model Reference

This guide covers raw fastMRI model classes exposed by `fastmri.models`. It intentionally stops before dataset HDF5 loading, Lightning training/test loops, and reconstruction metric/submission handling.

## Imports and Classes

```python
from fastmri.models import AdaptiveVarNet, NormUnet, Unet, VarNet
from fastmri.models.policy import LOUPEPolicy, StraightThroughPolicy
```

The package exports `AdaptiveVarNet`, `StraightThroughPolicy`, `Unet`, `NormUnet`, `SensitivityModel`, `VarNet`, and `VarNetBlock` from `fastmri.models`.

## Constructor Signatures

- `Unet(in_chans: int, out_chans: int, chans: int = 32, num_pool_layers: int = 4, drop_prob: float = 0.0)`
- `NormUnet(chans: int, num_pools: int, in_chans: int = 2, out_chans: int = 2, drop_prob: float = 0.0)`
- `VarNet(num_cascades: int = 12, sens_chans: int = 8, sens_pools: int = 4, chans: int = 18, pools: int = 4, mask_center: bool = True)`
- `AdaptiveVarNet(budget: int = 22, num_cascades: int = 12, sens_chans: int = 8, sens_pools: int = 4, chans: int = 18, pools: int = 4, cascades_per_policy: int = 1, loupe_mask: bool = False, use_softplus: bool = True, crop_size: Tuple[int, int] = (128, 128), num_actions: Optional[int] = None, num_sense_lines: Optional[int] = None, hard_dc: bool = False, dc_mode: str = "simul", slope: float = 10, sparse_dc_gradients: bool = True, straight_through_slope: float = 10, st_clamp: bool = False, policy_fc_size: int = 256, policy_drop_prob: float = 0.0, policy_num_fc_layers: int = 3, policy_activation: str = "leakyrelu")`
- `LOUPEPolicy(num_actions: int, budget: int, use_softplus: bool = True, slope: float = 10, sampler_detach_mask: bool = False, straight_through_slope: float = 10, fix_sign_leakage: bool = True, st_clamp: bool = False)`

## Choosing U-Net vs VarNet

Use `Unet` when the input already looks like an image tensor, usually after a data transform has converted k-space into normalized image-domain tensors. The raw module expects a 4D tensor shaped `(batch, in_chans, height, width)` and returns `(batch, out_chans, height, width)`. Repository tests instantiate it as `Unet(in_chans=num_chans, out_chans=..., chans=..., num_pool_layers=2)` and only require that the output channel count matches `out_chans`.

Use `VarNet` for end-to-end multicoil reconstruction from masked k-space. The raw module expects complex k-space shaped `(batch, coils, height, width, 2)`, a broadcastable mask shaped like `(batch, 1, 1, width, 1)`, and optional `num_low_frequencies`. It returns a real RSS reconstruction shaped `(batch, height, width)`. Repository tests instantiate it as `VarNet(num_cascades=2, sens_chans=4, sens_pools=2, chans=..., pools=2, mask_center=...)` and verify that output spatial shape matches the input height/width.

`VarNet` is multicoil-oriented because it estimates coil sensitivity maps before the cascade blocks. For singlecoil/multicoil challenge preprocessing, route transform decisions to `../data-loading/`; for `UnetModule`/`VarNetModule` training, route to `../lightning-training/`.

## Shape Expectations

### U-Net

```python
import torch
from fastmri.models import Unet

model = Unet(in_chans=1, out_chans=1, chans=8, num_pool_layers=2, drop_prob=0.0).eval()
image = torch.zeros(1, 1, 32, 32)
with torch.no_grad():
    output = model(image)
assert output.shape == (1, 1, 32, 32)
```

`Unet` can handle odd input dimensions by reflect-padding decoder outputs before concatenation, but extremely small images can fail once repeated pooling collapses spatial dimensions. For smoke checks, keep height/width comfortably larger than `2 ** num_pool_layers`, such as `32x32` for two pools.

### NormUnet

```python
import torch
from fastmri.models import NormUnet

model = NormUnet(chans=4, num_pools=2, in_chans=2, out_chans=2, drop_prob=0.0).eval()
x = torch.randn(1, 1, 32, 32, 2)
with torch.no_grad():
    output = model(x)
assert output.shape == x.shape
```

`NormUnet` requires a complex-valued final dimension of size `2`; it raises `ValueError("Last dimension must be 2 for complex.")` otherwise. Internally it converts complex channels to a channel dimension, normalizes by batch and real/imag group, pads height and width to multiples of 16, applies `Unet`, unpads, and restores the final complex dimension.

### VarNet

```python
import torch
from fastmri.models import VarNet

model = VarNet(num_cascades=2, sens_chans=4, sens_pools=2, chans=4, pools=2, mask_center=True).eval()
masked_kspace = torch.randn(1, 4, 32, 32, 2)
mask = torch.zeros(1, 1, 1, 32, 1, dtype=torch.bool)
mask[..., 14:18, :] = True
with torch.no_grad():
    output = model(masked_kspace * mask, mask, num_low_frequencies=4)
assert output.shape == (1, 32, 32)
```

The mask must align with the width dimension of k-space. Both boolean masks and `mask.byte()` are common in this codebase; repository tests pass `mask.byte()`. When `mask_center=True`, the sensitivity model masks the center of k-space. If `num_low_frequencies` is omitted or `0`, it infers the dense low-frequency region from `mask[:, 0, 0, :, 0]`; pass an explicit integer when debugging a known mask to avoid inference surprises.

### AdaptiveVarNet and Policy Modules

`AdaptiveVarNet` takes `(kspace, masked_kspace, mask)` and returns `(output, extra_outputs)`, where `output` is a real RSS reconstruction and `extra_outputs` contains lists such as masks, probability masks, sensitivity maps, and intermediate reconstructions. It starts from low-frequency lines, optionally applies a `LOUPEPolicy` or learned `StraightThroughPolicy`, and runs adaptive cascade blocks.

Use small CPU smoke checks only for construction and minimal forward compatibility. Real adaptive/feature VarNet examples document separate dependency expectations and may require older PyTorch Lightning versions, GPU-oriented settings, and example-specific requirements.

`LOUPEPolicy` is a standalone acquisition policy with trainable sampler parameters shaped by `num_actions` and `budget`. Its `forward(mask, kspace)` returns `(mask, masked_kspace, final_prob_mask)`. The mask and k-space width must match `num_actions`, and fully sampled or impossible budgets can trigger sampling/probability failures.

## TorchScript Evidence

Repository tests compile both:

```python
torch.jit.script(Unet(in_chans=1, out_chans=1, chans=8, num_pool_layers=2, drop_prob=0.0))
torch.jit.script(VarNet(num_cascades=4, pools=2, chans=8, sens_pools=2, sens_chans=4))
```

Treat this as evidence that the core U-Net and VarNet module definitions are scriptable in the tested environment. Do not assume the example inference scripts, Lightning modules, or adaptive policy training flows are covered by the same TorchScript smoke tests.

## Mask Names and Low-Frequency Handling

Use exact mask class names when diagnosing architecture failures that originate in preprocessing:

- `RandomMaskFunc` randomly selects outer k-space columns after dense center sampling.
- `EquiSpacedMaskFunc` samples equally spaced lines; with a dense center, actual acceleration can exceed the requested acceleration.
- `EquispacedMaskFractionFunc` adjusts spacing to approximately match requested acceleration, but its own documentation warns that samples may not be perfectly equispaced.

For VarNet model debugging, the key architecture interface is the mask tensor, not the mask function object. The model sees only `masked_kspace`, `mask`, and optional `num_low_frequencies`.
