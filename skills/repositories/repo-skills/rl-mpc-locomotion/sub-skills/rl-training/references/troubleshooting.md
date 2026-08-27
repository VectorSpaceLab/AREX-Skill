# RL training troubleshooting

Use the symptom first, then apply the smallest corrective check. Do not claim
an RL or simulation run passed while the required Isaac Gym backend is absent.
The checker commands below are bundled with this sub-skill and should be run
from its installed directory.

Set a current project copy and user-owned artifact paths only when needed:

```bash
PROJECT_COPY=/path/to/current/project-copy
CHECKPOINT=/path/to/user/checkpoints/Aliengo/model.pt
RUN_ROOT=/path/to/user/run-root
```

## Required backend and imports

### `ModuleNotFoundError: No module named 'isaacgym'`

**Cause:** Isaac Gym Preview 4 is a closed-source required dependency for task
construction, the public training package, and `WeightPolicy` import. PyTorch
CUDA support, `mpc_osqp`, and CPU package imports do not replace it.

**Recovery:** stop the RL run; obtain the authorized Isaac Gym SDK/package for
the supported Python/CUDA stack, install it in the intended environment, and
run the Isaac Gym availability/device check from
[isaac-gym-simulation](../../isaac-gym-simulation/SKILL.md). If the SDK cannot
be supplied, report the workflow as blocked rather than switching to CPU and
calling it verified.

### Torch or RSL-RL version changes unexpectedly

The documented stack is Python 3.8, PyTorch 1.10.0 with CUDA 11.3, and the
pinned RSL-RL revision. Installing RSL-RL with a broad dependency resolver can
replace the pinned Torch build. Check `python -m pip check`,
`torch.__version__`, `torch.version.cuda`, and `torch.cuda.is_available()` in
the selected environment, then repair in an isolated environment following
the setup route. Do not mutate a production environment merely to make this
check pass.

## Hydra and task resolution

### `KeyError` for a task name

Valid robot task values are `A1`, `Aliengo`, and `Go1`. `Ant` is a stale example
and is not in this task map. Use the exact case-sensitive value:

```bash
python scripts/validate_rl_config.py --task Aliengo
```

Then launch the installed project's public training command with
`task=Aliengo` (or the selected supported name), not an unrelated `task_name`
guess.

### Config not found or overrides are ignored

The public entry point composes `config` from its documented package/repository
config directory. Launch it from the working directory required by that
public command, keep each override as one space-separated `key=value` token,
and do not write `--task` or `--checkpoint` as if this were argparse. Check the
resolved configuration printed at startup and the saved run `config.yaml`
after a successful run. Do not open a source-checkout script to discover the
entry point; use the installed package/repository documentation.

### `num_envs` is not the requested value

The task config resolves an empty value to 32. Use a positive integer override,
for example `num_envs=4`, and confirm it in the printed resolved config. A
smaller count reduces memory pressure but does not remove Isaac Gym or GPU
requirements.

## Checkpoint failures

### Explicit checkpoint reports `Failed...`

The loader catches all exceptions around the explicit load and then tries the
latest model selected under the configured task run root. Possible causes
include a missing relative path, wrong launch working directory, wrong
task/policy, a corrupt artifact, or a checkpoint missing
`model_state_dict`/optimizer state. First run the safe checker without
_deserializing_ the file:

```bash
python scripts/validate_rl_config.py \
  --task Aliengo --test --checkpoint "$CHECKPOINT"
```

If the path is absent, fix the user-supplied path or choose an intentional
checkpoint. Do not accept a silent latest-run fallback in a reproducibility
report. For test mode, an empty checkpoint triggers fallback discovery; that
works only when a suitable run exists under the user-owned configured run root.
The public training entry point resolves its Hydra checkpoint path, but direct
`WeightPolicy` construction passes its constructor string to `torch.load`; use
an absolute path resolved from the actual public launch working directory in
that case.

### State-dict size or missing-key error

The current actor/critic contract is 48 observations and 12 actions with
hidden dimensions `[512, 256, 128]` and `elu`. Confirm that the task, policy
config, observation order, action mapping, and RSL-RL revision match the
checkpoint. Do not use non-strict loading or change `num_envs` to work around a
model-shape mismatch.

### Resume loads but does not behave like the prior run

A resume restores optimizer state and the saved iteration counter. Check the
resolved `seed`, task config, `max_iterations`, bridge setting, device, and
user-supplied checkpoint path in the run configuration. If any observation
normalization, reward scale, action scale, or MPC parameter mapping changed,
treat the result as a new experiment rather than a faithful continuation.

## Device and control-path failures

### GPU pipeline/device mismatch

`pipeline=gpu` enables the task's GPU pipeline only when the simulation device
is CUDA/GPU. The vector task forces CPU pipeline when that combination is
inconsistent, but this is not an Isaac Gym substitute. Keep `sim_device` and
`rl_device` explicit and validate device availability before constructing the
environment.

### Policy actions produce implausible MPC weights

Check that the policy output was clipped to `[-1,1]`, then apply the exact
mapping `[4,4,4,20,20,20,1,1,1,1,1,1] * action +
[5,5,5,50,50,50,1,1,1,1,1,1]`. Expected ranges are `[1,9]`, `[30,70]`, and
`[0,2]` by block. Ensure the thirteenth MPC weight is the appended zero and
that the first three command values were not shifted into the weight block.
For solver/FSM details route to [mpc-control](../../mpc-control/SKILL.md).

### Observation shape is 48 but behavior is wrong

Shape alone is insufficient. Simulator tasks put base position in the first
three values; `WeightPolicy` puts projected gravity (`-ground_normal_yaw`)
there. Both then include body velocities, commands, joint position/velocity
terms, and the previous 12-value action. Verify semantic ordering and scaling,
not only the tensor size. A changed ordering requires a compatible checkpoint
or retraining.

## TensorBoard and runtime cost

### No TensorBoard events appear

Training creates the writer when `learn` begins. A test-only run does not call
`learn`, so it should not create a new training stream. Use:

```bash
tensorboard --logdir "$RUN_ROOT"
```

Point at the actual user-owned timestamped run directory if the root contains
multiple experiments.

### Evaluation is unexpectedly long or expensive

The test loop runs ten maximum episode horizons; defaults are 20 seconds per
episode at 0.01-second simulation steps. Use the checker for configuration
validation, not `test=True` with a tiny environment as a general smoke test.
Even `num_envs=1` still requires the full Isaac Gym runtime.

## Scope boundary

Native training, viewer, and policy deployment cases remain blocked or
expensive in the partial handoff. The bundled checker is intentionally
side-effect-free and does not prove package import, Isaac Gym availability,
checkpoint compatibility, or reward quality.
