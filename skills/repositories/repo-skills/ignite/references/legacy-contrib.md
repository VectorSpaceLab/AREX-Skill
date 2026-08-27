# Legacy `ignite.contrib` compatibility

Read this file when you are working with older Ignite code that still imports `ignite.contrib.*`.

## What still matters

| Legacy surface | Current status | Modern home |
| --- | --- | --- |
| `ignite.contrib.engines.tbptt.create_supervised_tbptt_trainer` | Still provided for truncated backpropagation through time helpers. | No direct replacement; keep using this legacy engine helper when TBPTT is the goal. |
| `ignite.contrib.engines.common.setup_common_training_handlers` | Backward-compatible convenience helper for common training attachments. | Mostly covered by `ignite.handlers`, `ignite.handlers.logger_utils`, `ignite.metrics.RunningAverage`, and `ignite.handlers.checkpoint`. |
| `ignite.contrib.handlers.*` | Deprecated compatibility layer. | Use `ignite.handlers.*` and `ignite.handlers.logger_utils.*`. |
| `ignite.contrib.metrics.*` | Deprecated compatibility layer. | Use `ignite.metrics.*`. |

## Migration cues

- If you see `setup_tb_logging`, `setup_mlflow_logging`, `setup_clearml_logging`, `setup_neptune_logging`, `setup_wandb_logging`, `setup_visdom_logging`, or `setup_plx_logging` in old code, the modern implementations live in `ignite.handlers.logger_utils`.
- If you see `ParamScheduler`, `FastaiLRFinder`, `BasicTimeProfiler`, `HandlersTimeProfiler`, or logger classes under `ignite.contrib.handlers`, the modern path is `ignite.handlers`.
- If you see metric names under `ignite.contrib.metrics`, move to `ignite.metrics` and keep the same metric-family semantics.

## When to read the old examples

Use this reference when old notebooks or scripts mention TBPTT, compatibility imports, or deprecation warnings, then jump back to the modern `engine`, `handlers`, or `metrics` sub-skill that owns the actual workflow.
