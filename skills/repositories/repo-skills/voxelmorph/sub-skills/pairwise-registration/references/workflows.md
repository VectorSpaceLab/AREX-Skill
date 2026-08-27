# Pairwise Registration Workflows

## Purpose

Use these workflows when a task needs a current PyTorch VoxelMorph pairwise-registration model, a safe synthetic smoke-training loop, or a checkpoint pattern. These examples use installed package APIs and synthetic tensors only; they do not depend on datasets, old TensorFlow scripts, model downloads, or repository-local paths.

## 1. Build a minimal `VxmPairwise` model

```python
import torch
import voxelmorph as vxm

model = vxm.nn.models.VxmPairwise(
    ndim=2,
    source_channels=1,
    target_channels=1,
    nb_features=(4, 4, 4),
    integration_steps=0,
    device="cpu",
)
source = torch.rand(1, 1, 16, 16)
target = torch.rand(1, 1, 16, 16)
field = model(source, target)
assert field.shape == (1, 2, 16, 16)
```

Use `ndim=3` with tensors shaped `(B, C, D, H, W)` and fields shaped `(B, 3, D, H, W)`. Keep the model and all tensors on the same device.

## 2. Request warped outputs and field types

```python
import torch
import voxelmorph as vxm

model = vxm.nn.models.VxmPairwise(
    ndim=2,
    source_channels=1,
    target_channels=1,
    nb_features=(4, 4, 4),
    integration_steps=3,
)
source = torch.rand(1, 1, 16, 16)
target = torch.rand(1, 1, 16, 16)

disp, warped_source = model(
    source,
    target,
    return_warped_source=True,
    return_field_type="displacement",
)
velocity, warped_source, warped_target = model(
    source,
    target,
    return_warped_source=True,
    return_warped_target=True,
    return_field_type="velocity",
)
assert disp.shape == velocity.shape == (1, 2, 16, 16)
assert warped_source.shape == warped_target.shape == source.shape
```

Rules:

- `return_field_type="displacement"` returns the integrated displacement when `integration_steps > 0`; with `integration_steps == 0`, the raw velocity is used as the displacement.
- `return_field_type="velocity"` and `"svf"` return the raw stationary velocity field.
- `return_warped_target=True` requires `integration_steps > 0` because the model needs the inverse integrated field.

## 3. Run a tiny synthetic training step

Use Neurite losses, not `voxelmorph.nn.losses`, because the latter are deprecation stubs in this branch.

```python
import torch
import neurite as ne
import voxelmorph as vxm

torch.manual_seed(7)
model = vxm.nn.models.VxmPairwise(
    ndim=2,
    source_channels=1,
    target_channels=1,
    nb_features=(4, 4, 4),
    integration_steps=1,
)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
image_loss_fn = ne.nn.modules.MSE()
grad_loss_fn = ne.nn.modules.SpatialGradient("l2")

source = torch.rand(1, 1, 16, 16)
target = torch.rand(1, 1, 16, 16)
optimizer.zero_grad(set_to_none=True)
field, warped = model(source, target, return_warped_source=True)
loss = image_loss_fn(target, warped).mean() + 0.01 * grad_loss_fn(field).mean()
loss.backward()
optimizer.step()
assert torch.isfinite(loss)
```

For a direct command-line smoke, run the bundled helper:

```bash
python scripts/tiny_pairwise_training_smoke.py --steps 1 --spatial-size 16 --features 4 4 4
```

## 4. Connect data-generator outputs to the model

The NumPy data generators in the data-generators sub-skill usually emit arrays shaped `(batch, *spatial, features)`, while `VxmPairwise` expects PyTorch tensors shaped `(B, C, *spatial)`. Convert by moving the trailing feature axis to channel position.

```python
import torch
from voxelmorph.py import generators

# Example generator output, where scan arrays are (B, H, W, C) or (B, D, H, W, C).
invols, outvols = next(generators.scan_to_scan(volume_list, batch_size=1, no_warp=True))
source_np, target_np = invols
source = torch.from_numpy(source_np).float().movedim(-1, 1)
target = torch.from_numpy(target_np).float().movedim(-1, 1)
field = model(source, target)
```

Validate `.npz` schemas and shape consistency with the data-generators validator before creating the generator.

## 5. Save and reload portable checkpoints

Prefer a dictionary that contains both architecture config and weights.

```python
import torch
import voxelmorph as vxm

config = {
    "ndim": 2,
    "source_channels": 1,
    "target_channels": 1,
    "nb_features": (4, 4, 4),
    "integration_steps": 1,
}
model = vxm.nn.models.VxmPairwise(**config)
torch.save({"model_config": config, "state_dict": model.state_dict()}, "vxm_pairwise.pt")

payload = torch.load("vxm_pairwise.pt", map_location="cpu")
loaded = vxm.nn.models.VxmPairwise(**payload["model_config"])
loaded.load_state_dict(payload["state_dict"])
loaded.eval()
```

Avoid saving full Python model objects as the primary artifact because they are less portable across VoxelMorph or Neurite revisions.

## 6. Device selection for real workloads

```python
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
source = source.to(device)
target = target.to(device)
field, warped = model(source, target, return_warped_source=True)
```

A CPU environment is enough for synthetic correctness checks. Use a CUDA-capable PyTorch installation only when the user explicitly needs GPU execution for larger data or training performance.

## 7. Handling legacy registration examples

The current package exposes `vxm.nn.models.VxmPairwise`; it does not expose a `vxm.networks` module. If you encounter an old command or script that calls `vxm.networks.VxmDense.load(...)`, do not present it as a runnable path for this branch. Instead:

1. Identify what the user actually has: a current `VxmPairwise` state dict, an old TensorFlow/Keras model, or a third-party checkpoint.
2. If it is a current state dict, reconstruct `VxmPairwise` from a known config and call `load_state_dict()`.
3. If it is an old TensorFlow/Keras `.h5` or a `VxmDense` artifact, state that this PyTorch branch does not provide the loader and ask for the matching branch/package or a converted checkpoint.
4. Use `transform-ops` to apply or inspect predicted fields after a current model forward pass.

## 8. When not to continue automatically

Stop and ask for concrete data/runtime details when the user needs:

- real training beyond a tiny smoke loop,
- a benchmark or paper-level metric,
- a clinical or anatomical quality claim,
- downloading pretrained model weights,
- converting TensorFlow-era checkpoints,
- or running on a required GPU/accelerator that has not been verified.
