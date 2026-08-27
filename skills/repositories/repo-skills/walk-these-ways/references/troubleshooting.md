# Cross-cutting troubleshooting

## Installation and package import

Run the bundled `scripts/check_installation.py --json` from an environment that
is allowed to inspect the installed package. It performs a read-only metadata
and import-spec probe. A passing `go1_gym` package probe does not install or
prove Isaac Gym.

Use a Python version and PyTorch/Isaac Gym combination supported by the caller's
separately obtained Isaac Gym Preview 4 installation. The repository README's
historical stack and the currently inspected package environment may differ.
Do not repair a caller-owned environment blindly; create an isolated environment
when dependencies conflict. After any change, check package metadata and
`pip check`, then distinguish these results:

- `go1_gym`, `go1_gym_learn`, and `go1_gym_deploy` import/spec checks: package
  surface only;
- `torch.cuda.is_available()`: CUDA-enabled PyTorch visibility only;
- `import isaacgym` followed by a tiny environment construction: required
  evidence for simulator runtime, and not available from this skill's CPU
  fallback;
- LCM/helper imports: Python dependency surface only, never robot reachability.

Do not install Isaac Gym with an invented public pip command. Preview 4 is a
separately distributed NVIDIA component.

## Optional dependency and backend failures

`ModuleNotFoundError: isaacgym`, graphics initialization failures, PhysX/GPU
pipeline errors, or incompatible CUDA/PyTorch binaries are simulator backend
blocks. Read [simulation-environment](../sub-skills/simulation-environment/SKILL.md)
and keep simulator construction/training/playback explicitly blocked until the
actual backend is installed and tested.

A CUDA Torch probe can pass while Isaac Gym fails. Conversely, an Isaac Gym
installation may require an older Torch/CUDA ABI than the rest of a system. Keep
one isolated compatibility environment and record the effective versions.

Unitree/LCM failures are separate: generated message modules, matching
architecture binaries, an onboard or approved controller computer, an isolated
network, and a physically safe robot test area are all required for end-to-end
claims. Missing hardware is not repaired with an LCM import or a local
multicast-interface listing.

## Path, configuration, and artifact validation

Prefer explicit, caller-owned paths. Do not depend on `../runs`, the current
working directory, source-relative asset roots, or implicit first-match globs.
Validate a configuration summary before changing a policy architecture:

- Go1 static defaults: `42` actor observations, `18` declared privileged
  observations, `15` frames, flattened history `630`, `12` actions;
- checked-in PPO-CSE recipe: `70` observations, `2` privileged values, `30`
  frames, flattened history `2100`, body input `2102`, `12` actions.

The two contracts are not interchangeable. Changing observation flags,
commands, history length, privileged fields, actuator/control mode, hidden
layers, or action count requires a new compatibility check and usually a new
policy export. A filename alone cannot establish compatibility.

For checkpoint pickles, inspect names and metadata without loading untrusted
`parameters.pkl`. Require the matching TorchScript body and adaptation module
for the CSE playback route, and keep model artifacts outside the generated
skill tree.

## CLI/API misuse

When a bundled helper rejects input, first run its `--help`, then supply an
explicit regular file/directory and inspect its non-zero diagnostic. The safe
helpers do not import Isaac Gym, start loggers, publish LCM, or mutate network
configuration. A helper success is limited to the contract it checks.

For source APIs, route by responsibility instead of guessing imports:
configuration and environment constructors to `simulation-environment`; actor,
rollout, checkpoint, and playback shapes to `training-and-policy`; log samples
and actuator models to `actuator-network`; command profiles, LCM schemas,
network/container prerequisites, and safety to `robot-deployment`.

## Resource, logger, and run failures

The documented training recipe uses many parallel environments and substantial
GPU memory. Do not retry a full run after an OOM. Reduce `num_envs` only as an
explicit experiment while preserving the policy's observation/history/action
contract, and perform a tiny approved backend smoke first.

A blank logger prefix or an implicit source-relative run path is a hard stop.
Use a unique caller-owned run prefix and explicit checkpoint directory. Never
place credentials, private endpoints, or local environment paths in generated
skill content or diagnostic output.

## Safety boundary

Never execute `deploy_policy.py`, a controller/autostart script, `lcm_position`,
Docker/SSH/rsync installers, `sudo` route changes, calibration, or motor/LCM
commands as a troubleshooting shortcut. Read the deployment safety references,
record the missing prerequisite or approval, and stop. A static artifact or
network diagnostic does not authorize physical operation.
