# PDEBench data-generation workflows

This is a safety-oriented recipe book. Commands that use an installed
`pdebench.*` module are package-runtime recipes. Statements about NLE program
names, native config choices, and native output naming are source evidence only:
the current NLE programs use a bare `utils` import and are not a
self-contained installed-package interface. No native checkout path is a
runtime dependency of this reference.

## 1. Inspect before execute

After installing PDEBench and Hydra, inspect the package-safe classical
wrappers with module-qualified commands:

```bash
python -m pdebench.data_gen.gen_diff_react --help
python -m pdebench.data_gen.gen_diff_sorp --help
```

A Hydra config rendering is safer than starting a simulation:

```bash
python -m pdebench.data_gen.gen_diff_react \
  --cfg job --resolve mode=debug
python -m pdebench.data_gen.gen_diff_sorp \
  --cfg job --resolve mode=debug
```

These commands only prove parser/config compatibility when they finish. Confirm
the resolved working and output paths, sample range, spatial dimensions, and
time controls before removing the inspection-only flag. Hydra may change the
process working directory for classical wrappers. Resolve paths with
`--cfg job --resolve`; do not infer an output path from the caller's shell
directory alone.

The incompressible-NS runner and all NLE runners are currently source-evidence
only for installed-package use: their implementation imports bare native-layout
modules (`src` or `utils`). Do not turn their native program names into
`python path/to/script.py` commands. The bundled alternatives are the bounded
classical fixtures below and the output/schema checks in [data-formats](data-formats.md).

## 2. Classical generators

### Diffusion-sorption (1D)

The source-evidence config is the `diff-sorp` Hydra group. Its important `sim`
fields are `D`, `por`, `rho_s`, `k_f`, `n_f`, `sol`, `t`, `tdim`, `x_left`,
`x_right`, `xdim`, and `seed`. The checked-in defaults are a 1D grid of 1,024
cells and 501 saved times through `t=500`. The package wrapper currently sets
seeds 0 through 9,999 and creates a multiprocessing pool; `sim.n` does not
replace that range. Treat the wrapper as a production launcher, not a tiny
test.

Safe config inspection:

```bash
python -m pdebench.data_gen.gen_diff_sorp \
  --cfg job --resolve mode=debug \
  sim.xdim=16 sim.tdim=3 sim.t=0.02 sim.seed=0
```

A bounded single-sample solver fixture can use the installed helper directly
without writing HDF5:

```bash
python - <<'PY'
from pdebench.data_gen.src.sim_diff_sorp import Simulator

s = Simulator(t=0.02, tdim=3, xdim=16, seed=0)
a = s.generate_sample()
assert a.shape == (3, 16, 1)
print(a.shape, a.dtype)
PY
```

Use that fixture only when SciPy is available; it exercises one small ODE solve
and does not validate the multiprocessing writer or a benchmark dataset.

### Diffusion-reaction (2D)

Use the package module `pdebench.data_gen.gen_diff_react` and its `diff-react`
Hydra group. The main numerical controls are `Du`, `Dv`, `k`, `t`, `tdim`, x/y
bounds, `xdim`/`ydim`, and the per-sample `seed`. The checked-in defaults are
128 x 128, 101 saved times through `t=5`. The wrapper sets seeds 0 through 999
and opens one HDF5 file from multiple processes. `sim.n` is a helper argument,
not a safe sample-count switch.

Render a small configuration:

```bash
python -m pdebench.data_gen.gen_diff_react \
  --cfg job --resolve mode=debug \
  sim.xdim=8 sim.ydim=8 sim.tdim=3 sim.t=0.02 sim.seed=0
```

A small in-memory fixture is suitable for a CPU smoke test:

```bash
python - <<'PY'
from pdebench.data_gen.src.sim_diff_react import Simulator

s = Simulator(t=0.02, tdim=3, xdim=8, ydim=8, seed=0)
a = s.generate_sample()
assert a.shape == (3, 8, 8, 2)
print(a.shape, a.dtype)
PY
```

Do not substitute this fixture for HDF5 schema or long-time numerical
validation. `solve_ivp` can become expensive quickly as the grid and final time
increase.

### Incompressible Navier–Stokes (2D)

The source-evidence config is `ns_incomp.yaml`; the native runner is not an
installed-package-safe command because it imports a bare `src` module at run
time. Important fields are `domain_size`, `grid_size`, `NU`, `seed`, noise
`smoothness`/`scale`, `force_smoothness`/`force_scale`, `n_steps`, `DT`,
`frame_int`, `n_batch`, `save_h5`, `profile`, `backend`, `device`, and `jit`.
The HDF5 writer allocates arrays for velocity, particles, force, and time; with
defaults it requests 100,000 steps on a 256 x 256 grid. It is not a safe default
run.

Treat native config rendering and execution as source-evidence work requiring a
user-owned adapter. If the adapter is approved, render first with
`grid_size=[8,8]`, `n_steps=4`, `frame_int=2`, `n_batch=1`, `save_h5=false`,
disabled image/GIF output, `device=CPU`, and `jit=false`. If phiflow or the
requested backend is absent, stop at configuration evidence. Do not claim a
small rendering command ran a solver.

### Radial dam break / shallow water (2D)

Use the package module `pdebench.data_gen.gen_radial_dam_break` and the
`radial_dam_break` Hydra group only after Clawpack is installed. Controls
include `T_end`, `n_time_steps`, `xdim`, `ydim`, `gravity`, `dam_radius`,
`inner_height`, and x/y bounds. Defaults are 128 x 128 and 100 time steps; the
wrapper's seed range is 0 through 9,999 and it randomizes `dam_radius` per seed.

The package-qualified inspection command is:

```bash
python -m pdebench.data_gen.gen_radial_dam_break \
  --cfg job --resolve mode=debug \
  sim.xdim=8 sim.ydim=8 sim.n_time_steps=3 sim.T_end=0.02 sim.seed=0
```

This is only config inspection unless Clawpack is installed and a real run has
been approved. The solver imports `clawpack.pyclaw` and `clawpack.riemann` at
module import time. Do not run the checked-in production wrapper just to test
imports; its multiprocessing range is large.

## 3. NLE JAX families — source evidence only

The NLE family programs are not listed as executable recipes here. Their bare
`utils` imports and relative Hydra layout mean that a plain installed-package
module invocation is not currently verified. Do not ask a future agent to
change directory, read a native config path, or execute a native script path.
Use the family facts below to design a separately approved user-owned adapter,
then validate its output with [data-formats](data-formats.md) and
[troubleshooting](troubleshooting.md). No NLE generator wrapper is bundled in
this skill.

The source program identifiers, retained for provenance, are:

- **Advection:** `pdebench.data_gen.data_gen_NLE.AdvectionEq.advection_exact_Hydra`
  and `...advection_multi_solution_Hydra`.
- **Burgers:** `pdebench.data_gen.data_gen_NLE.BurgersEq.burgers_Hydra` and
  `...burgers_multi_solution_Hydra`.
- **Reaction-diffusion:**
  `pdebench.data_gen.data_gen_NLE.ReactionDiffusionEq.reaction_diffusion_Hydra`,
  `...reaction_diffusion_multi_solution_Hydra`, and the 2D variant.
- **Compressible CFD:**
  `pdebench.data_gen.data_gen_NLE.CompressibleFluid.CFD_Hydra` and
  `...CFD_multi_Hydra`.

Single-solution programs select the `args` group; batched programs select the
`multi` group. The following config names and semantics are source evidence,
not a promise that the corresponding files are installed or runnable.

### Advection

Config choices include `beta1e-1`, `beta1e0`, `beta1e1`, `beta2e-1`, `beta2e0`,
`beta4e-1`, and `beta4e0`. `beta` is the advection velocity; `xL`, `xR`, `nx`,
`ini_time`, `fin_time`, `dt_save`, `CFL`, `if_second_order`, `show_steps`,
`numbers`, `init_key`, and `if_rand_param` control the run. The batched code
uses JAX `pmap`/`vmap` and requires `numbers` compatible with the visible device
count. The exact program is the analytic test case; the multi program is a
batch generator.

### Burgers

Config choices include `possin_eps1e-3`, `sin_eps1e-2`, and
`sinsin_eps1e-2_du1` in `args`, with numeric viscosity choices such as `1e-1`
and `1e-2` in `multi`. `epsilon` is the viscosity/diffusion coefficient;
`CFL`, grid bounds/cell count, `fin_time`, `dt_save`, initial-condition mode and
its `u0`/`du`, `show_steps`, `numbers`, and `init_key` determine cost. The code
computes both advective and diffusive time-step limits, so increasing
resolution or reducing `epsilon` can greatly increase work.

### Reaction-diffusion and Darcy

Config choices include `Rho2e0_Nu5e0` and the other `Rho..._Nu...` choices;
2D choices include `config_2D`. `nu` controls diffusion and `rho` the reaction
term; `nx`, `fin_time`, `dt_save`, `CFL`, `numbers`, `init_key`, and save/display
fields bound cost. The 1D code saves `ReacDiff...` arrays. The 2D/Darcy route
has a separate output shape and is not interchangeable with 1D files. The
native Darcy production loop runs 50 multi-GPU jobs and is never an acceptance
test.

### Compressible CFD

Config choices include `1D_ShockTube`, `1D_Multi`, `1D_Multi_shock`,
`2D_KH_M01_dk1`, `2D_Multi_Rand`, `2D_Multi_Turb`, and `3D_TurbM1`.
`nx`, `ny`, `nz`, bounds, `bc`, `gamma`, `eta`, `zeta`, `CFL`, `p_floor`,
`fin_time`, `dt_save`, `numbers`, `init_mode_Multi`, `M0`, `dk`, and `init_key`
determine physics and cost. Boundary modes in solver evidence include
`trans`, `reflect`, and `periodic`; the merge interface accepts only `periodic`
or `trans`. 2D Kelvin–Helmholtz and all 3D configurations are especially
expensive; a 1D small-grid adapter is the sensible first fixture.

## 4. Output control and bounding principles

Use all of the following before approving a real generation:

- lower `numbers`/`nbatch` to the smallest useful value;
- lower `nx`/`ny`/`nz`, `tdim`/`n_time_steps`, `fin_time`/`T_end`, and increase
  `dt_save` only when the requested physics still makes sense;
- disable display, images, GIFs, profiling, and upload (`if_show=0`,
  `save_images=false`, `save_gif=false`, `profile=false`, `upload=false`);
- set a unique `save`/`WORKING_DIR`/`ARTEFACT_DIR` and confirm free disk space;
- keep a fixed `seed` or `init_key` and save the resolved config beside the
  output; and
- run one family/config first, inspect shape/finite values, and only then scale.

Do not rely on a shell timeout as resource control: JAX may compile before the
first output and a process can leave partial files. Stop production before
merging or uploading if the output schema, size, or device behavior is not as
expected.

## 5. Merge recipe and limits

The source-evidence merge module is
`pdebench.data_gen.data_gen_NLE.Data_Merge`. A package-qualified parser check
is safe when Hydra and the package's data files are installed:

```bash
python -m pdebench.data_gen.data_gen_NLE.Data_Merge --help
```

Do not treat parser help as a successful merge. An approved adapter must first
produce a homogeneous `.npy` directory, then pass `args.type`, `args.dim`,
`args.bd`, `args.nbatch`, and `args.savedir` as Hydra overrides to the merge
module. For 1D `advection`, `burgers`, and `ReacDiff`, the source uses
`transform`; for CFD it calls `merge` and expects dimension-specific variables.
The transform/merge code derives HDF5 names and physical attributes from
filenames, so do not mix families or parameter sets in one directory.

This is expensive/destructive postprocessing and is not default verification.
The inspected implementation has apparent runtime defects, including sorting a
`Path.glob` iterator and several misspelled `create_dataset` calls. Perform a
syntax/source audit and a tiny copy of the output directory before trusting a
merge. Do not overwrite the installed package or claim an HDF5 was produced
until a separately approved focused fix passes.
