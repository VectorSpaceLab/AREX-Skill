---
name: training-policy
description: "Teaches safe Rex-Gym legacy PPO training setup and packaged policy
  playback, including CLI flags, controller-policy mapping, configs,
  checkpoints, agent counts, and bounded preflight diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Rex-Gym training and policy operation

Use this route for Rex-Gym PPO training, `rex-gym train`, pretrained `policy`
playback, checkpoint or policy-catalog questions, agent counts, log directories,
open-loop/IK selection, or TensorFlow graph setup. It covers the legacy
Python 3.7/TensorFlow 1.x-style runtime and safe preparation; it does not claim
that a policy is good, that it transfers to hardware, or that a GUI is
available.

## Scope and routing

- Read [CLI reference](references/cli-reference.md) for the exact Click
  commands, choices, defaults, and argument mapping.
- Read [training workflows](references/training-workflows.md) before preparing
  a log directory or considering a PPO launch.
- Read [policy playback](references/policy-playback.md) for policy ids,
  package-data mapping, and the finite playback loop.
- Read [troubleshooting](references/troubleshooting.md) for dependency,
  checkpoint, controller, and runtime failures.
- Run the safe [policy catalog inspector](scripts/inspect_policy_catalog.py)
  from any working directory before using packaged policies. It only reads
  distribution metadata and small config text; it never trains, opens a GUI,
  restores a graph, or copies checkpoint data.
- Route task spaces, terrain semantics, robot/low-level models, and controller
  behavior to [simulation environments](../simulation-environments/SKILL.md)
  and [locomotion modeling](../locomotion-modeling/SKILL.md). This route only
  explains how those choices enter the training/playback CLI.

Do not put a large checkpoint into a skill or a new log tree merely to inspect
it. Treat a missing package asset, missing display, incompatible dependency, or
uncertain controller/task pairing as a preflight stop rather than improvising.

## Install and bounded entry checks

The package README targets Python 3.7 and the legacy dependency set. The
published package command is:

```bash
python3.7 -m pip install rex_gym
rex-gym --help
rex-gym train --help
rex-gym policy --help
```

`rex_gym` and `rex-gym` are the underscore/hyphen spellings of the package
distribution; use the spelling accepted by the package index in the chosen
Python 3.7 environment. TensorFlow 1.15.5 and TensorFlow Probability 0.8 are
legacy dependencies. In the verified setup, TensorFlow/TFP imports require
protobuf 3.20.3. Do not upgrade this stack casually to modern TensorFlow.

First perform bounded checks only:

From the generated skill directory, run the bundled helper with a path inside this tree:

```bash
python sub-skills/training-policy/scripts/inspect_policy_catalog.py
python sub-skills/training-policy/scripts/inspect_policy_catalog.py --policy walk_ik --config-summary
```

The second form is an asset/config check, not a playback test. Confirm the
package, the requested policy id, all three TensorFlow checkpoint sidecars,
and a readable config before considering a launch. Also check that the parent
of the proposed log directory exists and is writable, and choose a positive
agent count appropriate to the selected config.

## Select the workflow

### Train with PPO

Training is an explicit, potentially long-running side effect. Ask for a
bounded run plan and authorization before launching; the ordinary command is:

```bash
rex-gym train --env walk --log-dir ./rex-logs
```

For a rendered one-agent playground session, the README form is:

```bash
rex-gym train --playground True --env walk --log-dir ./rex-logs
```

Add controller, terrain, robot mark, environment arguments, and flags only
after validating them against the sibling environment/model routes. A complete
shape is:

```bash
rex-gym train --env walk --log-dir ./rex-logs --agents-number 25 \
  --inverse-kinematics --terrain plane --mark base \
  --arg target_position 1.0 --flag on_rack True
```

`--log-dir` is required. `--playground True` sets one rendered/debug
environment; ordinary training uses the selected agent count or the config
default. The trainer appends a timestamp and `<env>_<signal>` to the log path,
saves `config.yaml`, builds the PPO graph, and writes summaries/checkpoints.
There is no safe dry-run flag in the CLI: use the inspector and `--help`, not a
training command, for bounded verification.

### Play a packaged policy

The command has no log-dir or agent-count flag:

```bash
rex-gym policy --env walk --inverse-kinematics --terrain plane --mark base
```

The player resolves the signal, loads package `config.yaml`, creates the
rendered environment, restores the mapped TensorFlow checkpoint, and steps
until the environment returns `done`. This is a GUI/runtime operation, so do
not call it as a smoke test. A display, time, and enough storage for logs or
runtime caches may be required; a terminal policy check is not a quality
claim.

## Mapping facts to preserve

- Environment choices are `gallop`, `walk`, `turn`, `standup`, `go`, and
  `poses`. With neither controller flag, defaults are respectively `ik`,
  `ik`, `ol`, `ol`, `ik`, and `ik`.
- Supported packaged policy ids are `gallop_ol`, `gallop_ik`, `walk_ik`,
  `walk_ol`, `standup_ol`, `turn_ik`, `turn_ol`, and `poses_ik`. The exact
  folder/checkpoint mapping is in [policy playback](references/policy-playback.md).
- `go` is present in the environment/default mapping, but `go_ik` is not a
  supported policy-catalog entry. Do not infer a pretrained Go policy from the
  environment choice; stop when the catalog/config/checkpoint is absent.
- If both controller flags are supplied, the parser chooses open loop first;
  it does not enforce mutual exclusion. Use exactly one or neither.

## Graph and agent safety notes

`Trainer` creates `LimitDuration`, `RangeNormalize`, `ClipAction`, and
`ConvertTo32Bit` wrappers. Training graph construction is placed under
`/cpu:0`; the source sets `use_gpu=False`, permits soft placement, and enables
GPU memory growth in the TensorFlow 1.x session. Non-Windows training can use
external-process environment wrappers; playground mode stays one agent.

The current code default is `num_agents = 25` and `update_every = 25` (an older
README snippet says 20). `--agents-number` overrides the number used to build
the batch, but the source warning checks the config's own divisibility and does
not robustly validate every override. Prefer a positive count dividing the
config update interval, and stop on batch-shape or resource errors instead of
blindly increasing it.

For failures, use [troubleshooting](references/troubleshooting.md), then
repeat the catalog check. Do not promise a full training result, policy
quality, hardware transfer, or GUI playback when the relevant runtime is not
available.
