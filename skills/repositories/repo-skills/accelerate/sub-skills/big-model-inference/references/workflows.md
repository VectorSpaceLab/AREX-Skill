# Big-Model Inference Workflows

Use these workflows to help future agents solve big-model placement and loading tasks without accidental downloads or heavy GPU runs.

## 1. Inspect a Model Without Allocating Weights

```python
import torch.nn as nn
from accelerate import init_empty_weights
from accelerate.utils import compute_module_sizes, infer_auto_device_map

class TinyBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.proj = nn.Linear(8, 8)
        self.mlp = nn.Sequential(nn.Linear(8, 16), nn.ReLU(), nn.Linear(16, 8))

class TinyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.block0 = TinyBlock()
        self.block1 = TinyBlock()
        self.head = nn.Linear(8, 2)

with init_empty_weights():
    model = TinyModel()

sizes = compute_module_sizes(model)
device_map = infer_auto_device_map(
    model,
    max_memory={"cpu": "512MiB"},
    no_split_module_classes=["TinyBlock"],
)
```

Key checks:

- Parameters should report `device.type == "meta"` before loading.
- `infer_auto_device_map` can run on the meta model because it uses shapes and dtypes.
- `no_split_module_classes` uses class names, not module attribute names.

## 2. Load and Dispatch a Local Checkpoint

Use this only when the user already has local checkpoint files or explicitly approves downloads.

```python
from accelerate import init_empty_weights, load_checkpoint_and_dispatch

with init_empty_weights():
    model = MyModel(config)

model = load_checkpoint_and_dispatch(
    model,
    checkpoint="/path/to/local/checkpoint_or_index_or_folder",
    device_map="auto",
    no_split_module_classes=["DecoderLayer"],
    offload_folder="./offload",
    dtype="float16",
)
```

Decision points:

- `checkpoint` may be a full state-dict file, a sharded index JSON, or a folder with a single index plus shards.
- Provide `offload_folder` when the device map can contain `"disk"`.
- Use `strict=True` when diagnosing missing or unexpected checkpoint keys.
- After dispatch, inspect `model.hf_device_map` rather than assuming all modules are on one device.

## 3. Separate Loading from Hook Dispatch

Use this when debugging checkpoint loading separately from execution hooks.

```python
from accelerate import dispatch_model
from accelerate.utils import load_checkpoint_in_model

load_checkpoint_in_model(
    model,
    checkpoint="./checkpoint",
    device_map=device_map,
    offload_folder="./offload",
    dtype="float16",
)
model = dispatch_model(model, device_map=device_map, offload_dir="./offload")
```

`load_checkpoint_in_model` fills tensors but does not make a split/offloaded model runnable. `dispatch_model` installs the hooks that align inputs, outputs, and just-in-time weights.

## 4. Choose CPU Offload or Disk Offload

Use CPU offload when CPU RAM can hold the weights and the execution device cannot. Use disk offload only when CPU RAM is insufficient or the user accepts slower memory-mapped reads.

```python
from accelerate import cpu_offload, disk_offload

model = cpu_offload(model, execution_device="cuda:0")
# or, for a writable offload directory:
model = disk_offload(model, offload_dir="./offload", execution_device="cuda:0")
```

Notes:

- `cpu_offload_with_hook` returns a hook whose `.offload()` method must be called by the user or pipeline controller.
- `preload_module_classes` is for modules whose registered submodules are not called directly in `forward` but whose tensors are used manually.
- Full-disk placement through `dispatch_model` is rejected; call `disk_offload` instead.

## 5. Design a Device Map

Start with automatic inference, then pin problematic modules manually.

```python
from accelerate.utils import check_device_map, infer_auto_device_map

device_map = infer_auto_device_map(
    model,
    max_memory={0: "20GiB", "cpu": "64GiB"},
    no_split_module_classes=["Block", "DecoderLayer"],
    dtype="float16",
    offload_buffers=True,
)
check_device_map(model, device_map)
```

Guidelines:

- Valid destinations include accelerator indexes such as `0`, device strings such as `"cuda:0"`, `"cpu"`, and `"disk"`.
- Module names in a manual map are prefixes: mapping `"encoder"` maps all children under `encoder`.
- Keep tied weights and residual blocks on compatible devices.
- `clean_result=False` is useful when debugging why the automatic mapper chose individual submodules.

## 6. Estimate Memory Without Downloading Weights

For custom modules, use meta initialization and size utilities. For known `transformers` or `timm` Hub models, the `accelerate estimate-memory` CLI can instantiate configs on `meta`; CLI syntax is documented in `../configuration-and-cli/`.

Interpretation:

- Largest layer matters because offloaded CPU/disk layers need room to be staged back onto the execution device.
- Reported size is primarily weights; KV cache, activations, inputs, temporary tensors, and framework overhead can add substantial inference memory.
- Dtype assumptions change totals; always record whether the estimate used `float32`, `float16`, `bfloat16`, `int8`, or `int4`.

## 7. Distributed Inference Choices

- Use `PartialState().split_between_processes(data)` when each process can hold a full model copy and the goal is batch splitting.
- Use big-model dispatch (`device_map="auto"`) when one model must be spread across devices and only one stage may be active at a time.
- Use `prepare_pippy` when the user wants scheduled pipeline parallelism and accepts the experimental PyTorch pipeline tracing constraints.

Minimal pipeline shape:

```python
import torch
from accelerate.inference import prepare_pippy

model.eval()
example = (torch.zeros(2, 16, dtype=torch.long),)
pipe_model = prepare_pippy(
    model,
    split_points="auto",
    example_args=example,
    num_chunks=2,
    gather_output=False,
)
```

Cautions:

- Example inputs determine tracing behavior and effective batch shape.
- Passing positional `example_args` is generally safer than relying on kwargs for experimental tracing paths.
- With `gather_output=False`, inspect output only on the last process.
