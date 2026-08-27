# `spkmd` CLI and MD Configs

Use this reference for SchNetPack molecular dynamics from the command line or Hydra config files. Keep examples bounded and do not launch long simulations by default.

## Minimum Required Inputs

Every `spkmd` run needs these values:

- `simulation_dir`: output directory and Hydra run directory.
- `system.molecule_file`: ASE-readable structure file such as `.xyz`.
- `calculator.model_file`: trained SchNetPack model path.
- `calculator.neighbor_list.cutoff`: model neighbor-list cutoff.

Minimal CPU-safe command:

```bash
spkmd simulation_dir=md_run \
  system.molecule_file=structure.xyz \
  calculator.model_file=best_model \
  calculator.neighbor_list.cutoff=5.0 \
  device=cpu \
  dynamics.n_steps=10
```

The upstream default config uses `device: cuda`, `precision: 32`, `dynamics.n_steps: 1000000`, Velocity Verlet with `time_step: 0.5`, checkpoint/HDF5/tensorboard callbacks, and `calculator: spk`. On CPU-only hosts, always add `device=cpu`. For examples, override `dynamics.n_steps` to a small value.

## Config Structure

The default top-level blocks are:

- `calculator`: SchNetPack model, required properties, keys, units, script mode, and MD neighbor list.
- `system`: molecule file, initial velocities, replica count, input position/mass units, optional system restart.
- `dynamics`: integrator, step count, thermostat, barostat, progress flag, and extra hooks.
- `callbacks`: checkpoint, HDF5 logging, and tensorboard logging.
- `device`, `precision`, `seed`, `simulation_dir`, `overwrite`, `restart`, `load_config`.

Default calculator facts:

```yaml
calculator:
  _target_: schnetpack.md.calculators.SchNetPackCalculator
  required_properties: [energy, forces]
  model_file: ???
  force_key: forces
  energy_unit: kcal / mol
  position_unit: Angstrom
  energy_key: energy
  stress_key: null
  script_model: false
  neighbor_list:
    _target_: schnetpack.md.neighborlist_md.NeighborListMD
    cutoff: ???
    cutoff_shell: 2.0
```

If the model was trained with different keys or units, override them explicitly.

## Hydra Override Syntax

Use normal overrides for existing config values:

```bash
dynamics.n_steps=20000
dynamics.thermostat.temperature_bath=500
calculator.energy_key=energy
calculator.force_key=forces
```

Use `+` when adding a config where the existing slot is `null` or absent:

```bash
+dynamics/thermostat=langevin
+dynamics/barostat=nhc_iso
```

Use slash syntax to swap a config group:

```bash
dynamics/integrator=rpmd
calculator/neighbor_list=torch
calculator=spk_ensemble
```

Common trap: the user guide text has examples with `+dynamic/...`; the actual config group is `dynamics`, so use `+dynamics/thermostat=...` and `+dynamics/barostat=...`.

## Thermostats, Barostats, and Integrators

Available config group files include:

- Integrators: `dynamics/integrator=md` for `VelocityVerlet`, `dynamics/integrator=rpmd` for `RingPolymer`.
- Thermostats: `berendsen`, `gle`, `langevin`, `nhc`, `pi_gle`, `pi_nhc_global`, `pi_nhc_local`, `piglet`, `pile_global`, `pile_local`, `trpmd`.
- Barostats: `nhc_iso`, `nhc_aniso`, `pile_rpmd`.
- Neighbor lists: `calculator/neighbor_list=ase`, `matscipy`, or `torch`.

Classical Langevin example:

```bash
spkmd simulation_dir=md_langevin \
  system.molecule_file=structure.xyz \
  calculator.model_file=best_model \
  calculator.neighbor_list.cutoff=5.0 \
  device=cpu \
  dynamics.n_steps=20000 \
  +dynamics/thermostat=langevin \
  dynamics.thermostat.temperature_bath=300 \
  dynamics.thermostat.time_constant=100
```

RPMD example:

```bash
spkmd simulation_dir=md_rpmd \
  system.molecule_file=structure.xyz \
  calculator.model_file=best_model \
  calculator.neighbor_list.cutoff=5.0 \
  device=cpu \
  dynamics/integrator=rpmd \
  system.n_replicas=4 \
  +dynamics/thermostat=pile_local \
  dynamics.n_steps=50000
```

NPT-style guardrail:

- When a barostat is present, SchNetPack changes the integrator target through its NPT helper and passes the barostat into the integrator.
- If a barostat also provides temperature control, the CLI ignores a separate thermostat and warns to avoid double thermostatting.
- If the barostat's temperature-control behavior cannot be determined, the code warns and may still include the thermostat; ask the user to inspect the physical setup.

RPMD guardrail:

- `dynamics/integrator=rpmd` sets `n_beads` from `system.n_replicas`.
- Use ring-polymer-compatible thermostats such as `pile_local` or other `pi_`/RPMD-specific options.
- The CLI raises an `MDSetupError` if a thermostat or barostat explicitly declares itself unsuitable for ring polymer dynamics.

## Running from a Config File

Generate a config without running MD:

```bash
spkmd --cfg job > md_input.yaml
```

Run a saved config:

```bash
spkmd simulation_dir=md_from_config load_config=md_input.yaml device=cpu
```

Important details:

- `simulation_dir` is still required when using `load_config`; config-file `simulation_dir` is ignored/overridden because of Hydra run-directory handling.
- The CLI merges the loaded config with the base config and current task overrides, then writes the effective config under `.hydra/config.yaml` in the run directory.
- Use config files for review and reproducibility; use command-line overrides for quick bounded changes.

## Ensemble MD Calculator

Use `calculator=spk_ensemble` when MD should average multiple trained models:

```bash
spkmd calculator=spk_ensemble \
  simulation_dir=md_ensemble \
  system.molecule_file=structure.xyz \
  calculator.model_files='[model_a,model_b]' \
  calculator.neighbor_list.cutoff=5.0 \
  device=cpu \
  dynamics.n_steps=10
```

The ensemble config target is `schnetpack.md.calculators.SchNetPackEnsembleCalculator` and expects `model_files`, not `model_file`. It still uses `energy_key`, `force_key`, `stress_key`, `required_properties`, units, and neighbor-list settings.

## Stress in MD

To request stress:

```bash
spkmd simulation_dir=md_stress \
  system.molecule_file=structure.xyz \
  calculator.model_file=best_model \
  calculator.neighbor_list.cutoff=5.0 \
  calculator.stress_key=stress \
  '+calculator.required_properties=[energy,forces,stress]' \
  device=cpu \
  dynamics.n_steps=10
```

Use stress only if the model supports it. If the model was not trained/configured with stress-capable outputs or response modules, SchNetPack may fail while activating stress or while reading missing model outputs.

## Restart and Outputs

Default callbacks create:

- `checkpoint.chk` through `Checkpoint` every 10 steps.
- `simulation.hdf5` through `FileLogger` with molecule and property streams.
- `logs` through `TensorBoardLogger`.
- `.hydra/config.yaml`, `.hydra/overrides.yaml`, and Hydra metadata in `simulation_dir`.

Restart example:

```bash
spkmd simulation_dir=md_restart \
  restart=old_run/checkpoint.chk \
  system.molecule_file=structure.xyz \
  calculator.model_file=best_model \
  calculator.neighbor_list.cutoff=5.0 \
  device=cpu \
  dynamics.n_steps=100
```

The simulator restores state from the checkpoint after constructing the configured system/calculator/integrator. Keep model paths, keys, units, and system shape compatible with the checkpoint.

## Safe Validation Commands

Safe help/dry-run candidates:

```bash
spkmd --help
spkmd --cfg job simulation_dir=cfg_only system.molecule_file=structure.xyz calculator.model_file=best_model calculator.neighbor_list.cutoff=5.0 device=cpu
```

Potentially bounded native candidates for a final verifier:

- `spkmd` with local `md_ethanol.xyz` and `md_ethanol.model`, `device=cpu`, and `dynamics.n_steps=1`.
- A config generation check with `--cfg job`, not an MD run.

Do not run unbounded defaults, GPU MD, long RPMD, or production trajectories during routine skill verification.
