# Tracking, Logging, and Profiling

## Tracker Lifecycle

```python
from accelerate import Accelerator
from accelerate.utils import ProjectConfiguration

project_config = ProjectConfiguration(project_dir="runs/exp-001", logging_dir="runs/exp-001/logs")
accelerator = Accelerator(log_with="tensorboard", project_config=project_config)

accelerator.init_trackers(
    project_name="exp-001",
    config={"learning_rate": 3e-4, "batch_size": 32},
    init_kwargs={"tensorboard": {"flush_secs": 30}},
)

for step, batch in enumerate(train_dataloader):
    loss = train_step(batch)
    accelerator.log({"train/loss": float(loss)}, step=step)

accelerator.end_training()
```

Call order matters: construct `Accelerator(log_with=...)`, call `init_trackers()` before logging, call `accelerator.log()` from the loop, and call `end_training()` at the end so trackers can flush/finish.

## Built-In Tracker Names

Accelerate supports these tracker names when the optional package is installed:

| Name for `log_with` / `get_tracker` | Class | Needs local logging directory | Common caveat |
| --- | --- | --- | --- |
| `tensorboard` | `TensorBoardTracker` | Yes | Requires TensorBoard or tensorboardX; `Accelerator(log_with="tensorboard")` needs `project_dir` or `ProjectConfiguration.logging_dir`. |
| `wandb` | `WandBTracker` | No | Requires Weights & Biases package and login/offline configuration. |
| `trackio` | `TrackioTracker` | No | Requires Trackio package. |
| `comet_ml` | `CometMLTracker` | No | Requires Comet ML package and usually credentials. |
| `aim` | `AimTracker` | Yes | Requires Aim package and a repo/log directory. |
| `mlflow` | `MLflowTracker` | No | May need `MLFLOW_TRACKING_URI` or local file tracking setup. |
| `clearml` | `ClearMLTracker` | No | Usually requires ClearML credentials/server configuration. |
| `dvclive` | `DVCLiveTracker` | No | Writes DVCLive artifacts locally. |
| `swanlab` | `SwanLabTracker` | No | Requires SwanLab package and configuration. |

`log_with="all"` enables all available installed trackers. Prefer explicit tracker names for reproducible scripts, because the set of installed optional dependencies can differ by environment.

## Logging Values and Tracker-Specific Kwargs

`accelerator.log(values, step=step)` forwards the same dictionary to all active trackers. Keep values simple unless the tracker class documents richer methods: numeric scalars, strings, and small nested scalar dictionaries are safest.

For tracker-specific logging options, pass nested kwargs keyed by tracker name:

```python
accelerator.log(
    {"eval/accuracy": accuracy},
    step=global_step,
    log_kwargs={"wandb": {"commit": False}},
)
```

For direct tracker methods, use `get_tracker()`:

```python
tb_tracker = accelerator.get_tracker("tensorboard")
tb_tracker.log_images({"samples": images}, step=global_step)

wandb_run = accelerator.get_tracker("wandb", unwrap=True)
if accelerator.is_main_process:
    wandb_run.log_artifact(artifact)
```

`get_tracker(name)` returns Accelerate's wrapped tracker on the main process and a blank `GeneralTracker` placeholder on non-main processes when trackers only exist on the main process. If `unwrap=True`, guard direct library calls with `accelerator.is_main_process` unless the tracker library is explicitly process-aware.

## Custom Trackers

Implement `GeneralTracker` when the target service cannot be represented by a built-in tracker or when tests need local no-service logging.

```python
from accelerate.tracking import GeneralTracker, on_main_process

class JsonlTracker(GeneralTracker):
    name = "jsonl"
    requires_logging_directory = False
    main_process_only = True

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.handle = None

    @property
    def tracker(self):
        return self.handle

    @on_main_process
    def start(self):
        self.handle = open(self.path, "a", encoding="utf-8")

    @on_main_process
    def store_init_configuration(self, values):
        self.handle.write(json.dumps({"config": values}) + "\n")

    @on_main_process
    def log(self, values, step=None, **kwargs):
        self.handle.write(json.dumps({"step": step, "values": values}) + "\n")
        self.handle.flush()

    @on_main_process
    def finish(self):
        self.handle.close()
```

Pass a tracker instance with `Accelerator(log_with=JsonlTracker("metrics.jsonl"))`. Custom tracker methods should accept `**kwargs` when they may be used with `log_kwargs`.

## Multiprocess-Safe Logging

Use Accelerate's logger, not raw `print`, for rank-aware logs:

```python
from accelerate import Accelerator
from accelerate.logging import get_logger

logger = get_logger(__name__, log_level="INFO")
accelerator = Accelerator()

logger.info("only main process logs by default")
logger.info("all ranks log", main_process_only=False)
logger.info("rank ordered log", in_order=True)
```

Important details:

- Initialize `PartialState()` or `Accelerator()` before using the logging utility; otherwise the adapter raises `RuntimeError`.
- Logs are prefixed with `[RANK <index>]`.
- `main_process_only=True` is the default.
- `in_order=True` ignores `main_process_only`, loops over ranks, and calls `wait_for_everyone()` between ranks; it is easier to read but can slow or hang if not all ranks execute that log call.
- `warning_once()` emits the same warning arguments once per process.
- `ACCELERATE_LOG_LEVEL` controls the default log level when no `log_level` is passed.

Use `accelerator.print()` for simple main-process-only console messages and `get_logger()` for structured Python logging.

## Profiling with `ProfileKwargs`

```python
from accelerate import Accelerator
from accelerate.utils import ProfileKwargs

profile_kwargs = ProfileKwargs(
    activities=["cpu"],
    record_shapes=True,
    profile_memory=True,
)
accelerator = Accelerator(kwargs_handlers=[profile_kwargs])
model = accelerator.prepare(model)

with accelerator.profile() as prof:
    with torch.no_grad():
        model(inputs)

accelerator.print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=10))
```

Useful `ProfileKwargs` fields:

- `activities`: strings such as `"cpu"`, `"cuda"`, `"xpu"`, `"mtia"`, or `"hpu"` depending on backend support.
- `record_shapes`: needed for shape-grouped operator tables.
- `profile_memory`: records tensor allocation/deallocation.
- `with_stack`, `with_flops`, `with_modules`: add stack, FLOP, and module hierarchy information where PyTorch supports it.
- `schedule_option`: keys `wait`, `warmup`, `active`, `repeat`, and `skip_first` for long runs.
- `on_trace_ready`: callback that receives the profiler, often used to print tables or export traces.
- `output_trace_dir`: directory for Chrome trace JSON output.

For scheduled profiling in a training loop, call `prof.step()` once per profiled iteration. Keep profiling windows short; full-run traces can be very large and slow.

## Tracking Memory Metrics

Profiler tables are useful for debugging, while compact memory metrics are better for experiment tracking. For CUDA runs, reset and log peak stats around the profiled section:

```python
if torch.cuda.is_available():
    torch.cuda.reset_peak_memory_stats()

with accelerator.profile() as prof:
    train_or_eval_step()

if torch.cuda.is_available():
    accelerator.log(
        {
            "memory/peak_allocated_mb": torch.cuda.max_memory_allocated() / 1024**2,
            "memory/peak_reserved_mb": torch.cuda.max_memory_reserved() / 1024**2,
        },
        step=global_step,
    )
```

After profiler-heavy experiments, use `accelerator.clear(...)`, `accelerate.utils.release_memory(...)`, or `clear_device_cache(garbage_collection=True)` to release references before starting another run in the same process.
