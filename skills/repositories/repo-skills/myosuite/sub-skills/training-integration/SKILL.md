---
name: "training-integration"
description: "Plan, validate, and hand off optional MyoSuite policy evaluation
  or RL training integrations without starting uncontrolled experiments."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MyoSuite Training Integration

Use this sub-skill when a task involves an optional RL framework, a saved
policy, an experiment configuration, or a reproducible training handoff for a
MyoSuite environment. Keep environment use separate from experiment execution:
the base CPU package can create and step MyoSuite environments without any RL
framework, scheduler, model download, external account, JAX, or CUDA stack.

This sub-skill owns planning, dependency/config validation, bounded evaluation,
callback contracts, and safety gates. It does **not** own long-running training,
benchmark execution, scheduler submission, credential setup, or model download.

## Route The Request

| Request | Route |
| --- | --- |
| Check whether optional training packages are present | Run [`scripts/check_training_deps.py`](scripts/check_training_deps.py). |
| Evaluate a local saved policy | Follow [Policy evaluation](references/training-workflows.md#policy-evaluation). |
| Understand SB3, MJRL, DEP-RL, or TorchRL boundaries | Read [Framework boundaries](references/training-workflows.md#framework-boundaries). |
| Validate or design an experiment config | Read [Configuration](references/configuration.md). |
| Map Hydra launch concepts or callbacks | Read [Launch and callback contracts](references/training-workflows.md#launch-and-callback-contracts). |
| Diagnose a missing package, checkpoint, or space mismatch | Read [Troubleshooting](references/troubleshooting.md). |
| Start a full run, benchmark, Slurm job, or download | Stop at a reproducible handoff; require explicit execution outside this skill. |

## Establish The Contract

Before loading a policy or drafting a run, collect:

1. Exact environment id and MyoSuite/package versions.
2. Framework and algorithm (`stable_baselines3.PPO`, `SAC`, MJRL NPG, DEP-RL,
   TorchRL, or a custom policy).
3. Policy artifact type, local path, trusted origin, and companion state such as
   `VecNormalize` statistics.
4. Observation and action spaces used during training.
5. Evaluation budget: seed, episodes, maximum steps, render mode, and output
   directory.
6. For training: config snapshot, dependency lock, hardware/backend, resource
   cap, checkpoint cadence, evaluation protocol, and stop conditions.

Do not guess a framework from a suffix alone. A `.zip` commonly denotes an SB3
model, `.pickle` often denotes an MJRL-style object, and DEP-RL usually loads a
run directory, but provenance and loader API remain authoritative.

## Preflight Without Training

From this sub-skill directory, run a metadata-only check:

```bash
python scripts/check_training_deps.py --framework sb3 --json
```

Validate a local artifact without deserializing it:

```bash
python scripts/check_training_deps.py \
  --framework sb3 \
  --policy ./policy.zip \
  --json
```

Validate a project-owned YAML configuration without invoking Hydra or a
launcher:

```bash
python scripts/check_training_deps.py \
  --framework sb3 \
  --launcher hydra-local \
  --config ./experiment.yaml \
  --json
```

The script performs no installation, download, deserialization, training,
scheduler submission, credential lookup, or output creation. Optional
`--probe-env --env <id>` creates and resets one environment, reports spaces, and
closes it; it never steps or trains. Exit `0` means requested checks passed and
the config is within the script's agent-session guardrail, `1` means a missing
or invalid requirement, `2` is CLI misuse, and `3` means the config parsed but
exceeds or evades the bounded-run guardrail. None of these statuses authorizes
training.

## Evaluate A Saved Policy Safely

Use the loader that produced the artifact:

- SB3: `PPO.load(path, env=env, device="cpu")` or `SAC.load(...)`, then
  `model.predict(obs, deterministic=True)`.
- MJRL/examine-style policy: trusted pickle only; the object must implement
  `get_action(obs)`, whose first returned item is the action.
- DEP-RL: `deprl.load(path, env)` for a user run, or
  `deprl.load_baseline(env)` only when baseline acquisition is explicitly
  permitted.
- Custom: define and record an adapter with one clear action method and validate
  its output against `env.action_space` before stepping.

Do not pass an SB3 `.zip` directly to `myosuite.utils.examine_env`. Its policy
contract is a module-qualified class constructible as `(env, seed)` or a trusted
pickled object with `get_action`; SB3 uses `load` plus `predict`. Use a bounded
custom evaluation loop for SB3. See [training workflows](references/training-workflows.md).

Always check the package before the file loader, check file existence before
loading, and check spaces before rollout. This preserves distinct diagnoses for
`ModuleNotFoundError`, `FileNotFoundError`, and action/observation-space errors.
Never deserialize an untrusted pickle or checkpoint.

## Training Safety Gate

When asked to launch a full run from an agent session:

1. Do **not** call `model.learn`, a historical launcher, a shell training helper,
   Hydra multirun, Submitit, Slurm, a benchmark, or a download command.
2. Produce a resolved config and run manifest using the fields in
   [configuration](references/configuration.md#reproducible-handoff-manifest).
3. Run only dependency, file, and config checks; use the optional reset-only
   probe only if asset availability must be confirmed.
4. Mark requested side effects: working directory, files, videos, checkpoints,
   network services, credentials, worker count, RAM, GPU, and wall time.
5. Hand back a command template for human-controlled execution, not an executed
   command. Require explicit approval and an execution context with monitoring,
   cancellation, quotas, and cleanup.

A tiny learning smoke is still training and may create logs or initialize
accelerators. Treat it as an explicit verification candidate, not a default
preflight.

## Backend Boundary

- **Base CPU:** MyoSuite, MuJoCo, Gymnasium, and CPU policy evaluation. SB3 can
  run on CPU when installed; set `device="cpu"` for a portable handoff.
- **Optional learner GPU:** PyTorch frameworks may use CUDA for neural-network
  computation. This does not convert standard MyoSuite Gym environments into
  MJX environments or prove simulator acceleration.
- **Optional MJX/JAX:** MyoSuite's MJX environments require their separate JAX,
  MJX, and related dependency set. CUDA adds another JAX backend requirement.
  Never infer MJX/CUDA readiness from a base reset/step or from
  `torch.cuda.is_available()`.

For MJX/JAX planning, route to the sibling MJX acceleration sub-skill as well.
Do not use benchmark-scale PPO scripts as a training template here.

## Completion Criteria

A training-integration handoff is complete only when it states:

- loader/framework, trusted artifact, environment id, and space compatibility;
- dependency and config check results, with missing optional packages explicit;
- bounded evaluation or training budget and deterministic settings;
- model, normalization, config, and version artifacts to preserve;
- side effects, credentials, hardware, and scheduler assumptions;
- exact human-controlled launch concept and stop/recovery procedure;
- unresolved gaps, especially untested CUDA/MJX or unavailable policy files.
