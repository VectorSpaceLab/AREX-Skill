---
name: data-generation
description: "Route safe, reproducible PDEBench simulation generation, Hydra/JAX
  configuration, and postprocessing without launching unbounded jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PDEBench data generation

Use this sub-skill when a researcher needs to inspect, configure, or deliberately
run PDEBench simulation generators. It covers the classical generators and the
NLE Hydra/JAX families. It is a routing skill, not a request to regenerate the
published benchmark.

## Start with a safe route

Before running anything, record:

1. the family and entry point (classical diffusion/sorption, diffusion/reaction,
   incompressible Navier–Stokes, radial dam break, or NLE advection, Burgers,
   reaction-diffusion/Darcy, compressible CFD);
2. the exact config group/file and overrides;
3. the intended sample count, grid, final time, save interval, output directory,
   and device/backend;
4. whether the desired artifact is per-sample HDF5, NLE `.npy`, or a merged
   HDF5 file; and
5. whether this is help/config inspection, a tiny fixture, or an approved
   production run.

Default to help-only or config rendering. Copy outputs into a new, explicitly
named directory. Never start a family-wide shell loop, upload, or merge as a
verification shortcut. The top-level classical wrappers contain hard-coded
large sample ranges (1,000, 10,000, or 10,000 samples); NLE `run_*.sh` files
also contain multi-GPU loops and can create very large arrays.

Read the relevant internal runbook before proceeding:

- [workflows and commands](references/workflows.md)
- [data and output formats](references/data-formats.md)
- [troubleshooting and boundaries](references/troubleshooting.md)

The runbook distinguishes commands that work through installed package modules
from source-evidence-only facts. No published checkout, native config tree, or
native generator script is bundled by this skill.

## Installed-package entry-point policy

The classical diffusion-reaction and diffusion-sorption wrappers are importable
package modules. After installing PDEBench and its declared runtime
requirements, use commands such as:

```bash
python -m pdebench.data_gen.gen_diff_react --help
python -m pdebench.data_gen.gen_diff_sorp --cfg job --resolve
```

The radial-dam-break wrapper is also a package module, but importing it requires
the optional Clawpack stack. The incompressible Navier–Stokes wrapper and the
NLE programs currently use bare native-layout imports (`src` or `utils`), so
there is no verified installed-package-safe execution command for those
programs in this skill. Their names, configs, and numerical controls below are
source evidence only. Do not make a future agent change directory to a native
family directory or copy a native script path into a runtime command. Use the
bounded format checks in [data and output formats](references/data-formats.md)
and the dependency/merge diagnosis in [troubleshooting](references/troubleshooting.md)
as the bundled alternatives; a user-owned adapter is required for an NLE run.

## Family router

- **Classical 1D diffusion-sorption:** package module
  `pdebench.data_gen.gen_diff_sorp`, using the `diff-sorp` Hydra config group.
  The solver evidence is the importable helper
  `pdebench.data_gen.src.sim_diff_sorp`.
- **Classical 2D diffusion-reaction:** package module
  `pdebench.data_gen.gen_diff_react`, using the `diff-react` config group.
  The solver evidence is `pdebench.data_gen.src.sim_diff_react`.
- **Classical 2D incompressible Navier–Stokes:** the native wrapper is source
  evidence only because its runner imports a bare `src` module. The route needs
  optional phiflow/`phi` and a compatible backend.
- **Classical 2D radial dam break/shallow water:** package module
  `pdebench.data_gen.gen_radial_dam_break`, using the `radial_dam_break` config
  group. This route needs optional Clawpack.
- **NLE JAX:** the source-evidence program families are AdvectionEq, BurgersEq,
  ReactionDiffusionEq, and CompressibleFluid. Their native Hydra programs use
  a bare `utils` import and are not promised as installed-package entry points.
  Single-solution programs use an `args` config group; batched programs use a
  `multi` group.
- **Darcy merge path:** the source-evidence 2D reaction-diffusion program is
  used by the native Darcy production loop. Treat it as an NLE production loop,
  not as a small Darcy test.
- **Postprocessing:** the package module
  `pdebench.data_gen.data_gen_NLE.Data_Merge` is parser-inspectable when Hydra
  and the package data are installed, but its merge implementation has known
  defects documented in the runbook. Merge is not default verification.

Dataset retrieval, plotting/visualization, and velocity-to-vorticity conversion
belong to the `data-and-download` route. FNO/U-Net/PINN/inverse training and
metrics belong to `models-and-evaluation`. Notebooks, attic helpers, CI/release
files, credentials, and network upload are not runtime dependencies here.

## Minimum safe checks

With the public package installed, first prefer:

```bash
python -m pdebench.data_gen.gen_diff_react --help
python -m pdebench.data_gen.gen_diff_sorp --cfg job --resolve
```

Use the equivalent module-qualified help/config check for a selected classical
package wrapper. For radial dam break, check that Clawpack is installed before
importing the module. NLE and incompressible-NS commands are not listed as
copyable runtime commands because their current native imports are not
self-contained after package installation.

A help/config check must not be described as a generated dataset. The recorded
verification baseline for the generated skill was Python 3.10 with Hydra 1.3.5,
CPU JAX 0.4.38, and NumPy 1.26.4. This revision's live shell probe used Python
3.13 and found Hydra and JAX unavailable, so those checks were not rerun here;
that live fact is a limitation, not a successful package verification.

## Omission and verification boundary

This skill does not retrieve datasets, inspect network repositories, upload to
Dataverse, repair source bugs, run the full benchmark generation suite, or
certify numerical fidelity to the paper. Full generation, NLE runs, merge,
large output production, upload, and credential use all require an explicit
user-approved scope and an environment check. If a requested action crosses
those limits, explain the cost and route it for approval rather than silently
launching it.
