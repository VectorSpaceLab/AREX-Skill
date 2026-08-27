# Troubleshooting

Use the first failing boundary to classify the problem. Do not hide a missing
optional framework by falling back to random actions or by changing the policy
loader.

## Dependency and import failures

### `ModuleNotFoundError: stable_baselines3`

**Cause:** SB3 is not part of the base MyoSuite runtime, and the training
requirements evidence is not a complete SB3 install specification.

**Recovery:** Run `check_training_deps.py --framework sb3 --json`; ask the user
to install a compatible, pinned SB3/PyTorch set in the intended environment.
Do not install it, train, or change the base environment from this skill. If
only environment inspection is needed, use the base CPU path and omit policy
loading.

### Hydra or Submitit import failure

**Cause:** A historical launcher was selected without `hydra-core`,
`hydra-submitit-launcher`, `submitit`, or a compatible plugin/runtime.

**Recovery:** Validate the launcher as a separate optional dependency group.
Use direct, project-owned evaluation when Hydra is unnecessary. Do not treat a
Slurm launcher as a local fallback without rewriting and reviewing its output,
resource, and cancellation policy.

### TorchRL/DEP-RL/MJRL missing

**Cause:** Each framework has a separate API and dependency boundary. A base
MyoSuite import does not imply any of them is installed.

**Recovery:** Select one framework, validate its package and version, and keep
its policy/config contract. Do not switch a missing framework to another loader
or infer compatibility from a file extension.

### MJX or CUDA reported missing

**Cause:** MJX/JAX/CUDA is optional and is not proved by CPU MuJoCo or by a
PyTorch CUDA probe.

**Recovery:** Route to the MJX-specific dependency plan. For ordinary SB3 or
MJRL evaluation, use CPU if the learner and environment support it and record
that MJX was not tested. Never claim CUDA support from a CPU reset/step.

## Policy artifact failures

### Policy file is missing

**Symptom:** `FileNotFoundError`, a failed preflight, or a tutorial-style
"skipping policy loading" message.

**Recovery:** Stop policy evaluation. Ask for a trusted local artifact and its
framework, algorithm, environment id, observation/action spaces, normalization
file, and version context. A baseline directory or checkpoint download is not
implicitly available. It is valid to continue an environment-only smoke with a
seeded random policy, but label it as exploration rather than policy evaluation.

### SB3 `.zip` fails in `examine_env`

**Cause:** The examine utility's file fallback uses `pickle.load`; an SB3 zip
requires `PPO.load` or `SAC.load`.

**Recovery:** Load with the matching SB3 class and call `predict`. Do not rename
the zip or unpickle it. If an examine-style adapter is truly required, use an
importable, reviewed adapter that accepts a trusted model path through an
explicit constructor and returns an action under the examine contract.

### Pickle or checkpoint is rejected

**Cause:** The artifact is untrusted, empty, corrupt, from a different
framework, or missing companion configuration. Pickles and many ML checkpoints
can execute code during deserialization.

**Recovery:** Do not load it. Check file existence, size, extension, and (for a
zip) archive integrity only. Obtain provenance and a matching loader. The
bundled checker deliberately does not deserialize files.

### DEP-RL directory is incomplete

**Cause:** `deprl.load(path, env)` or its play command expects a run layout with
checkpoints and configuration, not just an arbitrary weights file.

**Recovery:** Request the complete trusted run directory and its environment
configuration. Verify `parallel`, `sequential`, and resource limits before any
human-controlled execution. Do not download a baseline automatically.

## Space and wrapper failures

### Observation-space mismatch

**Cause:** Different environment id/variant, wrapper order, normalization
state, policy class, feature selection, or Gym/Gymnasium API version.

**Recovery:** Print and compare `env.observation_space` with the loader's
expected space before stepping. For SB3, attach the environment to
`PPO.load`/`SAC.load` so its check runs. Restore the exact `VecNormalize`
statistics and wrapper order. Do not reshape or pad observations silently.

### Action-space mismatch or invalid action

**Cause:** Wrong policy/environment pair, wrong algorithm loader, scalar versus
vector action, wrong bounds, or an adapter returning the wrong item.

**Recovery:** Compare `env.action_space`, the action shape, dtype, and bounds.
For examine-style objects, `get_action(obs)[0]` must be the action; for SB3,
use `model.predict(obs)[0]`. Validate with `env.action_space.contains(action)`
or a clearly documented, bounded conversion. Do not clip silently when that
would alter the learned policy contract.

### Four-tuple/five-tuple step confusion

**Cause:** A legacy Gym wrapper and a Gymnasium wrapper expose different reset
and step signatures.

**Recovery:** Identify the actual wrapper/version. Handle
`obs, reward, terminated, truncated, info` for Gymnasium and stop rather than
silently treating `truncated` as an ordinary failure. Preserve the API contract
in the handoff.

### Environment cannot reset

**Cause:** Missing MuJoCo assets, unregistered id, incomplete optional model
setup, incompatible package versions, or a backend/display assumption.

**Recovery:** First run the base package import/registry check and the bounded
reset-only probe with the exact id. Use a non-rendering path. Do not invoke
asset fetch/clean operations automatically; those can mutate or download
optional model data. Record the precise id and asset/backend gap.

## Config and launcher failures

### Config parses but is unsafe for an agent session

**Cause:** `total_timesteps`, `total_frames`, worker counts, DEP-RL
`parallel * sequential`, checkpoint frequency, or wall time is large or
unbounded. Parsing does not imply a safe run.

**Recovery:** Reduce the plan, declare a small evaluation/smoke budget, and
run the checker again. For a real experiment, hand off the full resolved config
with quotas and cancellation controls; do not call `learn` or submit a job.

### `algorithm` or `sample_mode` assertion fails

**Cause:** Historical launchers accept a closed set: SB3 `PPO`/`SAC`; MJRL
`NPG`/`NVPG`/`VPG`/`PPO`; MJRL sampling `samples`/`trajectories`.

**Recovery:** Correct the config for the selected framework. Do not pass an
algorithm name from another framework or leave unused sample counts ambiguous.

### Hydra writes unexpected output or changes directories

**Cause:** Hydra run/sweep configuration chooses a timestamped output directory
and may change the process working directory; callbacks then write relative
checkpoints, logs, or videos there.

**Recovery:** Resolve the output path before execution, use one run rather than
multirun, declare every write, and use a temporary/project-approved directory.
Do not assume a relative `restore_checkpoint`, `logs/`, `wandb/`,
`eval_videos/`, or model path is harmless.

### Callback crashes on `infos[0]["solved"]`

**Cause:** `SaveSuccesses` assumes a vectorized environment emits a `solved`
key for the first info object at its configured cadence.

**Recovery:** Inspect one bounded rollout's info schema. Omit that callback or
write a reviewed adapter with a missing-key policy; do not fabricate success.
Similarly, ensure evaluation callbacks receive a compatible evaluation env and
that normalization statistics are synchronized.

### W&B/TensorBoard cannot initialize

**Cause:** Optional logging package, network service, credentials, or a
TensorBoard directory is unavailable.

**Recovery:** Disable external logging and use a local declared logger for a
bounded handoff. Never request credentials or create an external run from this
skill. Record logging as disabled and preserve the local metrics contract.

## Request to launch full training

Respond with a dry-run/config-validation result and a reproducible handoff, not
an active process. Include the resolved framework, environment, config,
policy/checkpoint inputs, dependency status, CPU/GPU/JAX boundary, worker and
memory estimate supplied by the user, output paths, logging, scheduler,
credentials, stop condition, and cleanup plan. A user can then execute the
reviewed command in a separately monitored context.
