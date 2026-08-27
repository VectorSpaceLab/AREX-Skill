---
name: setup-and-diagnostics
description: "Set up and diagnose the rl-mpc-locomotion Python, CUDA, Isaac Gym,
  submodule, MPC extension, solver, configuration, asset, and checkpoint
  dependencies without claiming unavailable backend support."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Setup and diagnostics

Use this sub-skill when the task is to prepare the project, explain a failed
installation, or decide whether a controller, training, or simulation command
is runnable. It is deliberately diagnostic and read-only by default. It does
not replace the detailed operating routes owned by the sibling skills.

## Boundary and status vocabulary

- **Ready** means the named probe passed in the current Python environment.
- **Optional** means a package or device is only needed for a selected workflow.
- **Blocked** means an external required capability was not proven; do not
  convert a GPU or PyTorch pass into an Isaac Gym pass.
- **Failed** means a required package, source prerequisite, path, or version is
  inconsistent and needs repair.

The supported baseline is the Python 3.8-era environment described in
[installation](references/installation.md) and classified in the
[dependency matrix](references/dependency-matrix.md). The repository handoff
verified PyTorch 1.10 with CUDA 11.3, an A100 CUDA allocation, package
imports, `rsl_rl`, `mpc_osqp`, and `pip check`. Isaac Gym Preview 4 was
unavailable, so RL and simulation remain an explicit required-backend block
until the external SDK is supplied and imported.

## First response: safe probes

Run these commands **from this installed sub-skill directory**. They use only
the bundled scripts and the active Python environment; they do not require a
construction checkout:

```bash
python scripts/check_environment.py --pip-check
python scripts/check_mpc_extension.py --strict
```

When a current project copy is available, validate its configuration/assets
and native layout explicitly:

```bash
python scripts/validate_config.py --repo-root /path/to/current/project-copy
python scripts/check_mpc_extension.py --repo-root /path/to/current/project-copy --check-submodules --strict
```

The first two commands perform package diagnostics without requiring a source
checkout. The configuration validator requires either `--repo-root` or an
absolute `--config` path because it must not guess a checkout. The first
environment probe is advisory about Isaac Gym. Add `--require-isaacgym
--strict` only when the requested operation is RL or simulation. These probes
do not launch Hydra, a viewer, a gamepad reader, or a long training run.

## Installation route

Use a current public package or repository copy supplied by the user. Keep
paths to that copy explicit and do not depend on files in this skill bundle:

1. Obtain the project package/repository and initialize its declared native
   dependencies according to its public installation instructions. Confirm the
   pinned revisions in the [dependency matrix](references/dependency-matrix.md)
   when a source copy is being checked.
2. Create the isolated environment from the supplied project's environment
   specification (Python 3.8, PyTorch 1.10.0, CUDA toolkit 11.3, NumPy
   1.20-era packages, Hydra/OmegaConf, `inputs`, and the older pip/setuptools
   constraints).
3. Before installing `rsl_rl`, print Torch and CUDA versions. Install the
   user-supplied RSL-RL repository editable **without dependency resolution**:
   `python -m pip install --no-deps -e /path/to/rsl_rl-repository`. Its broad
   `torch>=1.4.0` requirement otherwise permits a resolver to replace the
   pinned Torch stack.
4. Install the current project copy through its public packaging metadata, for
   example `python -m pip install -e /path/to/current/project-copy`. Then run
   the bundled extension probe and `python -m pip check`.
5. Install Isaac Gym Preview 4 separately, using its authorized distribution
   instructions, only when simulation or RL is requested. Re-run the strict
   backend probe; CUDA availability alone is insufficient.

Do not use an unbounded editable install for RSL-RL, vendor a replacement
solver, run system package-manager commands, or use `sudo` as a recovery step.
The complete order, optional solver policy, and recovery choices are in the
linked references.

## Diagnostic routing

- Native controller import or solver-extension issue: use
  [mpc-control](../mpc-control/SKILL.md), after this sub-skill's environment and
  extension checks.
- Hydra task, policy, training, or checkpoint issue: use
  [rl-training](../rl-training/SKILL.md); this sub-skill only validates paths
  and prerequisites.
- Viewer, PhysX, terrain, asset loading, or simulation issue: use
  [isaac-gym-simulation](../isaac-gym-simulation/SKILL.md), but preserve the
  Isaac Gym block if the SDK cannot be imported.
- General entry-point selection: return to the
  [root router](../../SKILL.md).

## Decision gates

Before running a long command, record the requested mode (`MPC`, `Policy`,
training, or simulation), robot/task, device, checkpoint, and whether a
physical gamepad is available. A gamepad is optional for the controller CLI
when `--disable-gamepad` is used, but the small `inputs` package remains part
of the import environment because the launcher imports its reader module.

For `MPC`/`Min`, a passing CPU package and extension check is sufficient to
continue to the controller route. For `Policy`, validate the checkpoint and
Torch device, then route to both `mpc-control` and `rl-training`; no policy
claim is valid without its checkpoint. For training or simulation, require
`isaacgym`, CUDA device visibility, matching assets, and the requested config.
Use `headless=True` to remove viewer requirements, not the Isaac Gym
requirement.

## Safe recovery

Prefer a fresh isolated environment when a resolver changed Torch or an old
native build is mixed with a new checkout. Preserve the pinned order, rerun
`pip check`, and rebuild only through the explicit editable-install command
for the user-supplied project copy. Treat missing Isaac Gym as a stop for
RL/simulation, not as an invitation to patch imports or substitute a different
simulator. Read [troubleshooting](references/troubleshooting.md) before
changing versions.

## Bundled checks

- `scripts/check_environment.py`: package imports, distribution versions,
  Torch/CUDA device probe, optional package inventory, and optional `pip check`.
- `scripts/check_mpc_extension.py`: installed native package symbols, optional
  current-project layout, optional recorded submodule commit checks, and opt-in
  editable build.
- `scripts/validate_config.py`: supplied YAML shape, supplied task configs and
  assets when a current project copy is available, configured CUDA intent, and
  explicit checkpoint paths.

All scripts support `--help`, use stable exit behavior (`0` for advisory
reports, `2` for strict gates), and avoid deleting files or starting the
simulator. Their detailed output interpretation is in the references.
