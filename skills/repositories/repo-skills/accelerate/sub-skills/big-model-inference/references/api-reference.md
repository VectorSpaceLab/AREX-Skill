# Big-Model API Reference

This reference summarizes Accelerate 1.15 big-model inference APIs that are safe to reason about from local code. Import examples assume `torch` and `accelerate` are installed.

## Meta Initialization

- `from accelerate import init_empty_weights`
  - Signature: `init_empty_weights(include_buffers: Optional[bool] = None)`.
  - Creates modules whose parameters live on PyTorch's `meta` device, avoiding allocation and random initialization cost.
  - Use only for model construction and size/device-map analysis. A meta-initialized model has no real tensor data and cannot be moved or run directly.
- `from accelerate import init_on_device`
  - Signature: `init_on_device(device: torch.device, include_buffers: Optional[bool] = None)`.
  - Constructs parameters on a chosen device; `init_empty_weights` is the `meta`-device specialization.

## Device Maps and Sizing

- `from accelerate.utils import infer_auto_device_map`
  - Signature: `infer_auto_device_map(model, max_memory=None, no_split_module_classes=None, dtype=None, special_dtypes=None, verbose=False, clean_result=True, offload_buffers=False, fallback_allocation=False)`.
  - Computes a map from module names to devices, prioritizing accelerators, then CPU, then disk.
  - Works with meta-initialized models because it analyzes parameter and buffer sizes, not actual values.
  - `max_memory` values can be integers in bytes or strings such as `"12GiB"`, `"24GB"`, or `"512MiB"`.
  - `no_split_module_classes` should include residual blocks or modules that must remain intact.
- `from accelerate.utils import get_balanced_memory`
  - Signature: `get_balanced_memory(model, max_memory=None, no_split_module_classes=None, dtype=None, special_dtypes=None, low_zero=False)`.
  - Builds a balanced `max_memory` plan for automatic maps, optionally reducing GPU 0 usage with `low_zero=True`.
- `from accelerate.utils import compute_module_sizes, calculate_maximum_sizes, check_device_map`
  - Use `compute_module_sizes(model, dtype=None, special_dtypes=None, buffers_only=False)` to inspect byte sizes by module name.
  - Use `calculate_maximum_sizes(model)` to identify total size and largest layer.
  - Use `check_device_map(model, device_map)` to fail early when a map is incomplete or has invalid keys.

## Checkpoint Loading and Dispatch

- `from accelerate import load_checkpoint_and_dispatch`
  - Signature: `load_checkpoint_and_dispatch(model, checkpoint, device_map=None, max_memory=None, no_split_module_classes=None, offload_folder=None, offload_buffers=False, dtype=None, offload_state_dict=None, skip_keys=None, preload_module_classes=None, force_hooks=False, strict=False, full_state_dict=True, broadcast_from_rank0=False)`.
  - Loads a full checkpoint file, a sharded checkpoint index JSON, or a folder containing a single index and shards, then dispatches modules if `device_map` is provided.
  - `device_map="auto"`, `"balanced"`, `"balanced_low_0"`, or `"sequential"` triggers automatic placement.
  - If any map value is `"disk"`, provide `offload_folder`; `offload_state_dict` defaults to `True` in this case.
  - `strict=True` enforces checkpoint keys matching the model state dict.
  - `broadcast_from_rank0=True` requires an initialized distributed process group.
- `from accelerate.utils import load_checkpoint_in_model`
  - Signature: `load_checkpoint_in_model(model, checkpoint, device_map=None, offload_folder=None, dtype=None, offload_state_dict=False, offload_buffers=False, keep_in_fp32_modules=None, offload_8bit_bnb=False, strict=False, full_state_dict=True, broadcast_from_rank0=False)`.
  - Loads tensors into the model according to a device map, but does not install the execution hooks. The checkpoint can also be a folder containing a unique `pytorch_model.bin` or `model.safetensors`. Call `dispatch_model` afterward when the model must run.
- `from accelerate import dispatch_model`
  - Signature: `dispatch_model(model, device_map, main_device=None, state_dict=None, offload_dir=None, offload_index=None, offload_buffers=False, skip_keys=None, preload_module_classes=None, force_hooks=False)`.
  - Attaches hooks and moves submodules so a model split across accelerator, CPU, or disk can execute.
  - Sets `model.hf_device_map` to the final map.
  - Do not map the entire model to `"disk"`; use `disk_offload` for full disk offload.

## CPU and Disk Offload

- `from accelerate import cpu_offload`
  - Signature: `cpu_offload(model, execution_device=None, offload_buffers=False, state_dict=None, preload_module_classes=None)`.
  - Keeps one CPU state dict and loads parameters onto the execution device just in time during forward.
- `from accelerate import cpu_offload_with_hook`
  - Signature: `cpu_offload_with_hook(model, execution_device=None, prev_module_hook=None)`.
  - Returns `(model, hook)`; call `hook.offload()` manually. Useful for model pipelines where one stage should stay resident until the next stage runs.
- `from accelerate import disk_offload`
  - Signature: `disk_offload(model, offload_dir, execution_device=None, offload_buffers=False, preload_module_classes=None)`.
  - Memory-maps model weights from `offload_dir` and loads them during forward. Requires a writable directory and is slower than CPU offload.

## Hooks

- `from accelerate.hooks import ModelHook, AlignDevicesHook, SequentialHook, add_hook_to_module, remove_hook_from_module, remove_hook_from_submodules`
  - Hooks intercept module init/forward/post-forward behavior to align inputs, outputs, parameters, and offloaded tensors.
  - Prefer high-level helpers (`dispatch_model`, `cpu_offload`, `disk_offload`) unless diagnosing hook behavior.
- `from accelerate.hooks import attach_execution_device_hook, attach_align_device_hook, attach_align_device_hook_on_blocks`
  - Lower-level utilities for aligning execution devices and offload behavior across submodules.
- `from accelerate import attach_layerwise_casting_hooks`
  - Signature: `attach_layerwise_casting_hooks(module, storage_dtype, compute_dtype, skip_modules_pattern=None, skip_modules_classes=None, non_blocking=False)`.
  - Stores weights in a lower precision and casts to compute precision around forward. This reduces memory but is not a substitute for checkpoint dispatch.

## Pipeline and Distributed Inference

- `from accelerate.inference import prepare_pippy`
  - Signature: `prepare_pippy(model, split_points='auto', no_split_module_classes=None, example_args=(), example_kwargs=None, num_chunks=None, gather_output=False)`.
  - Wraps a model with PyTorch pipeline parallelism support using tracing example inputs.
  - `split_points='auto'` derives split points from a device map; explicit split points are safer when tracing or placement is surprising.
  - Output is only on the last process unless `gather_output=True`.
- `from accelerate.inference import generate_device_map`
  - Signature: `generate_device_map(model, num_processes=1, no_split_module_classes=None, max_memory=None)`.
  - Computes a device map intended for pipeline placement across processes.
- For data-parallel inference where each process has a full model copy, use `PartialState().split_between_processes(...)`; launch syntax belongs in `../configuration-and-cli/`.

## Memory Estimation

- Programmatic sizing is based on `compute_module_sizes`, `calculate_maximum_sizes`, and `infer_auto_device_map` over meta or real modules.
- The `accelerate estimate-memory` CLI constructs supported `transformers` or `timm` models on `meta` and reports largest layer, total parameter size, and training optimizer estimates. CLI details are routed to `../configuration-and-cli/`.
- Estimates are for model weights and largest layers; inference usually needs extra activation/cache memory and may require more than the reported load-only size.
