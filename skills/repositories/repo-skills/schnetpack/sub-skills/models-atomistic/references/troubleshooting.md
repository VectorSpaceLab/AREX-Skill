# Models and Atomistic Troubleshooting

Use this guide for SchNetPack errors that arise while composing atomistic models in Python or Hydra configs.

## Missing Neighbor or Distance Keys

**Symptoms**

- `KeyError: '_Rij'`, `KeyError: '_idx_i'`, or `KeyError: '_idx_j'` inside `SchNet`, `PaiNN`, `SO3net`, or `FieldSchNet`.
- Representation forward pass fails before output modules run.

**Fix**

- Ensure the data transforms include a neighbor-list transform such as `schnetpack.transform.MatScipyNeighborList` with the same cutoff scale used by the model.
- Ensure the model `input_modules` include `schnetpack.atomistic.PairwiseDistances` before the representation.
- For long-range priors, add compatible filtering so `_Rij_lr`, `_idx_i_lr`, and `_idx_j_lr` exist before `EnergyCoulomb` or `EnergyEwald` when `use_neighbors_lr=True`.

## `Atomwise` with `aggregation_mode=None`

**Symptoms**

- Construction raises `ValueError` saying `per_atom_output_key` needs to be set.

**Fix**

- If you want per-system outputs, use `aggregation_mode="sum"` or `"avg"` and set `output_key`.
- If you want per-atom outputs, set `aggregation_mode=None` and provide `per_atom_output_key`; add a task loss only for a target with matching per-atom shape.

## Forces or Stress Not Produced

**Symptoms**

- `forces` missing from `model(batch)`.
- `RuntimeError` from autograd about tensors not requiring grad.
- Stress output fails or `strain` is missing.

**Fix**

- Add `schnetpack.atomistic.Forces` to `model.output_modules`; adding `ModelOutput(name="forces")` alone does not compute forces.
- Verify `Forces.energy_key` matches the energy output key produced earlier, commonly `energy`.
- Keep `Forces` after the energy-producing module in `output_modules`.
- For stress, set `calc_stress=True` and add `schnetpack.atomistic.Strain` before distance-dependent modules so `strain` exists and pair vectors include strain dependence.
- Do not detach or convert the energy tensor before `Forces` or `Response` differentiates it.

## Wrong Property Key Names

**Symptoms**

- `KeyError` in `ModelOutput.calculate_loss`.
- Model returns `energy` but task expects `energy_U0`, or postprocessor references a missing key.
- Metrics log under unexpected names.

**Fix**

- Align `Atomwise.output_key`, `Forces.energy_key`, `Forces.force_key`, `Response.energy_key`, `ModelOutput.name`, and postprocessor `property` fields.
- Use `ModelOutput(target_property="...")` when the dataset target key differs from the model prediction key.
- Prefer shared Hydra globals such as `globals.energy_key` and `globals.forces_key` to prevent drift.

## Missing Vector Representation

**Symptoms**

- `KeyError: 'vector_representation'` in `DipoleMoment(use_vector_representation=True)` or `Polarizability`.

**Fix**

- Use `PaiNN`, which produces `vector_representation`, or use `SO3net(return_vector_representation=True)`.
- Do not pair plain `SchNet` with output modules that require vector features unless you add a custom vector-producing module.

## Response Property Failures

**Symptoms**

- `NotImplementedError` from `Response` for a requested property.
- Missing `electric_field`, `magnetic_field`, or `nuclear_magnetic_moments` keys.
- Higher-order derivative errors for polarizability derivatives, hessians, shielding, or couplings.

**Fix**

- Request only supported `Response` properties: `forces`, `stress`, `hessian`, `dipole_moment`, `polarizability`, `dipole_derivatives`, `partial_charges`, `polarizability_derivatives`, `shielding`, and `nuclear_spin_coupling`.
- Add `schnetpack.atomistic.StaticExternalFields(response_properties=...)` to `input_modules` for response models so missing external fields are initialized.
- Use `FieldSchNet(response_properties=...)` when field-aware representation behavior is needed.
- Keep derivative-producing modules in `output_modules`; task outputs only define supervised losses.

## Postprocessor and Offset Confusion

**Symptoms**

- Training loss appears to use unshifted energies while predictions include offsets.
- `AddOffsets` cannot find the configured property.
- Direct `model(batch)` output differs from `AtomisticTask` loss-time prediction.

**Fix**

- Remember that `AtomisticTask.predict_without_postprocessing()` disables model postprocessors for supervised loss computation.
- Pair data-side `RemoveOffsets(property=...)` with model-side `AddOffsets(property=...)` using the same property key.
- Use `CastTo32` in data transforms and `CastTo64` in postprocessors when following built-in experiment patterns.
- For direct inference smoke checks, set `model.do_postprocessing=False` if you want loss-time predictions.

## Long-Range or Coulomb Prior Errors

**Symptoms**

- `KeyError: '_Rij_lr'` or long-range neighbor keys missing.
- Ewald calculation fails for cell geometry.
- Charges missing for Coulomb modules.

**Fix**

- Set `use_neighbors_lr=False` if using only standard `_Rij`, `_idx_i`, and `_idx_j` keys.
- Otherwise add short/long-range filtering before Coulomb modules.
- Ensure a previous output module produced `partial_charges` or configure `charges_key` to the existing charge key.
- Use `EnergyEwald` only with periodic systems whose cells have nonzero volume and meet its orthorhombic-cell expectation.

## Minimal Smoke Validation Fails

**Symptoms**

- A manually constructed batch fails even though class constructors work.

**Fix**

- Prefer a batch produced by SchNetPack data transforms or converters over hand-built dictionaries.
- If hand-building a small batch, include at least `_atomic_numbers`, `_positions`, `_idx_m`, `_n_atoms`, `_idx_i`, `_idx_j`, `_offsets`, and any property labels needed by `ModelOutput`.
- Run only constructor/import/small-forward checks in this skill context; leave native tests and long training to the verification workflow.

## Safe Validation Ideas

Use self-contained checks before running expensive training:

- Import and inspect signatures for the representation, radial basis, cutoff, output module, and task classes used in the user's config.
- Instantiate tiny `GaussianRBF`, `CosineCutoff`, `SchNet` or `PaiNN`, `PairwiseDistances`, `Atomwise`, `Forces`, and `NeuralNetworkPotential` objects with small dimensions.
- For forward checks, prefer a batch produced by SchNetPack data transforms or an `AtomsConverter` over hand-built tensors.
- Keep any synthetic batch to one or two structures, CPU execution, and no dataset downloads.
