# Troubleshooting and recovery

## Import and backend failures

- `FNO`, `U-Net`, and `metrics` are PyTorch paths. Verify that the installed
  PyTorch can construct `torch.fft` layers on the selected device before a
  data-dependent run.
- `pdebench.models.pinn.train` imports DeepXDE at module import time. Set the
  DeepXDE backend to PyTorch before that import and verify it through DeepXDE's
  backend report. A missing DeepXDE install or a backend mismatch is a
  dependency block, not a reason to silently skip PINN physics.
- `pdebench.models.inverse.inverse` imports Pyro and `inverse/train.py` imports
  Pyro's `MCMC`/`NUTS`. Install and verify Pyro only for an authorized
  `ProbRasterLatent`/inverse run. FNO/U-Net forward smoke checks do not need
  Pyro.
- The inverse dispatcher imports PINN training globally in the checked source;
  therefore an inverse-dispatch import can require DeepXDE even when the
  selected forward predictor is FNO or U-Net. If that blocks a non-PINN
  operation, use the direct model module only after recording the import
  adaptation, or install the declared optional dependency.

## Hydra, cwd, and data paths

- A `FileNotFoundError` after a Hydra launch often means a relative path was
  resolved from Hydra's run directory. Prefer absolute user-provided
  `data_path`/`base_path`/`root_path`; do not invent a repository-relative
  path from the current shell directory.
- FNO's `FNODatasetSingle` resolves `saved_folder` and joins `filename`;
  U-Net's equivalent concatenates `saved_folder + filename`. Ensure the
  caller's separator convention is valid for both or adapt the utility with
  an approved `Path` join.
- The README documents a Hydra path issue in the FNO/U-Net utilities and
  suggests `hydra.utils.to_absolute_path` in the commented utility section.
  Apply that change only in a user-owned checkout/patch; this operating graph
  does not edit the installed package.
- The `single_file` flag must agree with the adapter and actual file format.
  A wrong extension/flag can select an HDF5 layout branch that cannot find
  expected keys (`tensor`, `density`, `pressure`, velocity fields, or grids).

## Shape and layout failures

- Assert dataset shapes before the first model call: `[b, spatial..., nt, nc]`.
  FNO's initial context is flattened to `[b, spatial..., initial_step*nc]`
  and requires a coordinate grid with trailing dimension 1/2/3.
- FNO outputs a singleton time axis. If concatenating rollout steps, append on
  the time dimension `-2`, not the channel dimension.
- U-Net requires channel-first `[b, c, spatial...]`. In autoregressive mode,
  fold the time context into `c`; restore `[b, spatial..., time, variables]`
  only after the model call. Four pooling stages make dimensions smaller than
  16 or not divisible by 16 especially likely to fail at skip concatenation.
- Match `num_channels` to FNO output channels and `in_channels`/
  `out_channels` to U-Net variables. CFD examples use multiple physical
  fields; do not retain scalar defaults for a multi-field file.
- FNO mode counts cannot exceed the available FFT support. Reduce `modes`
  after spatial downsampling; if a custom tiny case fails in a spectral slice,
  use smaller modes rather than padding an unrelated dimension.
- PINN inputs are flattened coordinate rows (`x,t`, `x,y,t`, or
  `x,y,z,t`) and outputs are flattened components. `unravel_tensor` is the
  boundary back to `[1, spatial..., time, components]`; keep
  `n_last_time_steps` and `n_components` consistent.

## Checkpoints and evaluation mode

- `if_training: false` loads `<model-name>.pt` and expects a dictionary with
  `model_state_dict`. Missing files, a wrong current directory, or a model
  suffix mismatch (`_FNO`, `_Unet-1-step`, `_Unet-AR`, `_Unet-PF-N`, or
  `_PINN`) are checkpoint problems.
- `continue_training: true` additionally expects `optimizer_state_dict`,
  `epoch`, and `loss`. If only weights are available, evaluate with
  `continue_training: false` or obtain a compatible full checkpoint.
- Recreate the exact architecture and preprocessing used by the checkpoint:
  dimensions, channels, `initial_step`, FNO modes/width, U-Net AR/pushforward
  suffix, reduction factors, and model name. Do not “fix” a shape mismatch by
  loading with `strict=False` without recording the missing/unexpected keys.
- The inverse loader maps the checkpoint to the auto-selected device and
  switches to eval mode. Confirm the inverse `base_path` points to both the
  forward checkpoint and the intended data/result location.

## CPU/GPU and memory

- Module-level device selection is `cuda` when available, otherwise `cpu`.
  For a reproducible check, construct models explicitly on CPU and use the
  bundled smoke script; it makes no data or checkpoint assumptions.
- Lower `width`, Fourier modes, spatial/temporal resolution, batch size, and
  workers for CPU diagnosis. FNO3d, U-Net3d, DeepXDE autodiff, and Pyro NUTS
  can exhaust memory even with a small batch.
- Some PINN setup helpers create a `torch.Generator(device="cuda")` for a
  random split. On CPU-only execution this can fail before training. Treat it
  as a source compatibility issue requiring a local approved change to a CPU
  generator, not as evidence that the PDE model is invalid.
- Do not claim a GPU result from a CPU fallback or mix devices in grids,
  models, and targets. Log `torch.cuda.is_available()`, model device, and
  tensor devices when debugging.

## Optional dependency boundaries

- DeepXDE is required for PINN construction/training, not for the pure FNO or
  U-Net constructors. Its global backend choice can alter PyTorch behavior;
  import it in an isolated, verified process when possible.
- Pyro is required for `ProbRasterLatent` and MCMC only. The deterministic
  `InitialConditionInterp` path still requires the inverse module and its
  PyTorch dependencies.
- Dataset files, pretrained models, and benchmark downloads are never fetched
  by this skill. Route acquisition to the data skill and require explicit
  authorization for external artifacts.

## Metric and result errors

- `metric_func` uses a module-level device and moves inputs there. Ensure pred
  and target are compatible floating tensors, share shape/layout, and contain
  a nonzero target norm if normalized RMSE is needed. A zero target can make
  the normalized value unstable or uninformative.
- `initial_step` is sliced out before metrics. Passing the wrong value changes
  the reported time window. Fourier `iLow/iHigh` also operate on computed
  frequency bins, so small grids need deliberately chosen bounds.
- The high-level `metrics` helper has no implemented PINN branch. Use the PINN
  trainer's explicit `metric_func` conversion rather than routing a PINN model
  through `mode="PINN"` in that helper.
- The source validation aggregation divides by `itot` after enumeration,
  rather than by the number of batches; a one-batch or small-loader result can
  therefore be wrong or divide by zero. Recompute/inspect with a user-approved
  fix before treating it as a benchmark number.
- Forward analysis parses underscore-separated pickle filenames and scans all
  `*.pickle` in the current directory. Isolate intended files and inspect
  `Results.csv` indices before comparing.
- Inverse result analysis requires the exact generated filename convention and
  expected `pde`, `mean`, `std`, and model columns. Missing files, mismatched
  `inverse_model_type`, or a different column selection are input errors.
- `PINNDataset2Dpde.get_test_data` in the checked source indexes a fourth input
  column where its 2D coordinate input has three columns. If 2D PINN evaluation
  raises an index error, record this known source defect and use a reviewed
  local correction before rerunning; do not silently drop the 2D case.
