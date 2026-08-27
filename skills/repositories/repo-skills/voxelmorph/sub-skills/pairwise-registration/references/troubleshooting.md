# Pairwise Registration Troubleshooting

## Purpose

Use this guide when VoxelMorph `VxmPairwise` construction, forward calls, synthetic training, or checkpoint usage fails. Route pure transform-coordinate issues to the transform-ops sub-skill and data-layout/file issues to the data-generators sub-skill.

## Common failures and fixes

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `ImportError: voxelmorph requires neurite version 0.3 or greater` | Neurite is missing or too old. | Install the base VoxelMorph dependencies and confirm `import voxelmorph, neurite, torch` works before building models. |
| `NotImplementedError` from `voxelmorph.nn.losses.MSE`, `NCC`, `Dice`, or `Grad` | The VoxelMorph loss classes are deprecated stubs. | Use `neurite.nn.modules.MSE`, `NCC`, `Dice`, or `SpatialGradient` directly. |
| `ValueError: Cannot return warped target image when integration_steps=0` | Inverse target warping needs diffeomorphic stationary-velocity integration. | Rebuild the model with `integration_steps > 0`, or request only the field and/or warped source. |
| `ValueError: return_field_type must be one of ...` | Invalid field type string. | Use exactly `"displacement"`, `"velocity"`, or `"svf"`. |
| `TypeError: got multiple values for keyword argument ...` during construction | `unet_kwargs` duplicates constructor arguments that `VxmPairwise` already passes to Neurite `BasicUNet`. | Remove duplicate keys such as `ndim`, `in_channels`, `out_channels`, `nb_features`, `activations`, and `final_activation` from `unet_kwargs`. |
| PyTorch convolution says expected a different number of channels | `source_channels` or `target_channels` does not match the tensor's channel dimension. | Check that input tensors are `(B, C, *spatial)` and reconstruct the model with matching channel counts. |
| Shape mismatch in UNet skip connections | Spatial dimensions are too small, odd, or incompatible with the selected UNet down/up path. | For smoke tests, use `--spatial-size 16` or larger and small features such as `4 4 4`. For real data, crop/pad/resample consistently before training. |
| Device mismatch such as tensors on CPU and weights on CUDA | Model, source, target, or loss tensors are on different devices. | Move the model and every batch tensor to one `torch.device`. Avoid constructing some tensors after moving only part of the pipeline. |
| CUDA is visible on the host but `torch.cuda.is_available()` is false | CPU-only PyTorch wheel, missing container GPU passthrough, or incompatible driver/runtime. | Use CPU for skill smoke checks. For real GPU work, install a CUDA-capable PyTorch build that matches the host driver and verify a tiny CUDA tensor allocation. |
| `AttributeError: module 'voxelmorph' has no attribute 'networks'` | The current PyTorch package branch does not expose the legacy `vxm.networks.VxmDense` API. | Do not run legacy registration commands as-is. Use `VxmPairwise` with a known config/state dict, or switch to the branch/package that produced the legacy checkpoint. |
| README or old notes mention `scripts/tf/train.py`, `scripts/tf/register.py`, or `.h5` models | Those are TensorFlow-era paths and artifacts, not present in this branch. | Treat them as historical context. Use current `vxm.nn.models.VxmPairwise` APIs or explicitly request the TensorFlow branch. |
| Training script tries to access an institutional OASIS path | The source example's dataset class hardcodes a lab-local OASIS directory. | Do not use that script as a reusable runtime command. Adapt the pattern with your own generator/data loader or run the bundled synthetic smoke helper first. |
| Loss is NaN or diverges immediately | Data contains NaNs/infs, image scales are not normalized, learning rate is too high, or deformations are too large. | Validate arrays with the data-generators validator, normalize intensities, lower learning rate, lower `flow_initializer`, and inspect field magnitude/Jacobian with transform-ops guidance. |
| Checkpoint load reports missing or unexpected keys | The saved architecture config differs from the reconstructed `VxmPairwise` config or package versions changed. | Save/load a payload with `model_config` plus `state_dict`; reconstruct with exactly matching config before `load_state_dict()`. |
| `torch.load()` warns about device or fails on CUDA checkpoint in CPU environment | Checkpoint was saved from a CUDA device or a different environment. | Load with `map_location="cpu"`, then move the model to the desired device after loading. |

## Debugging sequence

1. **Import and version check**

   ```python
   import voxelmorph as vxm
   import neurite as ne
   import torch
   print(vxm.__version__, ne.__version__, torch.__version__)
   ```

2. **Run the bundled synthetic smoke**

   ```bash
   python scripts/tiny_pairwise_training_smoke.py --steps 1 --spatial-size 16 --features 4 4 4
   ```

3. **Check tensor layout**

   - Model images: `(B, C, *spatial)`.
   - Predicted fields: `(B, ndim, *spatial)`.
   - Data-generator arrays often need `.movedim(-1, 1)` before entering the model.

4. **Check model configuration**

   - `ndim` matches the number of spatial dimensions.
   - `source_channels` and `target_channels` match input channels.
   - `integration_steps > 0` if asking for warped target.
   - `unet_kwargs` does not duplicate fixed constructor arguments.

5. **Isolate transform behavior**

   If warped content moves the wrong direction, fields have confusing signs, or interpolation produces boundary artifacts, switch to the transform-ops sub-skill and run its smoke script.

## Stop conditions

Stop and ask for more evidence instead of guessing when:

- the checkpoint architecture is unknown,
- the user wants to load a TensorFlow/Keras `.h5` model in this PyTorch branch,
- real training data is unavailable or private,
- the requested result is a registration-quality metric rather than a smoke check,
- or a required GPU run has not been prepared and verified.
