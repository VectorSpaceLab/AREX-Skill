# Property Keys, Tensor Contracts, and Units

SchNetPack atomistic components communicate through string keys in a dictionary. Most hard-to-debug model issues are key mismatches between data transforms, model modules, `ModelOutput`, and postprocessors.

## Structural Keys

| Constant | String key | Meaning |
| --- | --- | --- |
| `schnetpack.properties.idx` | `_idx` | Sample index. |
| `schnetpack.properties.Z` | `_atomic_numbers` | Atomic numbers. |
| `schnetpack.properties.R` / `position` | `_positions` | Atomic positions. |
| `schnetpack.properties.cell` | `_cell` | Simulation cell. |
| `schnetpack.properties.pbc` | `_pbc` | Periodic boundary conditions. |
| `schnetpack.properties.idx_m` | `_idx_m` | Molecule/system index for each atom. |
| `schnetpack.properties.idx_i` | `_idx_i` | Center atom indices for neighbor pairs. |
| `schnetpack.properties.idx_j` | `_idx_j` | Neighbor atom indices for neighbor pairs. |
| `schnetpack.properties.Rij` | `_Rij` | Pair vectors from `PairwiseDistances`. |
| `schnetpack.properties.offsets` | `_offsets` | Cell offset vectors for neighbor pairs. |
| `schnetpack.properties.n_atoms` | `_n_atoms` | Atom count per system. |
| `schnetpack.properties.strain` | `strain` | Differentiable strain tensor used for stress. |
| `schnetpack.properties.Rij_lr` | `_Rij_lr` | Long-range pair vectors after filtering. |
| `schnetpack.properties.idx_i_lr` | `_idx_i_lr` | Long-range center atom indices. |
| `schnetpack.properties.idx_j_lr` | `_idx_j_lr` | Long-range neighbor atom indices. |

Representation modules require atomic numbers and neighbor pair tensors. `PairwiseDistances` creates `_Rij` from `_positions`, `_offsets`, `_idx_i`, and `_idx_j`; it does not create the neighbor list itself.

## Chemical and Response Keys

| Constant | String key | Typical producer/consumer |
| --- | --- | --- |
| `schnetpack.properties.energy` | `energy` | `Atomwise`, `Aggregation`, `Forces`, `Response`, `ModelOutput`. |
| `schnetpack.properties.forces` | `forces` | `Forces` or `Response`; training target for force loss. |
| `schnetpack.properties.stress` | `stress` | `Forces(calc_stress=True)` or `Response`; requires strain setup. |
| `schnetpack.properties.dipole_moment` | `dipole_moment` | `DipoleMoment` or `Response`. |
| `schnetpack.properties.polarizability` | `polarizability` | `Polarizability` or `Response`. |
| `schnetpack.properties.hessian` | `hessian` | `Response`. |
| `schnetpack.properties.dipole_derivatives` | `dipole_derivatives` | `Response`. |
| `schnetpack.properties.polarizability_derivatives` | `polarizability_derivatives` | `Response`. |
| `schnetpack.properties.total_charge` | `total_charge` | Input to `DipoleMoment(correct_charges=True)` and electronic embeddings. |
| `schnetpack.properties.partial_charges` | `partial_charges` | `DipoleMoment(return_charges=True)`, `Response`, Coulomb priors. |
| `schnetpack.properties.spin_multiplicity` | `spin_multiplicity` | Electronic embeddings. |
| `schnetpack.properties.electric_field` | `electric_field` | `StaticExternalFields`, `FieldSchNet`, `Response`. |
| `schnetpack.properties.magnetic_field` | `magnetic_field` | `StaticExternalFields`, `FieldSchNet`, shielding response. |
| `schnetpack.properties.nuclear_magnetic_moments` | `nuclear_magnetic_moments` | Magnetic response calculations. |
| `schnetpack.properties.shielding` | `shielding` | `Response`, `SplitShielding`, task outputs. |
| `schnetpack.properties.nuclear_spin_coupling` | `nuclear_spin_coupling` | `Response`. |

External-field requirements are inferred for response-style properties. For example, dipole, polarizability, partial charges, and their derivatives require `electric_field`; shielding and nuclear spin coupling require magnetic-related inputs.

## Representation Keys

These keys are not in `schnetpack.properties` but are conventional outputs of representation modules:

| Key | Producer | Consumer |
| --- | --- | --- |
| `scalar_representation` | `SchNet`, `PaiNN`, `SO3net`, `FieldSchNet` | `Atomwise`, `DipoleMoment`, `Polarizability`, custom output heads. |
| `vector_representation` | `PaiNN`; `SO3net` when `return_vector_representation=True` | `DipoleMoment(use_vector_representation=True)`, `Polarizability`. |
| `multipole_representation` | `SO3net` | Custom equivariant heads. |

If an output module expects `vector_representation`, choose a compatible representation or enable vector output explicitly.

## Key Alignment Rules

Use the same key across all layers unless intentionally mapping targets:

```yaml
globals:
  energy_key: energy
  forces_key: forces

model:
  output_modules:
    - _target_: schnetpack.atomistic.Atomwise
      output_key: ${globals.energy_key}
      n_in: ${model.representation.n_atom_basis}
    - _target_: schnetpack.atomistic.Forces
      energy_key: ${globals.energy_key}
      force_key: ${globals.forces_key}

task:
  outputs:
    - _target_: schnetpack.task.ModelOutput
      name: ${globals.energy_key}
    - _target_: schnetpack.task.ModelOutput
      name: ${globals.forces_key}
```

Use `ModelOutput(target_property="dataset_key")` only when the model output key and dataset target key differ. Example: a model predicts `energy` but the batch label is `energy_U0`.

## Units and Offsets

SchNetPack separates dataset units, model outputs, and interface units:

- Dataset and datamodule configuration owns `distance_unit` and `property_units`; route details to the data-pipelines sub-skill.
- Atomistic energy priors such as `EnergyCoulomb`, `EnergyEwald`, and `ZBLRepulsionEnergy` require explicit `energy_unit` and `position_unit` constructor arguments.
- `schnetpack.units.convert_units(src_unit, tgt_unit)` returns conversion factors through ASE units.
- MD internal base units are energy `kJ / mol`, length `nm`, mass `Dalton`, and charge in elementary charge; do not assume these are training dataset units.

Offset transforms are a common source of apparent unit/key bugs:

- `RemoveOffsets` belongs in data transforms and removes means or atom references from training targets.
- `AddOffsets` belongs in model postprocessors and adds them back for prediction/inference outputs.
- `AtomisticTask.predict_without_postprocessing()` disables postprocessors for losses, so losses are computed on de-offset predictions.
- `AddOffsets.property` must match the model output key it postprocesses.

## Dtype and Precision

The default `NeuralNetworkPotential` `input_dtype_str` is `"float32"`. Typical configs use data transform `CastTo32`, then model postprocessor `CastTo64` for prediction outputs. Consequences:

- Keep neighbor-list and model tensors on the same device/dtype before forward calls.
- Do not compare direct training losses against postprocessed double outputs without accounting for `predict_without_postprocessing()`.
- Direct Python smoke tests can use CPU tensors; CUDA is not required for API inspection.

## Shape Expectations

Common output shapes depend on the module and options:

- `Atomwise(..., aggregation_mode="sum")` returns one scalar/vector per system under `output_key`.
- `Atomwise(..., aggregation_mode="avg")` divides the summed atom contributions by `_n_atoms`.
- `Atomwise(..., aggregation_mode=None, per_atom_output_key="...")` returns only per-atom predictions unless another key is configured.
- `Forces` returns per-atom vectors under `forces`; stress returns per-system tensors.
- `DipoleMoment(predict_magnitude=True)` returns magnitudes; otherwise it returns dipole vectors.
- `Polarizability` returns per-system tensor-valued polarizability.

When metrics fail on shape mismatch, check whether the output module produces per-atom, per-system scalar, per-system vector, or tensor-valued targets.
