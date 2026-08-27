# Logging, summaries, CSV output, and schedulers

This reference covers PARL's small training-loop utilities that are commonly used next to environment wrappers and replay buffers.

## Schedulers

Public imports:

```python
from parl.utils import PiecewiseScheduler, LinearDecayScheduler
```

Runtime-checked signatures:

| Object | Signature | Use |
| --- | --- | --- |
| `PiecewiseScheduler` | `PiecewiseScheduler(scheduler_list)` | Stepwise hyperparameter schedule from sorted `(step, value)` pairs. |
| `LinearDecayScheduler` | `LinearDecayScheduler(start_value, max_steps)` | Linear decay from `start_value` to zero over `max_steps`. |

### `PiecewiseScheduler`

```python
scheduler = PiecewiseScheduler([(0, 0.1), (3, 0.2), (7, 0.3)])
value = scheduler.step()      # advances one step
value = scheduler.step(4)     # advances four steps
```

Rules:

- `scheduler_list` must be non-empty.
- Step values in the list must be strictly increasing.
- `step(step_num=1)` requires a positive integer.
- The current value changes when `cur_step >= next_boundary_step`.
- The scheduler advances at most one boundary per `step()` call. If a single very large `step_num` skips multiple boundaries, call `step()` repeatedly or verify behavior before relying on multi-boundary jumps.

Typical PARL uses include learning-rate schedules, entropy coefficients, and exploration parameters in Atari-style algorithms.

### `LinearDecayScheduler`

```python
scheduler = LinearDecayScheduler(start_value=1.0, max_steps=100000)
epsilon = scheduler.step()
```

Rules:

- `max_steps` must be positive.
- `step(step_num=1)` requires a positive integer.
- The internal step count saturates at `max_steps`.
- Returned value is `start_value * (1 - cur_step / max_steps)` and reaches `0` after `max_steps` total steps.

## CSV output: `CSVLogger`

Public import:

```python
from parl.utils import CSVLogger
```

Runtime-checked signature:

```python
CSVLogger(output_file)
```

Basic pattern:

```python
csv_logger = CSVLogger("result.csv")
csv_logger.log_dict({"loss": 1.0, "reward": 2.0})
csv_logger.log_dict({"loss": 0.8, "reward": 3.0})
csv_logger.flush()
csv_logger.close()
```

Expected CSV content:

```text
loss,reward
1.0,2.0
0.8,3.0
```

Contracts:

- The first `log_dict` call writes the header from the dict keys.
- All later `log_dict` calls must use exactly the same key set or an `AssertionError` is raised.
- The implementation uses a `threading.Lock`, which protects individual writes from concurrent threads in one process. It is not a multiprocess writer.
- The file is opened in write mode at construction time. Reusing an existing path truncates that file.
- Call `flush()` for durable intermediate output and `close()` when finished.
- Use a deliberate output directory; do not point the logger at a checkpoint file or a shared path used by another process.

## PARL logger directory helper

Public import:

```python
from parl.utils import logger
```

Common calls:

```python
logger.set_dir("train_log/experiment_a")
logger.set_level(logger.INFO)
logger.info("episode reward: %s", reward)
```

Important file-system behavior:

- `logger.set_dir(dirname)` removes any existing `dirname` tree, recreates it, and writes `log.log` under that directory. This is convenient for fresh experiments but destructive for an existing run directory.
- `logger.auto_set_dir(action=None)` chooses `train_log/<main_script_name>` and can prompt if that directory is non-empty. In non-interactive automation, pass an explicit `action` or avoid `auto_set_dir`.
- Supported `auto_set_dir` actions include `d` (delete existing), `k` (keep existing), and `n` (use a new time-suffixed directory). Any other action raises.
- `logger.get_dir()` returns the active directory or `None`.
- `logger.add_stdout_handler()` adds another stdout handler and returns it; call `logger.remove_handler(handler)` to remove it later if a script adds temporary handlers.

Safe pattern for generated or automated scripts:

```python
from pathlib import Path
from parl.utils import logger

run_dir = Path("train_log") / "small_smoke"
# Only use a disposable directory here: set_dir deletes it if it already exists.
logger.set_dir(str(run_dir))
```

If a task also involves model checkpoints, read `../../../core-framework/SKILL.md`: `logger.set_dir` does not manage `Agent.save`/`restore` semantics and should not be confused with checkpoint directories.

## Summary dispatch: `summary`, `tensorboard`, and `visualdl`

Public imports:

```python
from parl.utils import summary
# or explicitly:
from parl.utils import tensorboard
from parl.utils import visualdl
```

Common calls:

```python
summary.add_scalar("train/episode_reward", episode_reward, total_steps)
summary.add_histogram("weights", values, total_steps)
summary.flush()
summary.close()
```

Dispatch behavior:

- `parl.utils.summary` first tries to import PARL's VisualDL wrapper. If that import fails, it falls back to the TensorBoardX wrapper.
- `parl.utils.visualdl` requires `visualdl.LogWriter`.
- `parl.utils.tensorboard` requires `tensorboardX.SummaryWriter`.
- Both wrappers lazily create the writer on the first `add_scalar`/`add_histogram`/`flush`/`close` call.
- If `logger.get_dir()` is `None` on first writer use, the wrapper calls `logger.auto_set_dir(action='d')`, which can delete the default summary directory if it already exists.
- Each add call flushes after writing, favoring visible training curves over maximum throughput.

Safe pattern:

```python
from parl.utils import logger, summary

logger.set_dir("train_log/experiment_a")
summary.add_scalar("train/reward", 10.0, 1)
summary.flush()
```

Operational caveats:

- TensorBoard and VisualDL are optional visualization dependencies. Treat missing imports as an environment setup issue, not an algorithm bug.
- Summary calls write event files under the active PARL logger directory. They should not be used in read-only workspaces.
- Avoid importing both explicit backends and `summary` in the same script unless you intentionally want separate module-level writer state.
- In xparl or multiprocess examples, serialize logging in the learner or a designated process; do not let every actor write the same event directory.

## Relationship to examples

PARL's examples use these utilities in recurring roles:

- continuous-control DDPG/TD3/SAC/OAC/CQL-style loops: `ReplayMemory`, `logger`, `summary`, and often `ActionMappingWrapper`;
- Atari A2C/IMPALA/PPO-style loops: `wrap_deepmind`, `VectorEnv`, `PiecewiseScheduler`, `LinearDecayScheduler`, `logger`, and `summary`;
- multi-agent MADDPG-style loops: `MAenv`, per-agent replay buffers, `logger`, and `summary`;
- AlphaZero-style examples: `visualdl.add_scalar` for evaluation metrics.

Use `../../../algorithm-recipes/SKILL.md` when the task asks how these utilities fit into a complete algorithm recipe.
