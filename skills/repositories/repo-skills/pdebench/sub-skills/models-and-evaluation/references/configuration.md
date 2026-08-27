# Hydra configuration and execution modes

## Entry points and working directory

Forward dispatch is the installed module
`pdebench.models.train_models_forward`; it uses Hydra with `config_path="config"`
and a default config name tied to the package (default `config_rdb`). It
dispatches `args.model_name` to the FNO, U-Net, or PINN `run_training` function.
The package-qualified example pattern is:

```bash
python -m pdebench.models.train_models_forward +args=config_Adv.yaml \
  ++args.filename='1D_Advection_Sols_beta4.0.hdf5' \
  ++args.model_name='FNO'
```

Inverse dispatch is the installed module
`pdebench.models.train_models_inverse` with `config_path="config"` and config
name `config`; the dedicated inverse module uses its own package-relative
configuration. The published shell workflows are configuration provenance,
not safe launchers: they enumerate many GPU jobs and must not be run without
explicit authorization.

Hydra can change the process working directory. The repository configs set
`hydra.output_subdir: null` and `hydra.run.dir: .`, but relative data paths
remain fragile. Prefer a user-supplied absolute path for `data_path`,
`base_path`, and PINN `root_path`, or make the local approved adaptation to
resolve the path with Hydra's `to_absolute_path` before dataset construction.
The FNO and U-Net utilities use different path expressions (`Path(resolve()) /
filename` versus string concatenation followed by `resolve()`), so do not
assume the same relative-path behavior.

## Shared forward keys

These keys are passed by `train_models_forward.py` into FNO/U-Net/PINN
trainers as applicable:

| Key | Meaning and checks |
|---|---|
| `model_name` | Exactly `FNO`, `Unet`, or `PINN` in the forward dispatcher. |
| `if_training` | `true` enters epoch loops; `false` loads the expected checkpoint, evaluates, and writes metrics. |
| `continue_training` | Restores model and optimizer state from the model checkpoint; do not enable without a matching checkpoint. |
| `num_workers`, `batch_size` | PyTorch loader settings; use `0` when multiprocessing is troublesome. |
| `initial_step` | Number of context time steps. It must be available in the data and is folded into FNO/U-Net input channels. |
| `t_train` | Last time index used by the training loop; it is clipped to available `nt`. |
| `model_update` | Epoch interval for validation/checkpoint evaluation; keep positive. |
| `filename` | Dataset filename expected by the selected adapter. It must match the actual file and extension. |
| `single_file` | `true` selects `*DatasetSingle`; `false` selects the multi-seed adapter. The source README calls out diffusion-reaction, diffusion-sorption, and radial dam break as `false` cases. |
| `reduced_resolution`, `reduced_resolution_t`, `reduced_batch` | Spatial, temporal, and sample downsampling factors. Check resulting grid sizes against FNO modes and U-Net pooling. |
| `epochs`, `learning_rate`, `scheduler_step`, `scheduler_gamma` | Training controls; they are irrelevant to safe evaluation but can make a run long or expensive. |
| `plot`, `channel_plot`, `x_min`, `x_max`, `y_min`, `y_max`, `t_min`, `t_max` | Evaluation plotting controls. Disable plots for headless smoke/CI checks. |
| `training_type` | FNO/U-Net `autoregressive` rollout or `single` next-step mode. |

The forward FNO call receives `data_path` as `base_path`; the U-Net call does
the same. Some older configs use `data_path`, while the shared config and
inverse path use `base_path`. Normalize the spelling at the entry point rather
than adding an unrelated key.

## FNO-specific keys

```yaml
model_name: FNO
num_channels: 1        # physical variables/channels
modes: 12              # used for modes1/2/3 by the trainer
width: 20
initial_step: 10
training_type: autoregressive
```

The direct constructor defaults are dimension-specific:
`FNO1d(..., modes=16, width=64)`, `FNO2d(..., modes1=12, modes2=12,
width=20)`, and `FNO3d(..., modes1=8, modes2=8, modes3=8, width=20)`. The
training dispatcher passes one `modes` value into all spatial mode arguments
for 2D/3D. Choose modes below the post-reduction spatial Fourier support.

A single-file forward model names its checkpoint from `filename[:-5] +
"_FNO.pt"`; a multi-file model uses `filename + "_FNO.pt"`. Evaluation
expects that file in the active run directory unless the caller has adapted
path handling.

## U-Net-specific keys

```yaml
model_name: Unet
in_channels: 1
out_channels: 1
ar_mode: true
pushforward: true
unroll_step: 20
initial_step: 10
training_type: autoregressive
```

`ar_mode` selects autoregressive training; with `pushforward: true`, the model
name includes `-PF-<unroll_step>`. With `pushforward: false`, it uses `-AR`.
With `ar_mode: false`, it uses `-1-step`. A single-step `training_type` uses
`in_channels`; autoregressive mode constructs `in_channels * initial_step`
input channels. The generated checkpoint name includes the selected suffix,
so evaluation must repeat the same flags.

Four pooling stages make spatial divisibility a practical requirement. Start
with spatial dimensions divisible by 16, then reduce resolution deliberately
if memory is a constraint. `batch_size` is used in several loss reshapes in
the source; ensure the actual final batch behavior is compatible or use a
local approved fix before unusual batch sizes.

## PINN-specific keys

```yaml
model_name: PINN
scenario: pde1D             # also diff-react, diff-sorp, swe2d, CFD2D, CFD3D
filename: 1D_Advection_Sols_beta0.1.hdf5
root_path: data              # prefer an absolute user-owned path
input_ch: 2
output_ch: 1
epochs: 15000
learning_rate: 1.e-3
model_update: 500
val_num: 10
if_periodic_bc: true
aux_params: [0.1]
seed: "0000"
```

`aux_params` supplies equation parameters (for example advection beta,
reaction-diffusion nu/rho, Burgers nu, or CFD gamma) and must match the
filename/scenario. `val_num: 1` takes the single-run branch and writes a
pickle/plot; larger values iterate validation batch indices. PINN training
constructs DeepXDE collocation and boundary/initial constraints and is always
data- and compute-dependent. Do not interpret the config example as a
request to run 15,000 epochs.

## Inverse keys and model/checkpoint preparation

The shared inverse config uses:

| Key | Role |
|---|---|
| `base_path` | Root used for dataset and checkpoint/result names; keep it consistent and preferably absolute. |
| `filename` | Dataset file; the inverse trainer first loads its test split. |
| `model_name` | Forward predictor family, `FNO` or `Unet`/`UNET`. |
| `in_channels`, `out_channels`, `num_channels`, `modes`, `width`, `initial_step` | Must recreate the forward checkpoint architecture. |
| `t_train` | Observation time index; the trainer uses `yy[..., t_train:t_train+1, :]`. |
| `num_samples_max`, `reduced_resolution`, `reduced_resolution_t`, `reduced_batch` | Bound inverse data and match the checkpoint's preprocessing. |
| `inverse_model_type` | `InitialConditionInterp` for gradient optimization or `ProbRasterLatent` for Pyro NUTS. |
| `in_channels_hid` | Hidden/latent spatial resolution used by the inverse implementation. |
| `inverse_epochs`, `inverse_learning_rate`, `inverse_verbose_flag` | Gradient inverse controls. |
| `mcmc_num_samples`, `mcmc_warmup_steps`, `mcmc_num_chains` | Pyro NUTS controls; potentially very long and memory-intensive. |
| `training_type` | Retained in configs for forward predictor mode; verify the actual checkpoint was produced with the same rollout contract. |

The inverse trainer's `load_model` expects a checkpoint dictionary containing
`model_state_dict`; it also restores the model to the selected device and
evaluation mode. It derives the checkpoint name from `filename[:-5] + "_" +
model_name + ".pt"`. Never use `continue_training` or an inverse method as a
substitute for a missing or architecture-mismatched forward checkpoint.

## Device policy and safe commands

Model modules select `cuda` when available and otherwise `cpu`. Set `SKILL_ROOT` to this sub-skill directory. A safe model construction check
is:

```bash
python "$SKILL_ROOT/scripts/model_smoke.py" --help
python "$SKILL_ROOT/scripts/model_smoke.py"
```

A real command may be user-authorized only after paths, data, and checkpoint
existence are confirmed. Do not add a training launcher here. On CPU, lower
spatial resolution, width, batch size, and worker count; FNO 3D, U-Net 3D,
PINN autodiff, and MCMC can exceed practical memory/time quickly. On GPU,
select devices explicitly at the caller and verify the PyTorch CUDA build;
`CUDA_VISIBLE_DEVICES` in the example shell file is not a portable default.
