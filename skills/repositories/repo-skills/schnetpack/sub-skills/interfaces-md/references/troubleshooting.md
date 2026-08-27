# Interfaces and MD Troubleshooting

Use this reference to quickly diagnose SchNetPack ASE, `spkmd`, deployment, and LAMMPS failures.

## `spkmd` Missing Required Values

Symptoms:

- Hydra reports missing mandatory values such as `simulation_dir`, `system.molecule_file`, `calculator.model_file`, or `calculator.neighbor_list.cutoff`.
- A generated config still contains `???`.

Fix:

```bash
spkmd simulation_dir=md_run \
  system.molecule_file=structure.xyz \
  calculator.model_file=best_model \
  calculator.neighbor_list.cutoff=5.0 \
  device=cpu \
  dynamics.n_steps=10
```

If running from a config file, still pass `simulation_dir=...` because Hydra requires it and ignores the loaded config's simulation-dir value.

## CUDA Default on CPU-Only Hosts

Symptoms:

- CUDA initialization errors.
- `Torch not compiled with CUDA enabled`.
- Device mismatch after `spkmd` starts.

Cause: the default MD config uses `device: cuda`.

Fix:

- Add `device=cpu` to `spkmd` commands.
- In Python interfaces, pass `device="cpu"` to `SpkCalculator`, `AtomsConverter`, `SpkEnsembleCalculator`, `BatchwiseCalculator`, or `AseInterface`.
- Use CPU examples for agent-generated dry runs unless the user confirms CUDA.

## Hydra Thermostat and Barostat Syntax

Symptoms:

- Hydra cannot find a config group.
- `Could not override 'dynamics.thermostat'` or the thermostat remains `null`.
- A command uses `+dynamic/thermostat=...` instead of `+dynamics/thermostat=...`.

Fix:

- Use `+dynamics/thermostat=langevin` to add a thermostat into the default `null` slot.
- Use `+dynamics/barostat=nhc_iso` to add a barostat.
- Use `dynamics/integrator=rpmd` to swap the integrator group.
- Use `dynamics.thermostat.temperature_bath=500` only after the thermostat config exists.

Double-control warning:

- Some barostats also provide temperature control. SchNetPack warns and may ignore a separate thermostat to avoid double thermostatting.
- If the code cannot determine whether a barostat controls temperature, it warns and may keep both; ask the user to confirm the physical ensemble.

## RPMD Setup Errors

Symptoms:

- `MDSetupError: Thermostat not suitable for ring polymer dynamics.`
- `MDSetupError: Barostat not suitable for ring polymer dynamics.`
- RPMD command runs as classical MD because the integrator was not swapped.

Fix:

```bash
spkmd simulation_dir=md_rpmd \
  system.molecule_file=structure.xyz \
  calculator.model_file=best_model \
  calculator.neighbor_list.cutoff=5.0 \
  device=cpu \
  dynamics/integrator=rpmd \
  system.n_replicas=4 \
  +dynamics/thermostat=pile_local \
  dynamics.n_steps=100
```

Use ring-polymer-specific thermostats/barostats and set `system.n_replicas` intentionally.

## Missing Energy, Force, or Stress Outputs

Symptoms:

- Errors like `'energy' is not a property of your model`.
- ASE calculator raises missing-property errors.
- MD calculator cannot update required properties.

Fix:

- Confirm the model output keys and override `energy_key`, `force_key`, and optional `stress_key`.
- Confirm `required_properties` includes the requested outputs in MD configs.
- Route model architecture/output-module changes to `../models-atomistic/SKILL.md`; do not invent missing outputs at interface time.

## Stress Activation Fails

Symptoms:

- `CalculatorError: Failed to activate stress computation`.
- Stress shape/unit errors.
- Stress requested but results are absent.

Cause: stress requires model support. `SpkCalculator` and MD calculators try to activate stress only when `stress_key` is not `None`, but they need compatible output/response modules.

Fix:

- Remove `stress_key` if stress is not required.
- If stress is required, confirm the model was trained/configured for stress and has a stress-capable response/output module.
- For periodic systems, confirm cell and PBC are correct.
- In MD, include stress in `required_properties` and use the correct `calculator.stress_key`.

## Unit or Cutoff Mismatch

Symptoms:

- Energies/forces look scaled incorrectly.
- MD is unstable immediately.
- LAMMPS behavior differs from ASE or `spkmd`.

Fix:

- Match `energy_unit` and `position_unit` to training data/model config.
- Match `calculator.neighbor_list.cutoff` or ASE `ASENeighborList(cutoff=...)` to the trained model cutoff.
- For LAMMPS, ensure deployed-model cutoff metadata exists and the atom-type-to-atomic-number map is correct.
- Do not use dataset unit-conversion guesses here; route dataset/unit provenance questions to `../data-pipelines/SKILL.md`.

## `spkdeploy` or `deploy_for_lammps.py` Fails

Symptoms:

- TorchScript compilation errors.
- Missing `postprocessors` or `representation.cutoff` attributes.
- Errors involving type casts or `AddOffsets`.
- Runtime failure in LAMMPS after deployment.

Cause: the deployment script is designed for SchNetPack response-module force models. It removes casting postprocessors, adjusts `AddOffsets.mean`, scripts the model, and stores cutoff metadata.

Fix:

- Use `python scripts/deploy_for_lammps.py MODEL DEPLOYED --device cpu` first.
- Confirm the model is a SchNetPack atomistic model with `representation.cutoff`.
- Confirm the model predicts forces in the response-module style expected by the LAMMPS pair style.
- If postprocessors are incompatible with TorchScript, route back to model/export design rather than patching the deployed artifact blindly.

## LAMMPS Patch or Build Requests

Symptoms:

- User asks to run `patch_lammps.sh` or build LAMMPS.
- Build errors mention Torch, CUDA, MKL, CMake, or compiler ABI.

Policy and fix:

- Treat upstream LAMMPS patch helpers as reference-only by default because they mutate external LAMMPS source files.
- Ask for explicit approval before patching/building/installing dependencies.
- Verify toolchain compatibility before changing files: LAMMPS source version, PyTorch CMake prefix, compiler, CUDA/PyTorch-CUDA match, and MKL include path.
- Prefer a clean external checkout or disposable build directory.

## Safe Checks vs Expensive Runs

Safe checks:

```bash
spkmd --help
spkdeploy --help
python scripts/deploy_for_lammps.py --help
```

Potentially safe only with user-provided tiny inputs and verifier approval:

- One-step `spkmd` CPU smoke test with a small local model and molecule file.
- Tiny ASE single-point with a local model and structure.

Avoid by default:

- Long MD or RPMD trajectories.
- GPU jobs.
- Dataset downloads.
- LAMMPS patch/build/test runs.
