# Submission reference

## What the runner produces

The submission generator runs an agent over first-stage scenes and the
reactive second-stage scenes, then writes `submission.pkl` as a dictionary with
these exact top-level keys:

```text
team_name
authors
email
institution
country / region
first_stage_predictions
second_stage_predictions
```

The spaces above are formatting only: use the exact key `"country / region"`.
The five metadata values must be non-empty, intentional strings. The required
identity fields are `team_name`, `authors`, `email`, `institution`, and
`country / region`; do not leave the template value `MUST_SET` or a Hydra
placeholder. A minimally useful email should contain `@`, but server-side
identity and competition-rule checks are external.

The prediction fields are lists containing stage dictionaries. The generator's
normal shape is:

```python
{
    "first_stage_predictions": [
        {"scene_token_a": trajectory_a, ...},
    ],
    "second_stage_predictions": [
        {"synthetic_scene_token_b": trajectory_b, ...},
    ],
}
```

Each stage dictionary maps a scene token string to a NAVSIM `Trajectory`
object. A trajectory contains local ego-frame `(x, y, heading)` poses with
shape `(num_poses, 3)` and the sampling metadata expected by that configured
split/agent. Do not convert the stage dictionaries into one flat list, swap
stage order, use global coordinates, or silently drop tokens after an agent
exception. The bundled validator checks metadata and basic container/pose
shape without requiring NumPy, a dataset, or a server.

Use only a trusted local pickle with the validator: Python pickle loading can
execute code supplied by a malicious file. The validator is a format check,
not a sandbox or a proof that every server scene is covered.

## Pre-generation gate

Before invoking a data-backed runner:

1. Confirm the NAVSIM environment, maps/logs/sensors, and split-specific
   synthetic roots are installed and readable. This route does not download
   them.
2. Instantiate the intended agent and inspect its public contract. It must
   return a valid `Trajectory` from `compute_trajectory(agent_input)` and its
   sensor config must match the data that will be loaded.
3. Require `agent.requires_scene == False`. The submission runner intentionally
   rejects a privileged agent that needs the annotated `Scene`; only
   `AgentInput` is available on the evaluation server. A human/privileged
   baseline is therefore not a valid submission agent.
4. Set all five metadata overrides explicitly and choose the split before
   starting. Ensure the output directory is writable and contains no stale
   `submission.pkl` that could be mistaken for the new output.

The public warmup route uses the public dataloader runner. The authorized
private challenge route uses the private-aware runner and the
`private_test_hard_two_stage` split. Keep those routes distinct: never point a
public runner at private assets or claim that a public run validates a private
challenge submission.

A command-shaped warmup recipe is:

```bash
python -m navsim.planning.script.run_create_submission_pickle \
  train_test_split=warmup_two_stage \
  agent=<non-privileged-agent-config> \
  team_name="<team>" authors="<authors>" email="<email>" \
  institution="<institution>" country="<country>" \
  synthetic_sensor_path=<warmup-sensor-root> \
  synthetic_scenes_path=<warmup-scene-root>
```

The challenge recipe has the same metadata and sensor overrides but calls the
private-aware runner and uses `train_test_split=private_test_hard_two_stage`.
Use the command shape in this reference and adapt placeholders to the installed
package and local workspace; never copy a checkout-specific path into a
runtime command. Do not execute either command without the corresponding data,
because they iterate scenes and may consume substantial I/O/GPU time.

## Warmup parity and two-stage behavior

Warmup is the recommended technical dry run. To compare a local warmup score
with the public server, use `warmup_two_stage` for all of the following:

- submission generation;
- metric-cache creation;
- local EPDMS evaluation;
- the same `metric_cache_path` (if an explicit path was used);
- the same agent/checkpoint and relevant Hydra overrides.

The split contains first-stage scenes and synthetic reactive follow-up scenes.
NAVSIM evaluates both stages and weights follow-up scenes according to how
close their start is to the submitted first-stage endpoint before aggregating
with the first-stage result. A different split, cache, proposal sampling,
agent state, or traffic-policy configuration can change the score even when
the pickle is structurally valid. Use the evaluation route for the exact
cache/scoring recipe; this route only owns submission preparation.

A warmup score that matches locally is evidence of pipeline parity, not a
server acceptance guarantee. The server may enforce coverage, metadata, file
size, competition, or model-hosting rules that cannot be checked offline.

## Private challenge boundary and external stop

`private_test_hard_two_stage` has no public annotated evaluation loop in this
workflow. Keep private data, credentials, and challenge-only paths supplied by
the authorized user; never place them in a skill, log, or example. After local
validation, the remaining operation is external: create or select a Hugging
Face model, upload `submission.pkl`, and submit the model reference in the
competition space. This route must stop before upload/login/submission unless
the user explicitly requests that external action and supplies authorization.
The competition documentation says submissions are rate-limited, so do not
retry blindly after a server failure.

## Local validation checklist

Run:

```bash
python scripts/validate_submission_metadata.py --help
python scripts/validate_submission_metadata.py path/to/submission.pkl
```

Treat any error as a hard stop. In addition to required metadata, check that
both stage fields are non-empty lists of dictionaries, token keys are strings,
and values expose two-dimensional three-column poses (or an equivalent
trajectory shape). Then inspect the validator's warnings and compare expected
scene coverage to the selected split. A pickle can pass these checks while
still failing because a trajectory is numerically invalid, a token is absent,
a checkpoint crashes on a sensor, or the server cannot access the hosted file.
