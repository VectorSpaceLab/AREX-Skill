# Model Components and Configuration Patterns

This reference helps future agents choose and wire SchNetPack atomistic components without confusing model modules, data transforms, and training task outputs.

## Component Ownership

A typical `NeuralNetworkPotential` is assembled as:

```text
batch tensors
  -> input_modules       # e.g. PairwiseDistances, StaticExternalFields, Strain
  -> representation      # SchNet, PaiNN, SO3net, FieldSchNet
  -> output_modules      # Atomwise, Forces, Response, DipoleMoment, priors
  -> postprocessors      # CastTo64, AddOffsets, inverse scaling
  -> returned outputs    # only collected model_outputs
```

A typical training run then wraps the model in `AtomisticTask`, where each `ModelOutput` names a model output and supplies loss/metrics. Do not confuse `model.output_modules` with `task.outputs`.

## Representation Selection

| Goal | Prefer | Rationale | Watch-outs |
| --- | --- | --- | --- |
| Scalar extensive or intensive properties such as energy | `SchNet` or `PaiNN` with `Atomwise` | Both produce `scalar_representation`; `Atomwise` can sum or average per-atom contributions. | Need neighbor-list transform plus `PairwiseDistances`. |
| Energy plus forces | `PaiNN` or `SchNet` with `Atomwise` then `Forces` | `Forces` differentiates predicted energy with respect to positions. | Energy key in `Forces.energy_key` must match `Atomwise.output_key`. |
| Dipole magnitude from scalar features | `PaiNN` or `SchNet` with `DipoleMoment(use_vector_representation=False)` | Uses latent charges and positions. | `predict_magnitude=True` changes target shape from vector to magnitude. |
| Dipole with local atomic dipoles | `PaiNN` or `SO3net(return_vector_representation=True)` with `DipoleMoment(use_vector_representation=True)` | Needs `vector_representation`. | SchNet alone does not produce vector features. |
| Polarizability | `PaiNN` or `SO3net(return_vector_representation=True)` with `Polarizability` | Requires scalar and vector representations. | Missing `vector_representation` fails at forward time. |
| Response properties from energy derivatives | `FieldSchNet` plus `StaticExternalFields` and `Response` | Handles external-field derivatives for dipole/polarizability/shielding-style outputs. | Requested response properties drive required gradients and fields. |
| Long-range charge priors | Charge-producing module plus `EnergyCoulomb` or `EnergyEwald` | Adds physical electrostatic energy terms. | Long-range keys require `FilterShortRange` or compatible neighbor processing. |

## Built-In Hydra Model Defaults

`model/nnp.yaml` defines the top-level model:

```yaml
_target_: schnetpack.model.NeuralNetworkPotential
input_modules:
  - _target_: schnetpack.atomistic.PairwiseDistances
output_modules: ???
```

Representation config groups define `model.representation`:

```yaml
# model/representation/painn.yaml
_target_: schnetpack.representation.PaiNN
n_atom_basis: 128
n_interactions: 3
shared_interactions: False
shared_filters: False
radial_basis:
  _target_: schnetpack.nn.radial.GaussianRBF
  n_rbf: 20
  cutoff: ${globals.cutoff}
cutoff_fn:
  _target_: schnetpack.nn.cutoff.CosineCutoff
  cutoff: ${globals.cutoff}
```

Other representation targets are `schnetpack.representation.SchNet`, `schnetpack.representation.SO3net`, and `schnetpack.representation.FieldSchNet`.

## Energy-Only Atomwise Pattern

Use this for scalar property training when data transforms already include centering, neighbor-list generation, and dtype casting:

```yaml
globals:
  cutoff: 5.0
  property: energy_U0
  aggregation: sum

model:
  output_modules:
    - _target_: schnetpack.atomistic.Atomwise
      output_key: ${globals.property}
      n_in: ${model.representation.n_atom_basis}
      aggregation_mode: ${globals.aggregation}
  postprocessors:
    - _target_: schnetpack.transform.CastTo64
    - _target_: schnetpack.transform.AddOffsets
      property: ${globals.property}
      add_mean: true
      add_atomrefs: true

task:
  outputs:
    - _target_: schnetpack.task.ModelOutput
      name: ${globals.property}
      loss_fn:
        _target_: torch.nn.MSELoss
      metrics:
        mae:
          _target_: torchmetrics.regression.MeanAbsoluteError
      loss_weight: 1.0
```

Keep `output_key`, `AddOffsets.property`, and `ModelOutput.name` aligned unless deliberately using `target_property` to train against a differently named target.

## Energy and Force Pattern

For force training, add `Forces` after the energy output module and add a second task output:

```yaml
globals:
  energy_key: energy
  forces_key: forces

model:
  output_modules:
    - _target_: schnetpack.atomistic.Atomwise
      output_key: ${globals.energy_key}
      n_in: ${model.representation.n_atom_basis}
      aggregation_mode: sum
    - _target_: schnetpack.atomistic.Forces
      energy_key: ${globals.energy_key}
      force_key: ${globals.forces_key}
  postprocessors:
    - _target_: schnetpack.transform.CastTo64
    - _target_: schnetpack.transform.AddOffsets
      property: ${globals.energy_key}
      add_mean: true

task:
  outputs:
    - _target_: schnetpack.task.ModelOutput
      name: ${globals.energy_key}
      loss_fn:
        _target_: torch.nn.MSELoss
      loss_weight: 0.01
    - _target_: schnetpack.task.ModelOutput
      name: ${globals.forces_key}
      loss_fn:
        _target_: torch.nn.MSELoss
      loss_weight: 0.99
```

`Forces` adds `_positions` to `required_derivatives`. If `calc_stress=True`, it also requires `strain`; add `Strain` before distance-dependent modules when stress derivatives are needed.

## Dipole Pattern

For QM9-like dipole-magnitude training:

```yaml
globals:
  property: dipole_moment

model:
  output_modules:
    - _target_: schnetpack.atomistic.DipoleMoment
      dipole_key: ${globals.property}
      n_in: ${model.representation.n_atom_basis}
      predict_magnitude: true
      use_vector_representation: false
  postprocessors:
    - _target_: schnetpack.transform.CastTo64

task:
  outputs:
    - _target_: schnetpack.task.ModelOutput
      name: ${globals.property}
      loss_fn:
        _target_: torch.nn.MSELoss
      loss_weight: 1.0
```

Set `return_charges=True` if latent charges should be returned, and set `use_vector_representation=True` only with a representation that supplies `vector_representation`.

## Response Pattern

For energy-derived response properties, use `FieldSchNet`, add `StaticExternalFields`, and request response outputs explicitly:

```yaml
defaults:
  - override /model: nnp
  - override /model/representation: field_schnet

globals:
  energy_key: energy
  response_properties:
    - forces
    - dipole_moment
    - polarizability

model:
  input_modules:
    - _target_: schnetpack.atomistic.PairwiseDistances
    - _target_: schnetpack.atomistic.StaticExternalFields
      response_properties: ${globals.response_properties}
  output_modules:
    - _target_: schnetpack.atomistic.Atomwise
      output_key: ${globals.energy_key}
      n_in: ${model.representation.n_atom_basis}
      aggregation_mode: sum
    - _target_: schnetpack.atomistic.Response
      energy_key: ${globals.energy_key}
      response_properties: ${globals.response_properties}
```

`Response` supports `forces`, `stress`, `hessian`, `dipole_moment`, `polarizability`, `dipole_derivatives`, `partial_charges`, `polarizability_derivatives`, `shielding`, and `nuclear_spin_coupling`. It derives `required_derivatives` from requested properties.

## Physical Priors and Aggregation

Physical-prior modules are output modules that add energy-like terms under their own `output_key`:

- `ZBLRepulsionEnergy` uses atomic numbers and pair distances for short-range repulsion.
- `EnergyCoulomb` uses partial charges and pair distances; it can use long-range neighbor keys by default.
- `EnergyEwald` uses periodic orthorhombic cells and partial charges for reciprocal-space electrostatics.
- `Aggregation(keys=[...], output_key="energy")` can combine learned and prior contributions into one key that downstream `Forces` or `ModelOutput` uses.

When deriving forces from a sum of terms, aggregate to the final energy key before `Forces`.

## Postprocessors and Losses

Postprocessors such as `CastTo64` and `AddOffsets` are part of the model but are disabled during `AtomisticTask` loss computation. This means:

- Training targets should correspond to the model prediction before postprocessing when using offset-removal transforms.
- Inference and prediction receive postprocessed outputs by default.
- If you instantiate and call `NeuralNetworkPotential` directly, `do_postprocessing=True` applies postprocessors unless you disable it.

## Custom Module Compatibility Checklist

A custom representation should:

- Accept and return the SchNetPack input dictionary.
- Write `scalar_representation` and, if needed, `vector_representation` or `multipole_representation`.
- Consume the same property keys as neighbor-list and data transforms produce.

A custom output module should:

- Accept and return the input dictionary.
- Set `self.model_outputs` to every key that should appear in final model output.
- Set `self.required_derivatives` if it needs gradients with respect to input tensors.
- Avoid changing target names silently; make output keys configurable.
