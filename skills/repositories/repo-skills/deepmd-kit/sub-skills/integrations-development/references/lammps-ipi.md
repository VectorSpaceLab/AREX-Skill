# LAMMPS and i-PI Integration

This reference distills DeePMD-kit integration behavior for future agents writing or reviewing LAMMPS and i-PI inputs. It is self-contained and does not require the source checkout at runtime.

## LAMMPS Mode Decision

| Mode | When to use | Required setup | Input-script line |
| --- | --- | --- | --- |
| Plugin mode | LAMMPS was built with plugin support and DeePMD-kit provides a separate plugin library | The plugin shared library must be discoverable by explicit load or plugin search path | `plugin load libdeepmd_lmp.so` |
| Built-in mode | LAMMPS was compiled with the USER-DEEPMD package integrated | No `plugin load` line is needed | Start directly with `pair_style deepmd` or `pair_style deepspin` |

Do not assume which mode a user has. Inspect `lmp -h`, check local module documentation, or ask for the execution command when the binary is site-managed.

## Units

- DeePMD-kit supports all LAMMPS unit styles except `lj`.
- Prefer `units metal` because DeePMD-kit internal conventions align with angstrom, eV, eV/angstrom, and proton charge.
- LAMMPS performs unit conversion for supported non-`metal` styles, but tensor outputs can have extra interpretation risk.
- If a user asks for `lj`, explain that the DeePMD-kit LAMMPS integration does not support it and select a physical unit style instead.

## Standard `pair_style deepmd`

Use `pair_style deepmd` for standard Deep Potential energy/force/virial models:

```lammps
units           metal
boundary        p p p
atom_style      atomic
neighbor        2.0 bin
read_data       data.system
mass            1 15.999
mass            2 1.008
pair_style      deepmd graph.pb
pair_coeff      * * O H
fix             1 all nvt temp 300.0 300.0 0.1
timestep        0.0005
thermo_style    custom step temp pe ke etotal press vol
thermo          100
run             1000
```

Key points:

- The model file is usually `.pb`, `.pth`, `.pt2`, `.savedmodel`, or another exported artifact supported by the built backend.
- `pair_coeff * * O H` maps LAMMPS atom type 1 to `O` and type 2 to `H`.
- If the command omits element names, the model's stored `type_map` must be suitable for the LAMMPS type ordering.
- If `pair_coeff` uses `NULL` entries, those atom types are intentionally reserved for other pair styles in a hybrid setup.
- A DeePMD potential is many-body; do not treat `pair_coeff` as conventional pairwise parameters.

## Model Deviation

Provide multiple models on the `pair_style` line when the user wants uncertainty/deviation output:

```lammps
pair_style deepmd graph_0.pb graph_1.pb graph_2.pb out_file model_devi.out out_freq 10 atomic relative 1.0
pair_coeff * * O H
```

Behavior:

- The first model supplies the forces, energy, and virial used by the simulation.
- All listed models are compared for model deviation.
- `out_file` names the deviation output file; the default is `model_devi.out`.
- `out_freq` controls output cadence; the default is `100`.
- `atomic` includes per-atom force deviations.
- `relative LEVEL` reports force deviation normalized by force norm plus `LEVEL`.
- `relative_v LEVEL` similarly reports virial deviation.

Use model deviation for active learning, deployment confidence checks, and diagnostic runs. It is not a substitute for training a new model.

## Frame, Atom, and Charge/Spin Inputs

Some models require extra runtime inputs. Include these only when the model was trained/exported for them.

| Need | LAMMPS keyword | Example | Notes |
| --- | --- | --- | --- |
| Constant frame parameter | `fparam` | `pair_style deepmd graph.pb fparam 1.2` | Values are per frame. |
| Frame parameter from compute | `fparam_from_compute` | `pair_style deepmd graph.pb fparam_from_compute TEMP` plus `compute TEMP all temp` | The compute must produce compatible global values. |
| Frame parameter from fix | `fparam_from_fix` | `pair_style deepmd graph.pb fparam_from_fix U 1` | Optional index is 1-based for vector fixes. |
| Atomic parameter from compute | `aparam_from_compute` | `pair_style deepmd graph.pb aparam_from_compute KE` plus `compute KE all ke/atom` | The compute must produce per-atom compatible values. |
| Constant atomic parameter | `aparam` | `pair_style deepmd graph.pb aparam 0.0 1.0` | Same values apply to each atom. |
| Charge/spin embedding value | `charge_spin` | `pair_style deepmd dpa3.pth charge_spin 1.0 2.0` | Needed for models trained with charge/spin embeddings unless the model stores a default. |
| Two-temperature model | `ttm` | `pair_style deepmd graph.pb ttm TTMFIX` | Uses electronic temperatures from the named fix. |

`compute deepmd/fparam/dedn` estimates the derivative of energy with respect to a frame parameter source by finite differences:

```lammps
variable lambda equal 0.5
compute dEdL all deepmd/fparam/dedn v_lambda 1.0e-4
```

This compute performs two additional model-energy evaluations. It is intended for `pair_style deepmd` with one model and one scalar frame-parameter dimension.

## `pair_style deepspin`

Use `pair_style deepspin` for DeepSPIN models:

```lammps
units           metal
atom_style      spin
atom_modify     map array
read_data       init.data
pair_style      deepspin model.pb
pair_coeff      * * Ni O
fix             1 all precession/spin zeeman 0.0 0.0 0.0 1.0
fix_modify      1 energy yes
fix             2 all nve/spin lattice yes
thermo_style    custom step time temp etotal ke pe
run             1000
```

Notes:

- Spin simulations need spin-aware LAMMPS atom styles and fixes.
- `deepspin` accepts multiple models for force and magnetic-force deviation.
- Virial and atomic virial are not supported for spin models in the same way as standard `deepmd` models.
- The same mapping and optional parameter principles apply as for `deepmd`.

## Tensor and Long-Range Additions

Use `compute deeptensor/atom` when a model predicts atomic tensorial properties:

```lammps
compute dipole all deeptensor/atom dipole.pb
dump 1 all custom 100 tensor.dump id type c_dipole[1] c_dipole[2] c_dipole[3]
```

For long-range electrostatic terms, combine DeePMD-kit with LAMMPS `kspace_style` only when the model and physical setup were designed for that split:

```lammps
pair_style      deepmd graph.pb
pair_coeff      * *
kspace_style    pppm 1.0e-5
kspace_modify   gewald 0.45
```

For D3 dispersion overlays in new-enough LAMMPS builds:

```lammps
pair_style hybrid/overlay deepmd water.pb dispersion/d3 original pbe0 30.0 20.0
pair_coeff * * deepmd O H
pair_coeff * * dispersion/d3 O H
```

## Conservative Input Pattern

A safe starter script usually contains:

1. `units metal`, `boundary p p p`, and a simple atom style compatible with the model.
2. `read_data` before `pair_style` and `pair_coeff`.
3. `mass` commands when the data file lacks a `Masses` section.
4. A clear `pair_style` line with model files and optional deviation/parameter keywords.
5. A `pair_coeff * *` line with explicit element names when the type map is known.
6. Thermodynamic output and a trajectory dump with modest cadence.
7. One ensemble fix: `nve`, `nvt`, or `npt`.
8. A bounded `run` length, especially for smoke tests.

## i-PI Driver

DeePMD-kit's i-PI integration uses a client-server model:

- i-PI is the server and integrates path-integral replica positions.
- DeePMD-kit provides one or more `dp_ipi` clients that compute energy, forces, and virials.
- Multiple clients can serve multiple replicas in parallel.

Typical process layout:

```bash
i-pi input.xml &
dp_ipi water.json
```

The DeePMD-kit client JSON contains:

```json
{
  "verbose": false,
  "use_unix": true,
  "port": 31415,
  "host": "localhost",
  "graph_file": "graph.pb",
  "coord_file": "conf.xyz",
  "atom_type": {
    "OW": 0,
    "HW1": 1,
    "HW2": 1
  }
}
```

Checklist:

- Match `port` and socket mode with the i-PI XML input.
- Use `use_unix: true` for Unix-domain sockets; otherwise use an Internet socket with compatible host/port settings.
- `graph_file` is the frozen model used by the client.
- `coord_file` supplies atom names from XYZ labels; the coordinates themselves are not the force-evaluation coordinates.
- `atom_type` maps XYZ atom names to DeePMD type indexes.
- If `dp_ipi` is missing, rebuild/install DeePMD-kit with i-PI support rather than editing the JSON.

## Pre-Execution Review

Before running LAMMPS or i-PI, verify:

- The execution command is known and locally available.
- The selected unit style is supported.
- Model files and data/XYZ files exist relative to the planned run directory.
- The element order matches the trained model type map and LAMMPS data type numbering.
- Masses are defined before velocity/thermostat use.
- Optional keywords match model capabilities.
- The run length is safe for the user's time budget.
- For MPI/GPU runs, rank-to-device mapping is reasonable.
