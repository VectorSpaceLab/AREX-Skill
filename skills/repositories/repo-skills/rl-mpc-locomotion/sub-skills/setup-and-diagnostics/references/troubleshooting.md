# Troubleshooting and safe recovery

Start with the smallest read-only probe that distinguishes the failure. Keep
full command output out of the runtime skill and report only the status and
relevant version/error. The bundled probes run without a construction checkout.
For source-layout or asset checks, supply a current project copy explicitly.
Do not use `sudo`, `apt`, system-prefix installs, or commands that delete an
environment as an automatic repair.

Set these variables when a current project copy or an external dependency is
needed:

```bash
PROJECT_COPY=/path/to/current/project-copy
RSL_RL_REPO=/path/to/current/rsl_rl-repository
```

## `torch` is missing, too new, or has the wrong CUDA build

**Symptoms:** the environment probe cannot import Torch; Torch is not 1.10.0;
`torch.version.cuda` is not 11.3; or a CUDA allocation fails.

**Diagnosis** (run from the installed `setup-and-diagnostics` directory):

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
python -m pip show torch torchvision
python -m pip check
```

A common cause is installing RSL-RL without `--no-deps`; its broad Torch
requirement lets pip replace the pinned conda build. Prefer a fresh isolated
environment from the current project's environment specification, then repeat
the documented order. If the current environment is retained, restore Torch
through the same conda channel and version family, install `"$RSL_RL_REPO"`
with `--no-deps`, and rerun every probe. Do not “fix” a CUDA mismatch by
changing the project config to hide it.

## `rsl_rl` is missing or at an unexpected revision

**Symptoms:** `import rsl_rl` fails, training cannot import `OnPolicyRunner`, or
the optional commit check reports a different revision.

Confirm that the user-supplied RSL-RL repository is at
`2ad79cf0caa85b91721abfe358105f869a784121`. Reinstall it with:

```bash
python -m pip install --no-deps -e "$RSL_RL_REPO"
```

Then check Torch again. A successful editable install does not authorize a
Torch upgrade; the version and CUDA probes remain the acceptance gate.

## `mpc_osqp` cannot be imported

**Symptoms:** `ModuleNotFoundError`, an undefined C++ symbol, or a missing
binding such as `ConvexMpc`.

Run the bundled extension check from its directory:

```bash
python scripts/check_mpc_extension.py --strict
```

If the current project copy is available, include its optional integrity
checks:

```bash
python scripts/check_mpc_extension.py --repo-root "$PROJECT_COPY" --check-submodules --strict
```

If the native layout check reports missing inputs, initialize the declared
native dependencies and ensure the OSQP source tree is present in the supplied
copy. If compiler output mentions Eigen, pybind11, qpOASES, QDLDL, or an OSQP
header, repair that source layout before retrying:

```bash
python -m pip install -e "$PROJECT_COPY"
python scripts/check_mpc_extension.py --strict
```

Use `--build` on the bundled extension script only when an explicit rebuild is
wanted and a project copy is supplied. It runs the public editable install and
never removes old artifacts. If an old binary remains mixed with a changed
copy, prefer a fresh isolated environment and rebuild rather than deleting
arbitrary build directories. The extension is CPU-side; absence of `nvcc` does
not by itself invalidate a previously successful host C/C++ build, but it
limits claims about rebuilding on another machine.

## Isaac Gym import is blocked

**Symptoms:** `No module named isaacgym`, failure in `gymapi`, or training and
simulation imports stop before argument parsing.

Isaac Gym Preview 4 is a separate closed-source dependency. The project's
public environment specification does not provide it, and a passing Torch
CUDA probe is not a substitute. Obtain an authorized SDK distribution and
install it into the same isolated environment using its vendor instructions.
Then run from the installed `setup-and-diagnostics` directory:

```bash
python scripts/check_environment.py --require-isaacgym --strict --pip-check
```

Until that command passes, classify training, policy evaluation through the
Isaac environment, viewer execution, terrain simulation, and interactive
controller launch as **blocked**. Continue only with static config validation,
package diagnostics, and CPU-side MPC work. Do not add a fake `isaacgym`
module, change imports to bypass the gate, or claim that headless mode removes
the dependency.

## CUDA device is unavailable or the wrong device is selected

**Symptoms:** config requests `cuda:0`, but `torch.cuda.is_available()` is
false, the device count is zero, or a tensor allocation fails.

Check the driver and runtime from the host, then compare them with Torch's
reported CUDA build. The inspected project configuration uses CUDA devices,
GPU pipeline, PhysX, and graphics device `0` by default. Use a visible device
selection only after a strict Torch probe passes. A headless run can reduce
display failures, but it cannot make a missing CUDA runtime or Isaac Gym
importable. If a CPU-only diagnostic is intentional, change the selected
config through the RL/simulation owner and do not report GPU readiness.

## `pip check` reports broken requirements or an old-specifier warning

`pip check` failures are actionable; repair the named package and rerun it.
The old OmegaConf 2.1 metadata may produce a pip deprecation warning about a
non-standard version specifier. Treat that warning separately from a broken
requirement, but retain the Python/pip constraints in the environment
specification. Do not upgrade the whole environment to silence one warning.

## Task/config YAML fails validation

Run the bundled validator from its directory:

```bash
python scripts/validate_config.py --repo-root "$PROJECT_COPY" --all-tasks --strict
```

Without `--repo-root`, the validator performs package-safe checks and reports
how to supply a current project copy; it does not make package diagnostics
fail. With a supplied copy, the validator checks the main config, A1/Aliengo/
Go1 task YAML, configured CUDA intent, URDF presence, and referenced mesh files.
Hydra interpolations such as `${task.name}` are expected in checked-in YAML and
are not errors in a static parse. Use the RL sibling skill for override
precedence and task behavior.

If the task file exists but an asset mesh is missing, repair the asset checkout
or select a task whose complete asset tree is present. Do not point the
simulation at an unrelated robot model just to make a path check pass.

## Checkpoint cannot be loaded

Pass an explicit user-supplied absolute path to the validator:

```bash
python scripts/validate_config.py --repo-root "$PROJECT_COPY" \
  --task Aliengo --checkpoint /path/to/user/checkpoints/Aliengo/model.pt \
  --require-checkpoint --strict
```

A missing explicit file is a failure. An omitted checkpoint is informational:
the training code can use its configured latest-run fallback in some policy
paths, while policy evaluation still needs a usable saved model. Keep task
names aligned with the checkpoint's policy architecture and use the RL sibling
skill for serialization or observation-shape errors.

## Gamepad errors

`inputs==0.5` is part of the import environment, but a physical Xbox-like
gamepad is not required for a controller invocation that passes
`--disable-gamepad`. Without that flag, `inputs.devices.gamepads` must contain a
device and the reader starts a background thread. A missing device is therefore
an input-mode problem, not evidence that the MPC extension or Isaac Gym is
broken. Avoid starting a reader thread in a diagnostic probe.

## Optional solver or license errors

The compiled OSQP path and its native inputs are the default. A missing Python
`osqp`, CVXOPT, or MOSEK package is only a failure if the selected workflow
explicitly requests it. MOSEK also needs a valid external license. Do not
install system-wide OSQP Eigen or a different qpOASES release as a shortcut for
a failed local extension build; first inspect the expected source layout and
pinned commits in the user-supplied copy.

## Safe stop and recovery rule

When the cause is ambiguous, stop the expensive workflow, capture the probe
classification, and preserve the last known-good version facts. The preferred
recovery is a new isolated environment with the ordered install, followed by
package, extension, config, and strict-backend checks. Never convert a partial
handoff into a full-backend success, and never hide a required-backend block by
catching the import error in application code.
