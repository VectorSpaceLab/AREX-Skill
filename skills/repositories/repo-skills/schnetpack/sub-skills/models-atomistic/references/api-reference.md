# Models and Atomistic API Reference

This reference summarizes the SchNetPack 2.2 atomistic model APIs needed to assemble models in Python or Hydra. Constructor names and defaults are based on verified package/source inspection.

## Top-Level Model and Task Objects

| Object | Constructor pattern | Purpose and key contract |
| --- | --- | --- |
| `schnetpack.model.NeuralNetworkPotential` | `NeuralNetworkPotential(representation, input_modules=None, output_modules=None, postprocessors=None, input_dtype_str="float32", do_postprocessing=True)` | Sequential atomistic model. Runs `input_modules`, representation, `output_modules`, postprocessors, then returns only collected `model_outputs`. |
| `schnetpack.AtomisticTask` | `AtomisticTask(model, outputs, optimizer_cls=torch.optim.Adam, optimizer_args=None, scheduler_cls=None, scheduler_args=None, scheduler_monitor=None, warmup_steps=0)` | PyTorch Lightning task tying model, loss, metrics, optimizer, and scheduler. `outputs` are `ModelOutput` instances, not atomistic output modules. |
| `schnetpack.task.ModelOutput` | `ModelOutput(name, loss_fn=None, loss_weight=1.0, metrics=None, constraints=None, target_property=None)` | Maps a prediction key to a target key, loss, weight, metrics, and optional constraints. If `target_property` is omitted, the target key is `name`. |

`NeuralNetworkPotential` discovers child-module contracts by scanning all modules:

- Child modules with `model_outputs` define keys returned from `model(batch)`.
- Child modules with `required_derivatives` define input tensors that receive `requires_grad_()` before the forward pass.
- `postprocessors` are stored as modules and are initialized from the datamodule during `AtomisticTask.setup(stage="fit")`.
- `AtomisticTask.predict_without_postprocessing()` temporarily disables postprocessing while computing supervised losses and metrics.

## Representation Modules

All built-in representations write at least `inputs["scalar_representation"]`; equivariant representations may also write vector or multipole representations.

| Representation | Constructor pattern | Required input tensors | Produced representation keys | Notes |
| --- | --- | --- | --- | --- |
| `schnetpack.representation.SchNet` | `SchNet(n_atom_basis, n_interactions, radial_basis, cutoff_fn, n_filters=None, shared_interactions=False, activation=shifted_softplus, nuclear_embedding=None, electronic_embeddings=None)` | `_atomic_numbers`, `_Rij`, `_idx_i`, `_idx_j` | `scalar_representation` | Continuous-filter convolution; default config uses 128 basis features and 6 interactions. |
| `schnetpack.representation.PaiNN` | `PaiNN(n_atom_basis, n_interactions, radial_basis, cutoff_fn=None, activation=F.silu, shared_interactions=False, shared_filters=False, epsilon=1e-8, nuclear_embedding=None, electronic_embeddings=None)` | `_atomic_numbers`, `_Rij`, `_idx_i`, `_idx_j` | `scalar_representation`, `vector_representation` | Equivariant scalar/vector representation; default config uses 128 basis features and 3 interactions. |
| `schnetpack.representation.SO3net` | `SO3net(n_atom_basis, n_interactions, lmax, radial_basis, cutoff_fn=None, shared_interactions=False, return_vector_representation=False, activation=F.silu, nuclear_embedding=None, electronic_embeddings=None)` | `_atomic_numbers`, `_Rij`, `_idx_i`, `_idx_j` | `scalar_representation`, `multipole_representation`; optionally `vector_representation` | Spherical-harmonic representation. Set `return_vector_representation=True` when downstream output needs `vector_representation`. |
| `schnetpack.representation.FieldSchNet` | `FieldSchNet(n_atom_basis, n_interactions, radial_basis, external_fields=[], response_properties=None, cutoff_fn=None, activation=shifted_softplus, n_filters=None, shared_interactions=False, max_z=100, electric_field_modifier=None)` | `_atomic_numbers`, `_Rij`, `_idx_i`, `_idx_j`, `_idx_m`, plus external fields | `scalar_representation` | Response-oriented SchNet variant. `response_properties` can infer fields such as `electric_field` or `magnetic_field`. |

## Radial Basis and Cutoff Modules

| Module | Constructor pattern | Use |
| --- | --- | --- |
| `schnetpack.nn.radial.GaussianRBF` | `GaussianRBF(n_rbf, cutoff, start=0.0, trainable=False)` | Gaussian distance expansion with centers from `start` to `cutoff`. Exposes `n_rbf`. |
| `schnetpack.nn.radial.GaussianRBFCentered` | `GaussianRBFCentered(n_rbf, cutoff, start=1.0, trainable=False)` | Gaussian basis centered at zero with varying widths. Exposes `n_rbf`. |
| `schnetpack.nn.radial.BesselRBF` | `BesselRBF(n_rbf, cutoff)` | Sine/Bessel distance expansion with Coulomb-like decay. Exposes `n_rbf`. |
| `schnetpack.nn.cutoff.CosineCutoff` | `CosineCutoff(cutoff)` | Behler-style cutoff; value goes to zero at and beyond cutoff. Exposes `.cutoff`. |
| `schnetpack.nn.cutoff.MollifierCutoff` | `MollifierCutoff(cutoff, eps=1.0e-7)` | Smooth mollifier cutoff with numerical epsilon. Exposes `.cutoff`. |
| `schnetpack.nn.cutoff.SwitchFunction` | `SwitchFunction(switch_on, switch_off)` | Switches from 1 to 0 between two distances; useful for damped/long-range terms. |

Representation modules expect `radial_basis.n_rbf` and `cutoff_fn.cutoff` to exist, so custom modules should provide compatible attributes.

## Input Modules

| Module | Purpose | Required inputs | Outputs |
| --- | --- | --- | --- |
| `schnetpack.atomistic.PairwiseDistances` | Converts neighbor-list indices and offsets into pair vectors. | `_positions`, `_offsets`, `_idx_i`, `_idx_j` | `_Rij` |
| `schnetpack.atomistic.FilterShortRange` | Splits full neighbor information into short-range and long-range copies. | `_idx_i`, `_idx_j`, `_Rij` | `_Rij_lr`, `_idx_i_lr`, `_idx_j_lr`, filtered short-range keys |
| `schnetpack.atomistic.StaticExternalFields` | Adds zero-valued external fields when absent for response calculations. | `_n_atoms`, `_positions`; optional field keys | `electric_field`, `magnetic_field`, `nuclear_magnetic_moments` as needed |
| `schnetpack.atomistic.Strain` | Adds strain dependence for stress derivatives. | `_cell`, `_positions`, `_idx_m`, `_idx_i`, `_offsets` | `strain`, strained `_cell`, `_positions`, `_offsets` |

Neighbor-list generation itself is a data transform concern. In configs, data transforms commonly include a neighbor-list transform such as `schnetpack.transform.MatScipyNeighborList` before batches reach the model; model `input_modules` then include `PairwiseDistances`.

## Output Modules

| Module | Constructor pattern | Requires | Outputs |
| --- | --- | --- | --- |
| `schnetpack.atomistic.Atomwise` | `Atomwise(n_in, n_out=1, n_hidden=None, n_layers=2, activation=F.silu, aggregation_mode="sum", output_key="y", per_atom_output_key=None)` | `scalar_representation`, `_idx_m`, `_n_atoms` for average aggregation | `output_key`; optionally `per_atom_output_key` |
| `schnetpack.atomistic.Forces` | `Forces(calc_forces=True, calc_stress=False, energy_key="energy", force_key="forces", stress_key="stress")` | Differentiable energy under `energy_key`; positions and optionally strain | `forces` and/or `stress` |
| `schnetpack.atomistic.Response` | `Response(energy_key, response_properties, map_properties=None)` | Differentiable energy and requested derivative variables | Forces, stress, hessian, dipole, polarizability, partial charges, shielding, or coupling keys |
| `schnetpack.atomistic.DipoleMoment` | `DipoleMoment(n_in, n_hidden=None, n_layers=2, activation=F.silu, predict_magnitude=False, return_charges=False, dipole_key="dipole_moment", charges_key="partial_charges", correct_charges=True, use_vector_representation=False)` | `scalar_representation`, positions, `_idx_m`, `_n_atoms`; optional total charge; optional vector representation | `dipole_moment`; optionally `partial_charges` |
| `schnetpack.atomistic.Polarizability` | `Polarizability(n_in, n_hidden=None, n_layers=2, activation=F.silu, polarizability_key="polarizability")` | `scalar_representation`, `vector_representation`, positions, `_idx_m` | `polarizability` |
| `schnetpack.atomistic.Aggregation` | `Aggregation(keys, output_key="y")` | Existing predicted keys | Sum of listed keys under `output_key` |
| `schnetpack.atomistic.ZBLRepulsionEnergy` | `ZBLRepulsionEnergy(energy_unit, position_unit, output_key, trainable=True, cutoff_fn=None)` | Atomic numbers, pair vectors, neighbor indices, molecule indices | Repulsion energy under `output_key` |
| `schnetpack.atomistic.EnergyCoulomb` | `EnergyCoulomb(energy_unit, position_unit, coulomb_potential, output_key, charges_key="partial_charges", use_neighbors_lr=True, cutoff=None)` | Partial charges, molecule indices, pair vectors/indices | Coulomb energy under `output_key` |
| `schnetpack.atomistic.EnergyEwald` | `EnergyEwald(alpha, k_max, energy_unit, position_unit, output_key, charges_key="partial_charges", use_neighbors_lr=True, screening_fn=None)` | Periodic orthorhombic cell, charges, long-range neighbor info | Periodic Coulomb energy under `output_key` |

Important `Atomwise` rule: if `aggregation_mode=None`, set `per_atom_output_key`; otherwise no accumulated output exists and construction raises `ValueError`.

## Minimal Python Assembly Pattern

```python
import schnetpack as spk
import schnetpack.atomistic as atomistic
import schnetpack.nn as snn
from schnetpack.model import NeuralNetworkPotential

cutoff = 5.0
representation = spk.representation.PaiNN(
    n_atom_basis=64,
    n_interactions=3,
    radial_basis=snn.GaussianRBF(n_rbf=20, cutoff=cutoff),
    cutoff_fn=snn.CosineCutoff(cutoff),
)
model = NeuralNetworkPotential(
    representation=representation,
    input_modules=[atomistic.PairwiseDistances()],
    output_modules=[
        atomistic.Atomwise(n_in=64, output_key=spk.properties.energy),
        atomistic.Forces(energy_key=spk.properties.energy),
    ],
    postprocessors=[],
)
```

This object is only ready for a forward pass when the batch already contains SchNetPack graph tensors, including neighbor-list indices and offsets. Build those through the data-pipeline transforms or through interface converters rather than hand-inventing tensor names.
