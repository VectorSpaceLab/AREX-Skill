# Policy evaluation and pretrained playback

This reference converts `scripts/play.py` and the deployment loader into an
explicit, bounded playback contract. It does not launch Isaac Gym, render a
window, contact a logger, or operate a robot.

## Select a checkpoint explicitly

A run directory is expected to contain `parameters.pkl` and a `checkpoints/`
subdirectory. The source `play.py` discovers a directory with a relative glob
and chooses the first sorted match. That is convenient for the original
checkout but unsafe as a reusable contract. Pass one explicit run directory to
a caller-owned evaluator or to `inspect_checkpoint_layout.py`; never rely on
current working directory or `../runs`.

Before loading:

1. inspect the layout and require the three files in
   [checkpoint-format.md](checkpoint-format.md);
2. read `parameters.pkl` only as a caller-trusted, local configuration snapshot;
3. compare its `Cfg` values with the model's expected observation history,
   privileged width, command count, and action count;
4. disable evaluation-time randomization only in a simulator-specific harness,
   after reviewing the source behavior; do not mutate the saved file;
5. ensure all inputs are finite CPU tensors with the exact widths documented
   below.

`parameters.pkl` is a pickle and can execute arbitrary code when loaded. Do not
load an untrusted file. The safe bundled checker reports presence and file
metadata but never unpickles it.

## Body/adaptation loading contract

The source loader does:

```python
body = torch.jit.load(run / "checkpoints/body_latest.jit")
adaptation = torch.jit.load(run / "checkpoints/adaptation_module_latest.jit")
latent = adaptation(obs["obs_history"].to("cpu"))
action = body(torch.cat((obs["obs_history"].to("cpu"), latent), dim=-1))
```

For the checked-in CSE/RMA shape, a batch of `B` history vectors has:

```text
obs_history: (B, 2100)
latent:      (B, 2)
body input:  (B, 2102)
action:     (B, 12)
```

The returned action is the actor mean from the scripted body. The adaptation
output is placed into the caller's `info["latent"]`. Use `torch.no_grad()` or
inference mode for evaluation and keep the modules on CPU unless an approved
runtime requires another device. `body_latest.jit` and
`adaptation_module_latest.jit` are separate artifacts; loading only
`ac_weights_last.pt` does not reproduce this playback path without rebuilding
the Python actor-critic.

## `parameters.pkl` and config restoration

The source playback script prints the pickle keys, extracts `pkl_cfg["Cfg"]`,
and copies matching nested fields into the imported global `Cfg`. This can
restore the observation/command schema, but it is a mutable global update and
is coupled to source imports. A safe evaluator should instead parse a
caller-owned, trusted snapshot into an isolated configuration representation,
check compatibility, and make any simulator-specific override explicit.

The source then sets evaluation-only values: one recording environment and one
total environment, small terrain rows/columns, centered/teleporting robots,
and disables listed domain randomizers. Those changes are evaluation policy,
not evidence that the training configuration was reproduced. Do not silently
apply them to a new environment.

## Command vector and gait indices

For the 15-command training/playback recipe, `scripts/play.py` writes:

| Index | Command |
|---:|---|
| `0` | x linear velocity |
| `1` | y linear velocity |
| `2` | yaw angular velocity |
| `3` | body-height command |
| `4` | gait step frequency |
| `5` | gait phase |
| `6` | gait offset |
| `7` | gait bound |
| `8` | gait duration |
| `9` | foot-swing height |
| `10` | body pitch |
| `11` | body roll |
| `12` | stance width |
| `13` | stance length, when the configured command vector includes it |
| `14` | auxiliary reward/compliance field in configurations that use it; verify the exact environment schema before setting it |

The source's `gaits` dictionary uses three-value vectors applied to indices
`5:8`:

```text
pronking = [0,   0,   0]
trotting = [0.5, 0,   0]
bounding = [0,   0.5, 0]
pacing   = [0,   0,   0.5]
```

The example selects trotting and sets x velocity 1.5, yaw/y velocity 0,
body-height 0, frequency 3.0, duration 0.5, foot-swing height 0.08, pitch/roll
0, and stance width 0.25. It evaluates 250 steps and plots measured forward
velocity against the x-velocity target plus joint positions. The README's
higher-level description says its example commands forward motion at 3 m/s for
5 seconds; treat that as documentation context, not a guaranteed value for
this checked-in script.

The exact meaning of indices 13 and 14 is configuration-dependent. The source
reward code confirms stance length at index 13 when `num_commands >= 14`; do
not invent a semantic for index 14 without checking the active environment.
Route environment schema changes to
[simulation-environment](../../simulation-environment/SKILL.md).

## Bounded evaluation procedure

For a safe, source-independent evaluation harness:

1. accept an explicit run directory and a finite step budget (for example, a
   few steps for tensor compatibility, not the 250-step plotting demo);
2. run the read-only layout checker;
3. load the two TorchScript files only after the local artifact trust check;
4. construct synthetic finite history tensors with the recorded width, call
   adaptation then body, and assert `(B, 2)` latent and `(B, 12)` action for
   the checked-in CSE contract;
5. if a real environment is separately approved and installed, use its
   `HistoryWrapper` output and apply a bounded command sequence; record the
   effective config and stop on shape, NaN, timeout, or safety anomalies;
6. keep plotting and online logging optional and outside the validation gate.

A synthetic forward is a model/artifact check only. It does not verify Isaac
Gym, terrain stepping, velocity tracking, gait quality, hardware behavior, or
sim-to-real performance. Full playback is intentionally unverified on the
current host because Isaac Gym Preview 4 is unavailable.

## Hardware boundary

The deployment script uses the same two JIT files and history concatenation,
but the LCM agent, state estimator, command profile, calibration, controller,
and physical safety gates belong to [robot-deployment](../../robot-deployment/SKILL.md).
Do not use this sub-skill to launch `deploy_policy.py`, publish LCM, or test a
new policy on a robot.
