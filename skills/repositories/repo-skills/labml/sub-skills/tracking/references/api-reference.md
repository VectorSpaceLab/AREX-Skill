# Tracking API Reference

## Purpose

Read this for verified function signatures, config keys, and client CLI entry
points used by the tracking workflow.

## Core experiment API

| Object | Signature | Use |
| --- | --- | --- |
| `labml.experiment.create` | `(*, uuid=None, name=None, python_file=None, comment=None, writers=None, ignore_callers=None, tags=None, distributed_rank=0, distributed_world_size=0, distributed_main_rank=0, disable_screen=False)` | Start a tracked experiment and choose writers. |
| `labml.experiment.record` | `(*, name=None, comment=None, writers=None, tags=None, exp_conf=None, lab_conf=None, app_url=None, distributed_rank=0, distributed_world_size=0, disable_screen=False)` | Convenience wrapper for `create` + config calculation + `start`. |
| `labml.experiment.configs` | `(*args)` | Calculate config objects or dictionaries. |
| `labml.experiment.start` | `(global_step=0)` | Enter the monitored experiment context. |
| `labml.experiment.evaluate` | `()` | Start an evaluation-only session. |
| `labml.experiment.load_configs` | `(run_uuid, *, is_only_hyperparam=True)` | Load previous run configs. |
| `labml.experiment.generate_uuid` | `()` | Create a run UUID. |

## Tracker API

| Object | Signature | Use |
| --- | --- | --- |
| `labml.tracker.add` | `(*args, **kwargs)` | Queue scalar or structured values for the next save. |
| `labml.tracker.save` | `(*args, **kwargs)` | Flush queued values and optionally set the global step. |
| `labml.tracker.set_global_step` | `(global_step)` | Set the current step explicitly. |
| `labml.tracker.add_global_step` | `(increment_global_step=1)` | Advance the current step. |
| `labml.tracker.set_scalar` | `(name, is_print=False)` | Declare a scalar indicator. |
| `labml.tracker.set_histogram` | `(name, is_print=False)` | Declare a histogram indicator. |
| `labml.tracker.namespace` | `(name)` | Nest indicator names under a namespace. |
| `labml.tracker.new_line` | `()` | Print a blank separator line in tracked output. |
| `labml.tracker.get_global_step` | `()` | Read the current step. |
| `labml.tracker.reset` | `()` | Clear queued indicators. |

## Logger and monitor API

| Object | Signature | Use |
| --- | --- | --- |
| `labml.logger.log` | `(*args, is_new_line=True, is_reset=True)` | Print styled messages. |
| `labml.logger.inspect` | `(*args, **kwargs)` | Pretty-print dictionaries, arrays, or tensors. |
| `labml.monit.section` | `(name=None, *, is_silent=False, is_timed=True, is_partial=False, is_new_line=True, is_children_silent=False, is_track=False, is_not_in_loop=False, total_steps=1.0)` | Time a block. |
| `labml.monit.loop` | `(iterator_, *, is_track=True, is_print_iteration_time=True)` | Monitored loop for training or iteration. |
| `labml.monit.iterate` | `(name, iterable=None, total_steps=None, *, is_silent=False, is_children_silent=False, is_timed=True, is_track=False, is_not_in_loop=False, context=None)` | Monitored iterator. |
| `labml.monit.enum` | Similar to `iterate` | Monitored enumerator. |
| `labml.monit.mix` | `(*args, is_monit=True)` | Merge monitored iterators; the overloads accept an optional leading total-iterations integer. |
| `labml.monit.record_time` | `(name)` | Record a named timing sample. |
| `labml.monit.get_recorded_times` | `(ignore_first=0, ignore_last=0)` | Read timing summaries. |

## Lab and project helpers

| Object | Signature | Use |
| --- | --- | --- |
| `labml.lab.get_path` | `()` | Read the project root used by LabML config discovery. |
| `labml.lab.get_data_path` | `()` | Read the configured data directory. |
| `labml.lab.get_experiments_path` | `()` | Read the configured experiment output directory. |
| `labml.lab.configure` | `(configurations)` | Override LabML config values programmatically. |
| `labml.lab.get_info` | `()` | Inspect the resolved project/config state. |
| `labml.manage.new_run` | `(python_file, *, configs=None, comment=None)` | Launch a run for a Python file. |
| `labml.manage.new_run_process` | `(python_file, *, configs=None, comment=None)` | Launch a run in a new process. |

## App client API

`labml.app_api.AppAPI` defaults to `http://localhost:5005/api/v1` and provides
these method groups:

- **Run endpoints:** `get_run`, `update_run_data`, `update_config`,
  `get_run_status`, `get_runs`, `get_runs_by_tag`, `archive_runs`,
  `unarchive_runs`, `delete_runs`.
- **Analysis endpoints:** `get_analysis`, `get_preferences`,
  `update_preferences`.
- **Custom metrics:** `create_custom_metric`, `get_custom_metrics`,
  `update_custom_metric`, `delete_custom_metric`.
- **Logs and data:** `get_logs`, `get_data_store`, `set_data_store`,
  `update_data_store`.
- **Tags:** `get_all_tags`.

The client raises `NetworkError` if the app responds with an error or the server
is unreachable.

## CLI commands

| Command | Notes |
| --- | --- |
| `labml capture` | Capture command output or stdin as an experiment. |
| `labml launch` | Launch a distributed training session wrapper. |
| `labml monitor` | Start hardware monitoring. |
| `labml service` | Create and start the user-level monitoring service. |
| `labml service-run` | Internal service entrypoint. |
| `labml app-server` | Client-side launcher that starts the monitoring app backend. |

## `.labml.yaml` keys

| Key | Meaning |
| --- | --- |
| `path` | Project root used for config discovery. |
| `check_repo_dirty` | Abort if the repo has uncommitted changes. |
| `data_path` | Relative path for datasets and caches. |
| `experiments_path` | Relative path for logs and checkpoints. |
| `analytics_path` | Relative path for generated analytics notebooks. |
| `app_url` | Base URL for the monitoring app. |
| `app_track_frequency` | Client-side app push interval. |
| `app_open_browser` | Open the monitoring URL automatically. |
| `indicators` | Default indicator routing rules. |

Older guides may still mention `web_api*` names; the current client code uses the `app_*` keys above.

## When to cross-check the source

If you need the precise return shape or a less common overload, confirm it in the
source modules and the smoke script rather than guessing from a sample.
