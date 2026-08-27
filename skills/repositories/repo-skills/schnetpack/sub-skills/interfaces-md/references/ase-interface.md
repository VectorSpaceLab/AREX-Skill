# ASE Calculators, Relaxation, and Ensembles

Use this reference when a user has a trained SchNetPack model and wants Python-side predictions, ASE optimization/MD, ensemble uncertainty, or batchwise relaxation.

## Core Imports

```python
import torch
from ase.io import read
from ase.optimize import LBFGS

import schnetpack.transform as trn
from schnetpack.interfaces import AtomsConverter, SpkCalculator
from schnetpack.interfaces.ase_interface import (
    AseInterface,
    SpkEnsembleCalculator,
    AbsoluteUncertainty,
    RelativeUncertainty,
)
from schnetpack.interfaces.batchwise_optimization import (
    ASEBatchwiseLBFGS,
    BatchwiseCalculator,
    BatchwiseEnsembleCalculator,
)
```

## Single-Structure ASE Calculator

`SpkCalculator` wraps a trained SchNetPack model as an ASE calculator. The verified signature is:

```python
SpkCalculator(
    model,
    neighbor_list,
    energy_key="energy",
    force_key="forces",
    stress_key=None,
    energy_unit="kcal/mol",
    position_unit="Angstrom",
    device="cpu",
    dtype=torch.float32,
    converter=AtomsConverter,
    transforms=None,
    additional_inputs=None,
)
```

Minimal CPU example:

```python
atoms = read("structure.xyz")
calculator = SpkCalculator(
    model="best_model",
    neighbor_list=trn.ASENeighborList(cutoff=5.0),
    energy_key="energy",
    force_key="forces",
    energy_unit="kcal/mol",
    position_unit="Angstrom",
    device="cpu",
)
atoms.calc = calculator
energy_ev = atoms.get_potential_energy()
forces_ev_per_ang = atoms.get_forces()
```

Checklist:

- Match `energy_key`, `force_key`, and optional `stress_key` to the model outputs.
- Match `energy_unit` and `position_unit` to the units used during training; ASE receives eV, eV/Angstrom, and eV/Angstrom^3 after conversion.
- Match neighbor-list `cutoff` to the model/training cutoff. If the deployed model exposes `representation.cutoff`, use it as the authoritative value.
- Use `device="cpu"` on CPU-only hosts; do not rely on CUDA being available.
- Use `dtype=torch.float64` only when the model or workflow requires double precision; the default is `torch.float32`.

## AtomsConverter

`AtomsConverter` converts one ASE `Atoms` object or a list of `Atoms` objects into a SchNetPack batch. The verified signature is:

```python
AtomsConverter(
    neighbor_list,
    transforms=None,
    device="cpu",
    dtype=torch.float32,
    additional_inputs=None,
)
```

Behavior to remember:

- If `neighbor_list` is not `None`, it is prepended to `transforms`.
- `transforms` can be one transform or a list, and order matters.
- The converter appends `CastTo32()` for `torch.float32` or `CastTo64()` for `torch.float64`; other dtypes raise an error.
- It constructs `_n_atoms`, `_atomic_numbers`, `_positions`, `_cell`, `_pbc`, and sample index fields from ASE objects.
- `additional_inputs` is copied into every converted structure and is useful for transform-specific metadata.

## AseInterface Helper

`AseInterface` is a convenience wrapper for a molecule file, working directory, model file, neighbor list, and ASE optimizer. It supports:

- `calculate_single_point()` to write `single_point.xyz` with energy and forces.
- `optimize(fmax=1e-2, steps=1000)` using the configured ASE optimizer and saving an `optimization.extxyz` result.
- `init_md(name, time_step=0.5, temp_init=300, temp_bath=None, reset=False, interval=1)` for ASE Velocity Verlet or Langevin dynamics.
- `run_md(steps)` after `init_md`.
- `compute_normal_modes(write_jmol=True)` through ASE vibrations.

Example:

```python
interface = AseInterface(
    molecule_path="structure.xyz",
    working_dir="ase_run",
    model_file="best_model",
    neighbor_list=trn.ASENeighborList(cutoff=5.0),
    device="cpu",
)
interface.calculate_single_point()
interface.optimize(fmax=0.02, steps=200)
```

Use `AseInterface` for small workflows and teaching examples. For production MD or Hydra configs, prefer `spkmd` from `md-cli.md`.

## Stress with ASE

Set `stress_key="stress"` only when the model can provide stress. `SpkCalculator` attempts to activate stress computation through SchNetPack's stress utility when a stress key is supplied. If the model lacks a suitable response/output module, this can fail or produce missing-property errors.

Stress checklist:

- Training/model setup must include a stress-capable output or response path.
- Use the same `stress_key` used during training/configuration.
- For materials/PBC workflows, ensure the `Atoms` object has the intended cell and PBC flags.
- Confirm unit expectations: stress is converted from model energy/position units to ASE-style eV/Angstrom^3.

## Ensemble Calculator and Uncertainty

`SpkEnsembleCalculator` averages predictions across several models and stores an uncertainty value in `calc.results["uncertainty"]`.

```python
uncertainty = [
    AbsoluteUncertainty(energy_weight=0.5, force_weight=1.0),
    RelativeUncertainty(energy_weight=1.0, force_weight=2.0),
]
calc = SpkEnsembleCalculator(
    models=["model_a", "model_b"],
    neighbor_list=trn.ASENeighborList(cutoff=5.0),
    energy_key="energy",
    force_key="forces",
    stress_key=None,
    energy_unit="kcal/mol",
    position_unit="Angstrom",
    device="cpu",
    uncertainty_fn=uncertainty,
)
atoms.calc = calc
energy = atoms.get_potential_energy()
forces = atoms.get_forces()
unc = calc.get_uncertainty(atoms)
```

Uncertainty rules from the implementation and tests:

- If `uncertainty_fn` is omitted, `AbsoluteUncertainty()` is used.
- A single uncertainty function stores a scalar-like value in `results["uncertainty"]`.
- A list of functions stores a dictionary keyed by function class name, such as `AbsoluteUncertainty` and `RelativeUncertainty`.
- `AbsoluteUncertainty` and `RelativeUncertainty` can weight energy, force, and stress terms; total weight cannot be zero.
- The shipped ensemble tests cover mean energy/forces/stress, absolute and relative uncertainty, multiple uncertainty functions, missing-property errors, and identical-model zero uncertainty.

## Batchwise Relaxation

SchNetPack includes batchwise optimization utilities for relaxing many similar structures in parallel:

- `BatchwiseCalculator` for a single model and a list of ASE structures.
- `BatchwiseEnsembleCalculator` for a directory/list of models and per-property uncertainty outputs.
- `ASEBatchwiseLBFGS` for an LBFGS-style batch optimizer.

The tutorial notes that batchwise structure optimization is deprecated and expected to be upgraded, so present it as a legacy/advanced option, not the first recommendation.

Sketch:

```python
atoms_list = [read("a.xyz"), read("b.xyz")]
converter = AtomsConverter(
    neighbor_list=trn.ASENeighborList(cutoff=5.0),
    device="cpu",
)
calculator = BatchwiseCalculator(
    model="best_model",
    atoms_converter=converter,
    device="cpu",
    energy_key="energy",
    force_key="forces",
    energy_unit="kcal/mol",
    position_unit="Angstrom",
)
optimizer = ASEBatchwiseLBFGS(
    calculator=calculator,
    atoms=atoms_list,
    trajectory="relax_traj",
    logfile="-",
)
optimizer.run(fmax=0.05, steps=100)
opt_atoms, opt_props = optimizer.get_relaxation_results()
```

Batchwise guardrails:

- Use only for similarly sized/similar convergence structures when batching actually helps.
- Keep `steps` and `fmax` bounded for agent-generated examples.
- Provide `fixed_atoms_mask` when positions should remain fixed.
- Do not hide the deprecation note; suggest normal ASE optimizers or `spkmd` when appropriate.

## Safe Validation Ideas

Use self-contained checks before running real relaxation or MD:

- Run import/signature checks for `SpkCalculator`, `AtomsConverter`, `SpkEnsembleCalculator`, `AbsoluteUncertainty`, and `RelativeUncertainty` in the target environment.
- Use a user-provided tiny model and one small `structure.xyz` for a single-point CPU calculation before any optimization loop.
- Keep optimizer or MD steps very small during validation, and record expected files such as `single_point.xyz`, trajectory files, or uncertainty entries.

Avoid long optimization or MD trajectories during skill validation.
