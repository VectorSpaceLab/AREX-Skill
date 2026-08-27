# Offline Pretrained Inference Adaptation

The original fastMRI U-Net and VarNet example inference scripts are useful references, but they download checkpoints automatically when `state_dict_file` is missing and default the device to `cuda`. Runtime agents should adapt their logic only after making checkpoint and device behavior explicit.

## Offline Safety Rule

Require a user-supplied local checkpoint path before loading weights:

```python
from pathlib import Path

state_dict_file = Path(user_supplied_path)
if not state_dict_file.is_file():
    raise FileNotFoundError(f"Missing state_dict file: {state_dict_file}")
```

Do not copy example behavior that falls back to `requests.get(...)` or writes downloaded state dicts into the working directory. If a user explicitly asks to download pretrained weights, warn that network access is required and make the URL, destination, checksum/provenance, and overwrite behavior explicit.

## U-Net Inference Skeleton

The reference U-Net script uses these challenge names and architecture choices:

- `unet_knee_sc`: singlecoil knee U-Net state dict.
- `unet_knee_mc`: multicoil knee U-Net state dict.
- `unet_brain_mc`: multicoil brain U-Net state dict.
- Model: `Unet(in_chans=1, out_chans=1, chans=256, num_pool_layers=4, drop_prob=0.0)`.
- Transform choice: `UnetDataTransform(which_challenge="multicoil")` when challenge includes `_mc`, otherwise `UnetDataTransform(which_challenge="singlecoil")`.

Minimal safe loading pattern:

```python
import torch
from fastmri.models import Unet

model = Unet(in_chans=1, out_chans=1, chans=256, num_pool_layers=4, drop_prob=0.0)
state = torch.load(state_dict_file, map_location="cpu")
model.load_state_dict(state)
model.eval()
```

The original per-batch helper runs `model(image.to(device).unsqueeze(1)).squeeze(1)`, then unnormalizes with `mean` and `std` from the transform. Keep the transform/data-loader details with `../data-loading/` and the save/submission details with the evaluation/submission skill.

## VarNet Inference Skeleton

The reference VarNet script uses these challenge names and architecture choices:

- `varnet_knee_mc`: multicoil knee VarNet state dict.
- `varnet_brain_mc`: multicoil brain VarNet state dict.
- Model: `VarNet(num_cascades=12, pools=4, chans=18, sens_pools=4, sens_chans=8)`.
- Transform choice: `VarNetDataTransform()` with `SliceDataset(..., challenge="multicoil")`.

Minimal safe loading pattern:

```python
import torch
from fastmri.models import VarNet

model = VarNet(num_cascades=12, pools=4, chans=18, sens_pools=4, sens_chans=8)
state = torch.load(state_dict_file, map_location="cpu")
model.load_state_dict(state)
model.eval()
```

The original per-batch helper runs `model(batch.masked_kspace.to(device), batch.mask.to(device))`, crops with `center_crop`, and includes a FLAIR-203 width adjustment when the output width is smaller than the requested crop width. Keep those crop/save details outside this architecture sub-skill unless the user is specifically debugging model output shapes.

## Device Handling

The example scripts default to `--device cuda`. Prefer a safe selector:

```python
device = torch.device("cuda" if requested_device == "cuda" and torch.cuda.is_available() else "cpu")
```

If the user requested CUDA and it is unavailable, fail clearly or fall back only with consent, because CPU inference on full volumes can be slow.

## Checkpoint Key Mismatches

If `load_state_dict` fails:

- Confirm that the checkpoint is a raw state dict, not a Lightning checkpoint wrapper. Lightning checkpoints often require extracting `checkpoint["state_dict"]` and stripping module prefixes.
- Confirm that the challenge matches the model family: U-Net state dicts do not load into `VarNet`, and knee/brain or singlecoil/multicoil choices may imply different transforms or preprocessing.
- Confirm architecture parameters exactly match the checkpoint, especially U-Net `chans`/`num_pool_layers` and VarNet `num_cascades`, `pools`, `chans`, `sens_pools`, and `sens_chans`.
- Use `map_location="cpu"` for inspection on machines without CUDA.

## Why Scripts Were Not Bundled Directly

The original `run_pretrained_unet_inference.py` and `run_pretrained_varnet_inference.py` scripts import `requests` and auto-download model state dicts if `state_dict_file` is absent. This generated skill keeps them as source evidence only and distills their architecture/loading choices into offline-safe guidance.
