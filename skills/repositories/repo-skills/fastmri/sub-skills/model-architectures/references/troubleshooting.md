# Model Architecture Troubleshooting

Use this guide for raw `fastmri.models` instantiation and forward-pass failures. Route HDF5 dataset reads, transform construction, and training-loop failures to the neighboring data-loading and Lightning training sub-skills.

## `ModuleNotFoundError: requests`

`fastmri.data` imports `requests`, but `setup.cfg` does not list `requests` in `install_requires` for this checkout. If an architecture smoke check imports only `fastmri.models`, this may still appear because `VarNet` imports `fastmri.data.transforms` internally.

Fix by installing `requests` in the active environment or by using an environment that includes the repository's test/dev extras. Do not work around this by editing fastMRI runtime imports inside user projects unless the user explicitly asks for a packaging patch.

## U-Net vs VarNet Input Confusion

`Unet` expects image-domain tensors shaped `(batch, channels, height, width)`. It does not accept complex k-space with a final dimension of `2` unless preprocessing has converted that representation into image channels.

`VarNet` expects multicoil masked k-space shaped `(batch, coils, height, width, 2)` plus a mask shaped like `(batch, 1, 1, width, 1)`. It estimates coil sensitivity maps and returns real RSS images shaped `(batch, height, width)`.

If a user asks about singlecoil or multicoil dataset challenge handling, inspect the transform path rather than changing the raw model class. U-Net can be used for singlecoil or multicoil workflows through transforms; VarNet is multicoil-oriented.

## Mask Dtype and Shape Failures

Common VarNet symptoms include `where` dtype errors, broadcast mismatches, bad center-line inference, or output shapes that do not match expected height/width.

Check these first:

```python
assert masked_kspace.shape[-1] == 2
assert mask.shape == (masked_kspace.shape[0], 1, 1, masked_kspace.shape[-2], 1)
mask = mask.bool()  # or mask.byte() for compatibility with older fastMRI tests
output = model(masked_kspace * mask, mask, num_low_frequencies=known_center_lines)
```

The width dimension is `masked_kspace.shape[-2]`, not height. If the mask came from `transforms.apply_mask`, the returned `num_low_frequencies` can be passed directly to `VarNet.forward(..., num_low_frequencies=...)` for clearer sensitivity-map masking.

`mask_center=True` tells `SensitivityModel` to crop k-space to the center for sensitivity estimation. If `num_low_frequencies` is `None` or `0`, the model infers the dense center from `mask[:, 0, 0, :, 0]`; an unusual mask can make that inference surprising. Temporarily set `mask_center=False` or pass explicit `num_low_frequencies` to isolate the issue.

Use exact mask names when tracing preprocessing: `EquiSpacedMaskFunc` and `EquispacedMaskFractionFunc` are different classes.

## Tiny Image and Pooling Constraints

`Unet`, `NormUnet`, and VarNet regularizers downsample repeatedly. Very small height/width values can fail because pooling, normalization, or convolution layers run out of spatial support.

For CPU smoke tests, start with at least `32x32` and `num_pool_layers=2` or `pools=2`. Increase spatial size before increasing pool count. If an odd dimension causes a mismatch, `Unet` has reflect-padding logic in the decoder, but reflect padding still needs enough spatial extent to operate safely.

`NormUnet` pads height and width to multiples of `16`, so a successful `NormUnet` forward should return to the original spatial size after unpadding.

## Checkpoint Key or Challenge Mismatch

If loading a state dict fails:

- Confirm the model class and architecture match the checkpoint. U-Net checkpoints do not load into `VarNet`; VarNet checkpoints require matching cascade/channel/pool parameters.
- Confirm challenge family assumptions. U-Net examples distinguish `unet_knee_sc`, `unet_knee_mc`, and `unet_brain_mc`; VarNet examples distinguish `varnet_knee_mc` and `varnet_brain_mc`.
- Detect Lightning checkpoint wrappers: if the file has a top-level `state_dict`, load that value and strip prefixes such as `unet.` or `varnet.` only after confirming the training module layout.
- Use `torch.load(path, map_location="cpu")` for offline inspection on machines without CUDA.

Avoid `strict=False` until after listing missing and unexpected keys; it can hide a wrong challenge/model pairing.

## CUDA Defaults and Offline Inference

The original pretrained example scripts default to `cuda` and download missing state dict files. For safe agent work:

- Require an explicit local checkpoint path.
- Choose CPU when CUDA is unavailable, or ask before a slow CPU fallback.
- Do not download model weights unless the user explicitly permits network access and destination writes.
- Keep output saving/submission concerns outside this architecture sub-skill.

## AdaptiveVarNet, LOUPE, and Feature VarNet Caveats

Adaptive and feature VarNet examples document separate requirements and recommend separate environments because their expected PyTorch Lightning versions differ from the base fastMRI installation. Treat them as advanced example families, not drop-in replacements for the core `VarNet` path.

For `AdaptiveVarNet`:

- `cascades_per_policy` cannot exceed `num_cascades`.
- If `loupe_mask=True`, `num_actions` must be an integer matching the k-space width.
- `num_sense_lines` must not exceed the actual low-frequency lines present in the mask.
- `dc_mode` must be one of `"first"`, `"last"`, or `"simul"`.

For policy modules:

- `LOUPEPolicy(num_actions, budget, ...)` expects mask and k-space width to match `num_actions`.
- Fully sampled masks or impossible budgets can lead to probability normalization or rejection-sampling failures.
- Policy outputs include updated masks and probability masks; they are useful for acquisition debugging but not direct reconstruction metrics.
