# Model overview and tensor contracts

## Scope and routing

PDEBench's baseline family contains forward surrogate models (FNO, U-Net,
PINN), a learned-forward-model inverse path, and metric/result utilities. Use
this page for model selection and tensor layouts. Data acquisition, HDF5
creation, and visualization belong elsewhere; this page only states the data
shape that a model expects after the data has already been prepared.

| Need | Prefer | Why / boundary |
|---|---|---|
| Grid-based operator learning with a coordinate grid and rollout | FNO | Spectral layers; autoregressive or single-step training. |
| Local convolutional rollout or pushforward training | U-Net | Channel-first convolutional network; spatial sizes must survive four pooling stages. |
| Physics residuals and coordinate-wise prediction | PINN | DeepXDE MLP plus PDE/initial/boundary constraints; backend-sensitive and long-running. |
| Recover an initial condition from a later observation | Gradient / `InitialConditionInterp` | Optimizes a latent initial field through a frozen forward model. |
| Posterior-like latent initial condition for a 1D spatial case | `ProbRasterLatent` | Pyro NUTS over a raster latent; optional and expensive. |

## Common dataset convention

The FNO and U-Net dataset adapters normalize loaded fields to
`[batch, x1, ..., xd, time, variables]`:

- 1D: `[batch, nx, nt, nc]`
- 2D: `[batch, nx, ny, nt, nc]`
- 3D: `[batch, nx, ny, nz, nt, nc]`

The first item from the FNO/U-Net dataset is the initial context
`[..., :initial_step, :]`; the second is the complete target trajectory. FNO
also returns a coordinate grid with trailing coordinate dimension `d`.
Scalar equations are represented with `nc=1`; multi-variable CFD fields use
one channel per physical variable. The exact HDF5 keys and acquisition
formats are data-skill concerns.

## FNO

Verified constructors:

```text
FNO1d(num_channels, modes=16, width=64, initial_step=10)
FNO2d(num_channels, modes1=12, modes2=12, width=20, initial_step=10)
FNO3d(num_channels, modes1=8, modes2=8, modes3=8, width=20, initial_step=10)
```

Each `forward(x, grid)` concatenates coordinates, lifts with a linear layer,
runs four spectral plus pointwise layers, and returns one next-step field with
an explicit singleton time axis:

| Class | `x` before grid concatenation | `grid` | output |
|---|---|---|---|
| `FNO1d` | `[b, nx, initial_step*nc]` | `[b, nx, 1]` | `[b, nx, 1, nc]` |
| `FNO2d` | `[b, nx, ny, initial_step*nc]` | `[b, nx, ny, 2]` | `[b, nx, ny, 1, nc]` |
| `FNO3d` | `[b, nx, ny, nz, initial_step*nc]` | `[b, nx, ny, nz, 3]` | `[b, nx, ny, 1, nc]` |

The training loop reshapes `[... , initial_step, nc]` to
`[..., initial_step*nc]`, feeds the grid, appends the returned singleton
step, and rolls the context. `training_type: autoregressive` performs this
rollout; `single` uses the first context step and evaluates one selected
future step. Spectral mode counts must fit the transformed spatial sizes;
small CPU smoke cases should choose fewer modes than the grid supports.

## U-Net

Verified constructors:

```text
UNet1d(in_channels=3, out_channels=1, init_features=32)
UNet2d(in_channels=3, out_channels=1, init_features=32)
UNet3d(in_channels=3, out_channels=1, init_features=32)
```

These are standard channel-first modules:

- `UNet1d.forward`: `[b, in_channels, nx] -> [b, out_channels, nx]`.
- `UNet2d.forward`: `[b, in_channels, nx, ny] -> [b, out_channels, nx, ny]`.
- `UNet3d.forward`: `[b, in_channels, nx, ny, nz] -> [b, out_channels, nx, ny, nz]`.

The implementation has four max-pooling stages, transpose-convolution skip
connections, and two-convolution Tanh blocks. For autoregressive training,
the trainer constructs `in_channels * initial_step` input channels by folding
time and variables together; it then permutes from the dataset's
space/time/channel layout to channel-first. For single-step training it uses
`in_channels` rather than `in_channels * initial_step`. Choose spatial sizes
that remain compatible with four factor-two pools (multiples of 16 are the
safe baseline), and ensure the output channel count matches the next-step
variable count.

## PINN and DeepXDE

`pdebench.models.pinn.train.run_training` builds DeepXDE `TimePDE` problems
for `swe2d`, `diff-react`, `diff-sorp`, `pde1D`, `CFD2D`, and `CFD3D`. The
network is a DeepXDE fully-connected tanh network with six hidden layers of
width 40 by default in the setup helpers. Inputs are coordinates plus time:
`[x,t]`, `[x,y,t]`, or `[x,y,z,t]`; outputs are one or more physical fields.
The PDE functions use DeepXDE Jacobian/Hessian operators and the scenario's
initial/boundary/data constraints. `pde_definitions.py` contains advection,
Burgers, reaction-diffusion, diffusion-sorption, shallow-water, and CFD
residual definitions.

Set the DeepXDE backend to PyTorch **before** importing DeepXDE or the PINN
trainer (for example, in the user-approved environment configuration with
`DDE_BACKEND=pytorch`), then verify the backend reported by DeepXDE. This
path is not covered by the CPU smoke script: it creates collocation points
and trains for many iterations when used.

## Inverse model boundaries

The inverse trainer first loads a forward FNO or U-Net checkpoint, freezes
that predictor for the inverse model, and compares a predicted observation
at `t_train` with the observed/scaled field.

- `ElementStandardScaler` stores global mean/std from `fit(x)` and reuses
  them in `transform(x)`; `fit_transform(x)` fits then transforms.
- `ProbRasterLatent(process_predictor, dims=(256,256), latent_dims=(16,16), interpolation="bilinear", prior_scale=0.01, obs_scale=0.01, prior_std=0.01, device=None)` is a `PyroModule`. Its latent is sampled from a normal prior, interpolated to `dims`, and passed to the frozen predictor; `forward(grid, y=None)` exposes the Pyro observation site. The checked trainer restricts this route to one spatial dimension and runs NUTS/MCMC.
- `InitialConditionInterp(dims, hidden_dim)` is a deterministic trainable
  latent field. It uses bilinear interpolation below three spatial dimensions
  and trilinear interpolation for three; `forward()` returns the interpolated
  initial field. Gradient inverse training optimizes this field through the
  frozen predictor.

Inverse inputs use the first time slice as `x` and the configured observation
slice `y = yy[..., t_train:t_train+1, :]`. Check the predictor's expected
layout before adapting a model: the source inverse U-Net wrapper permutes its
input to channel-first and permutes the result back.
