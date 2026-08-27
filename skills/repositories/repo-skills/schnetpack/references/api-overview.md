# SchNetPack API Overview

Use this root reference to orient a task before selecting a sub-skill. For detailed workflows, route to the nearest sub-skill.

## Package Families

| Area | Public surface | Use for |
| --- | --- | --- |
| `schnetpack.data` | `ASEAtomsData`, `AtomsDataModule`, loaders, split strategies, stats helpers | ASE DB datasets, batching, splits, transforms, unit conversion |
| `schnetpack.datasets` | `QM9`, `MD17`, `rMD17`, `MD22`, `ANI1`, `ISO17`, `QM7X`, `MaterialsProject`, `OMDB`, `TMQM` | Built-in benchmark dataset modules and default data configs |
| `schnetpack.model` | `NeuralNetworkPotential`, `AtomisticModel` | Composing representation, input modules, output modules, and postprocessors |
| `schnetpack.task` | `AtomisticTask`, `ModelOutput`, `UnsupervisedModelOutput` | Lightning training task, losses, metrics, optimizers, schedulers |
| `schnetpack.representation` | `SchNet`, `PaiNN`, `SO3net`, `FieldSchNet` | Atomistic representation networks |
| `schnetpack.atomistic` | `Atomwise`, `Forces`, response/electrostatics/output modules | Energy, force, stress, dipole, polarizability, response predictions |
| `schnetpack.nn` | radial bases, cutoffs, activations, dense blocks | Lower-level model components used by representations |
| `schnetpack.transform` | neighbor lists, casts, offsets, atomistic transforms | Pre/postprocessing, neighbor generation, dtype and unit handling |
| `schnetpack.interfaces` | `SpkCalculator`, `AtomsConverter`, `AseInterface`, ensemble calculators | ASE runtime, relaxation, uncertainty, model-to-ASE conversion |
| `schnetpack.md` | `System`, calculators, simulator, hooks, integrators, MD CLI | Molecular dynamics and path-integral/thermostat/barostat workflows |

## Verified Signatures

These signatures were verified from an installed SchNetPack `2.2.0` package during skill generation.

```python
ASEAtomsData(datapath, load_properties=None, load_structure=True, transforms=None, subset_idx=None, property_units=None, distance_unit=None)
AtomsDataModule(datapath, batch_size, num_train=None, num_val=None, num_test=None, split_file="split.npz", format=None, load_properties=None, val_batch_size=None, test_batch_size=None, transforms=None, train_transforms=None, val_transforms=None, test_transforms=None, train_sampler_cls=None, train_sampler_args=None, num_workers=8, num_val_workers=None, num_test_workers=None, property_units=None, distance_unit=None, data_workdir=None, cleanup_workdir_stage="test", splitting=None, pin_memory=False)
create_dataset(datapath, format, distance_unit, property_unit_dict, **kwargs)
load_dataset(datapath, format, **kwargs)
NeuralNetworkPotential(representation, input_modules=None, output_modules=None, postprocessors=None, input_dtype_str="float32", do_postprocessing=True)
SchNet(n_atom_basis, n_interactions, radial_basis, cutoff_fn, n_filters=None, shared_interactions=False, activation=shifted_softplus, nuclear_embedding=None, electronic_embeddings=None)
PaiNN(n_atom_basis, n_interactions, radial_basis, cutoff_fn=None, activation=F.silu, shared_interactions=False, shared_filters=False, epsilon=1e-8, nuclear_embedding=None, electronic_embeddings=None)
Atomwise(n_in, n_out=1, n_hidden=None, n_layers=2, activation=F.silu, aggregation_mode="sum", output_key="y", per_atom_output_key=None)
Forces(calc_forces=True, calc_stress=False, energy_key="energy", force_key="forces", stress_key="stress")
SpkCalculator(model, neighbor_list, energy_key="energy", force_key="forces", stress_key=None, energy_unit="kcal/mol", position_unit="Angstrom", device="cpu", dtype=torch.float32, converter=AtomsConverter, transforms=None, additional_inputs=None, **kwargs)
AtomsConverter(neighbor_list, transforms=None, device="cpu", dtype=torch.float32, additional_inputs=None)
```

## Routing by API Name

- `ASEAtomsData`, `AtomsDataModule`, `AtomsLoader`, `RandomSplit`, `GroupSplit`, `spkconvert` -> `sub-skills/data-pipelines/SKILL.md`.
- `spktrain`, `spkpredict`, `Hydra`, `experiment=qm9_atomwise`, `logger=csv`, `trainer.max_epochs` -> `sub-skills/training-configs/SKILL.md`.
- `NeuralNetworkPotential`, `SchNet`, `PaiNN`, `Atomwise`, `Forces`, `ModelOutput`, `AddOffsets`, property keys -> `sub-skills/models-atomistic/SKILL.md`.
- `SpkCalculator`, `AseInterface`, `SpkEnsembleCalculator`, `spkmd`, `spkdeploy`, LAMMPS -> `sub-skills/interfaces-md/SKILL.md`.

## Minimal Import Check

Use the bundled root script for machine-readable checks:

```bash
python scripts/schnetpack_import_check.py --json
```

For a quick manual check:

```python
import schnetpack as spk
import schnetpack.data, schnetpack.representation, schnetpack.atomistic
import schnetpack.interfaces, schnetpack.md
print(spk.__version__)
```
