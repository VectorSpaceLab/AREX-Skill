# Checkpointing Workflows

## Choose the Right Save API

| Need | Preferred API | Notes |
| --- | --- | --- |
| Resume the same training script | `accelerator.save_state()` / `accelerator.load_state()` | Saves prepared model state, optimizers, schedulers, dataloader sampler/stateful dataloader state when available, GradScaler, RNG state, step, and registered custom objects. |
| Save an arbitrary object once per machine | `accelerator.save(obj, path)` | Distributed-safe replacement for `torch.save`; respects `ProjectConfiguration.save_on_each_node`. |
| Save model weights for later model loading | `accelerator.save_model(model, save_directory, max_shard_size="10GB", safe_serialization=True)` | Handles wrapped models, sharding, and safetensors by default. Backend-specific details still belong with distributed backends. |
| Build a custom state dict | `accelerator.get_state_dict(model)` | Returns the unwrapped model state dict by default, with backend-aware handling. |
| Remove wrappers before custom export | `accelerator.unwrap_model(model)` | Useful before custom save methods or when a library expects the original module class. |

Use `save_state()` for restartability and `save_model()`/`get_state_dict()` for portable model artifacts. A state checkpoint is expected to be restored by the same script with the same prepared object structure.

## Minimal Same-Script Resume Pattern

```python
from accelerate import Accelerator
from accelerate.utils import ProjectConfiguration, set_seed

project_config = ProjectConfiguration(
    project_dir="runs/exp-001",
    automatic_checkpoint_naming=True,
    total_limit=3,
)
accelerator = Accelerator(project_config=project_config)

set_seed(42)
model, optimizer, train_dataloader, scheduler = accelerator.prepare(
    model, optimizer, train_dataloader, scheduler
)

if resume:
    accelerator.load_state(resume_path)  # or omit path with automatic naming to load the latest checkpoint

for epoch in range(starting_epoch, num_epochs):
    for step, batch in enumerate(train_dataloader):
        outputs = model(**batch)
        loss = loss_fn(outputs)
        accelerator.backward(loss)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()

    accelerator.save_state()
```

With `automatic_checkpoint_naming=True`, checkpoints are written under `<project_dir>/checkpoints/checkpoint_<iteration>`. If `total_limit` is set, `save_state()` deletes the oldest checkpoint folders on the main process before writing the next one. If a target automatic folder already exists, Accelerate raises a `ValueError`; set `ProjectConfiguration(iteration=...)` when resuming a run that will continue checkpoint numbering.

## Loading Paths and Map Location

- `accelerator.load_state(path)` requires `path` to exist or raises `ValueError`.
- `accelerator.load_state()` without a path is valid only when `automatic_checkpoint_naming=True`; it selects the numerically latest `checkpoint_<n>` folder.
- `map_location` can be passed through `load_state(path, map_location="cpu")` or `load_state(path, map_location="on_device")`. Any other map location raises `TypeError`.
- If `map_location` is omitted, Accelerate defaults to CPU for single-process runs and to on-device for most multi-device distributed runs.

## Custom Objects

Use `register_for_checkpointing()` for schedulers, counters, tokenizers with internal state, or other same-script stateful objects that expose both methods:

```python
class Counter:
    def __init__(self):
        self.value = 0

    def state_dict(self):
        return {"value": self.value}

    def load_state_dict(self, state):
        self.value = state["value"]

counter = Counter()
accelerator.register_for_checkpointing(counter)
```

Accelerate stores registered objects as `custom_checkpoint_<index>.pkl`. On load, the number of matching custom checkpoint files must equal the number of registered objects, otherwise `load_state()` raises a runtime error. Do not place unrelated files named `custom_checkpoint_<number>.pkl` in a state directory.

## Save and Load Hooks

Use hooks when extra metadata must be saved next to the state checkpoint or when a custom library needs to override model save/load behavior.

```python
def save_metadata(models, weights, output_dir):
    with open(os.path.join(output_dir, "metadata.json"), "w") as handle:
        json.dump({"format": 1}, handle)


def load_metadata(models, input_dir):
    with open(os.path.join(input_dir, "metadata.json")) as handle:
        metadata = json.load(handle)

save_handle = accelerator.register_save_state_pre_hook(save_metadata)
load_handle = accelerator.register_load_state_pre_hook(load_metadata)
```

Important hook details:

- Save hooks run before the lower-level checkpoint writer and receive `(models, weights, output_dir)`.
- Load hooks run before model state is loaded and receive `(models, input_dir)`.
- Hooks return `torch.utils.hooks.RemovableHandle`; call `handle.remove()` to stop using a hook.
- If a save hook fully handles model serialization, it may remove entries from the mutable `weights` list to prevent default model serialization for those entries.
- Pair save and load hooks. A save-only metadata convention is fragile unless load code explicitly tolerates absence.

## RNG and Step State

`save_state()` records Python `random`, NumPy, CPU Torch RNG, available accelerator backend RNG states, and the internal Accelerator step. `load_state()` attempts to restore these states and logs if random states cannot be loaded. For reproducibility, set the initial seed with `accelerate.utils.set_seed(seed)` before constructing randomized datasets/models, and keep dataloader ordering and script object registration consistent across resume.

## Dataloader Resume Notes

State checkpoints can include sampler state for Accelerate sharded iterable datasets and stateful dataloader state when `DataLoaderConfiguration(use_stateful_dataloader=True)` is used. If the checkpoint was saved mid-epoch and the dataloader itself is not stateful enough for the exact use case, combine `load_state()` with the training-loop pattern `accelerator.skip_first_batches(dataloader, already_seen_batches)` in the training-loop sub-skill.

## Unwrapped Model Export Pattern

```python
accelerator.wait_for_everyone()
unwrapped = accelerator.unwrap_model(model)
state_dict = accelerator.get_state_dict(model)
if accelerator.is_main_process:
    unwrapped.save_pretrained(
        output_dir,
        is_main_process=accelerator.is_main_process,
        save_function=accelerator.save,
        state_dict=state_dict,
    )
```

For generic PyTorch modules, `accelerator.save_model(model, output_dir)` is usually simpler and will create sharded safetensors by default when needed.

## Memory Cleanup Between Runs

- `accelerator.free_memory(model, optimizer, scheduler)` releases Accelerator references, garbage-collects, clears device cache where supported, resets `accelerator.step` to `0`, and returns `None` placeholders to reassign.
- `accelerator.clear(...)` is an alias for `free_memory(...)`.
- `accelerate.utils.release_memory(...)` can be used outside an `Accelerator` object for local references.
- `accelerate.utils.clear_device_cache(garbage_collection=True)` is useful after profiler-heavy runs or failed experiments; garbage collection is slower, so do not call it every step.
