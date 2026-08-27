# PPO training workflows

Read this for preparation and operation of the legacy PPO trainer. It is a
workflow recipe, not an instruction to run an unbounded experiment.

## Preflight record

Before asking to launch `train`, record:

1. Python 3.7 and the legacy TensorFlow 1.15.5 / TFP 0.8 compatibility set;
2. the environment id, explicit controller choice, mark, terrain, `--arg` and
   `--flag` pairs;
3. the expected `<environment>_<signal>` configuration function and whether
   that function exists;
4. a writable `--log-dir` parent with enough storage;
5. a positive `--agents-number`, or the config default, and the batch/update
   divisibility plan; and
6. whether the user wants a bounded playground observation or a real training
   run.

Use the bundled catalog check before any training side effect:

From the generated skill directory, run:

```bash
python sub-skills/training-policy/scripts/inspect_policy_catalog.py
```

The inspector checks packaged policy assets, not a new run directory. Check a
proposed output parent with ordinary filesystem permissions, but do not create
many timestamped directories merely to test the command.

## Commands and outputs

Batch training starts with:

```bash
rex-gym train --env walk --log-dir ./rex-logs
```

The README's rendered playground form is:

```bash
rex-gym train --playground True --env walk --log-dir ./rex-logs
```

A controller and common option shape is:

```bash
rex-gym train --env gallop --log-dir ./rex-logs \
  --inverse-kinematics --agents-number 25 --terrain plane --mark base
```

`--log-dir` is required by Click. `Trainer.start_training` expands the path,
creates a child named like `YYYYMMDDTHHMMSS-gallop_ik`, writes `config.yaml`,
and then starts the TensorFlow graph. It uses the selected environment's
signal when explicit; otherwise it uses `DEFAULT_SIGNAL`.

The `--playground` path sets `render=True` and `debug=True`, and `_train`
forces `num_agents = 1` for that mode. Ordinary training uses the explicit
`--agents-number` when non-null or the configuration's `num_agents` otherwise.
No CLI flag bounds steps or converts this into a dry run.

## Config facts

The training configuration factory defaults are `num_agents=25`,
`eval_episodes=25`, `update_every=25`, `use_gpu=False`, policy/value layers
`(200, 100)`, and Adam optimizers. Task functions set these approximate step
budgets. Shipped policy YAML files may preserve a historical run configuration
(for example, a packaged walk policy can report `max_length=2500` and
`steps=5000000`); inspect the selected YAML with the catalog helper rather than
assuming the factory defaults describe every checkpoint.

| Config function | Environment | `max_length` | `steps` |
|---|---|---:|---:|
| `gallop_ik` | `RexGalloping-v0` | 2000 | 1e6 |
| `gallop_ol` | `RexGalloping-v0` | 2000 | 2e6 |
| `walk_ik` | `RexWalk-v0` | 2000 | 1e6 |
| `walk_ol` | `RexWalk-v0` | 2000 | 2e6 |
| `turn_ik`, `turn_ol` | `RexTurn-v0` | 1000 | 1e6 |
| `standup_ol` | `RexStandup-v0` | 500 | 1e6 |
| `poses_ik` | `RexPoses-v0` | 1000 | 1e6 |
| `go` | `RexGo-v0` | 1000 | 5e6 |

The README contains an older example saying the default is 20; use the
configuration factory's current 25, while treating shipped checkpoint YAML as
historical run metadata. `go` is a function named `go`, not a
`go_ik`/`go_ol` pair, so the CLI's default signal construction cannot be
assumed to find a usable Go training config.

## Runtime mechanics that affect diagnosis

The trainer resets the TensorFlow v1 default graph, builds the batch through
`agents.scripts.utility.define_batch_env` and
`define_simulation_graph`, and wraps environments with duration limiting,
range normalization, action clipping, and 32-bit conversion. The PPO graph
uses `agents.ppo.algorithm.PPOAlgorithm`; checkpoint initialization is handled
by `initialize_variables`. On non-Windows systems it may create the tools
`ExternalProcess` wrappers; playground mode disables the multi-agent path. The
graph and environment variables are constructed under `tf.device('/cpu:0')`;
the session allows soft placement and GPU memory growth.

Before a real launch, confirm the selected environment and controller expose
matching observation/action spaces. `BatchEnv` requires all members to have
the same spaces. A requested count that is zero, negative, too large for the
machine, or inconsistent with the update cadence is a stop condition. The
source emits a divisibility warning based on `update_every % config.num_agents`
but does not fully validate an overridden CLI count; choose a positive count
dividing the configured update interval where practical.

## Stop conditions

Stop rather than retrying a full run when the preflight finds an absent config,
missing dependency, missing writable log parent, unsupported `go` policy key,
controller/task mismatch, or insufficient disk/time. If a user explicitly
approves execution, still set an external time/step budget and retain the
created log directory for diagnosis. This skill does not promise PPO quality,
convergence, or hardware transfer.
