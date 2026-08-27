# CLI and Configuration Overview

SchNetPack command-line tools use installed scripts and Hydra configuration. Route deep CLI tasks to `sub-skills/training-configs/SKILL.md` or `sub-skills/interfaces-md/SKILL.md`.

## Installed Commands

| Command | Main use | Owning route | Safe first check |
| --- | --- | --- | --- |
| `spktrain` | Train/evaluate a model from Hydra configs | `training-configs` | `spktrain --help` |
| `spkpredict` | Run predictions over an ASE DB using a trained model directory | `training-configs` | `spkpredict --help` |
| `spkconvert` | Update legacy ASE DB unit metadata and old atomrefs metadata | `data-pipelines` | `spkconvert --help` or bundled `convert_ase_units.py --help` |
| `spkdeploy` | Convert a trained force model to TorchScript for LAMMPS | `interfaces-md` | `spkdeploy --help` or bundled `deploy_for_lammps.py --help` |
| `spkmd` | Run SchNetPack molecular dynamics from Hydra MD configs | `interfaces-md` | `spkmd --help` |

Use the bundled checker for command availability and help exits:

```bash
python scripts/schnetpack_cli_check.py --commands spktrain spkpredict spkmd spkconvert spkdeploy
```

## Training Config Families

`spktrain` composes a base training config with config groups:

- `run`: work/data/run path and checkpoint-resume fields.
- `globals`: reusable values such as model path, cutoff, learning rate, and property keys.
- `data`: custom or built-in dataset modules.
- `model`: `NeuralNetworkPotential` and representation/output module choices.
- `task`: optimizer, scheduler, outputs, losses, and metrics.
- `trainer`: PyTorch Lightning trainer settings.
- `callbacks`: checkpointing, early stopping, LR monitoring, EMA.
- `logger`: TensorBoard, CSV, Aim, or W&B logger configs.
- `experiment`: templates such as QM9 atomwise/dipole and MD17/rMD17 force-field training.

Hydra override patterns:

```bash
spktrain experiment=qm9_atomwise
spktrain experiment=qm9_atomwise model/representation=painn data.batch_size=64
spktrain experiment=md17 data.molecule=uracil task.outputs.0.loss_weight=0.005 task.outputs.1.loss_weight=0.995
```

A slash selects/replaces a config group, while a dot edits a field inside the composed config. A leading `+` adds a key/group that is absent or currently null.

## Prediction Config Requirements

`spkpredict` requires these fields:

- `datapath`: ASE DB to read.
- `modeldir`: directory containing `best_model` and used as Hydra's run directory.
- `outputdir`: prediction output directory.
- `cutoff`: neighbor-list cutoff for prediction transforms.

Typical shape:

```bash
spkpredict datapath=data.db modeldir=trained-run outputdir=predictions cutoff=5.0 batch_size=32
```

Prediction does not repair unit metadata, infer missing properties, or validate that the trained model matches a new database. Route those checks through `data-pipelines` and `models-atomistic`.

## MD Config Families

`spkmd` composes MD configs with groups for:

- `calculator`: SchNetPack, ensemble, Lennard-Jones, or ORCA calculators.
- `calculator/neighbor_list`: ASE, matscipy, or torch neighbor lists.
- `system`: molecule file, replicas, units, and initializer.
- `dynamics/integrator`: classical MD or RPMD integrators.
- `dynamics/thermostat`: Langevin, NHC, PILE, GLE, TRPMD, and related thermostats.
- `dynamics/barostat`: isotropic/anisotropic NHC or RPMD barostats.
- `callbacks`: checkpoint, HDF5, TensorBoard logging.

Minimum command fields are `simulation_dir`, `system.molecule_file`, `calculator.model_file`, and `calculator.neighbor_list.cutoff`. Add `device=cpu` on CPU-only hosts because MD defaults may prefer CUDA.

## Safety Notes

- `--help`/config-print commands are safe; training, prediction, MD, deployment, and conversion may write files or perform compute.
- Avoid using dataset downloads or long training runs as smoke tests.
- Make `run.data_dir`, `run.path`, and `run.id` explicit when reproducibility matters.
- Do not assume a model supports forces or stress unless the model/task output wiring confirms it.
