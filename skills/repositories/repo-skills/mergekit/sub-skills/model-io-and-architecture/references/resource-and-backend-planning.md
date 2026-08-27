# Resource and backend planning

Use an explicit resource decision before starting a merge. The merge graph has a
**math device** (where tasks marked `uses_accelerator()` receive tensors) and a
**storage device** (where each task result is retained between dependencies).
They are intentionally separable.

## Decision matrix

| Situation | Recommended baseline | Why / checks |
|---|---|---|
| Unknown host, small checkpoint, or debugging | `--device cpu` with default CPU storage | Most portable. It exercises loading, conversion, planning, and serialization without requiring CUDA. |
| CUDA available and arithmetic is the bottleneck | `--cuda` or `--device cuda` | `MergeOptions` resolves the default device to `cuda`; verify `torch.cuda.is_available()` and the selected index before running. |
| CPU RAM is the bottleneck but one accelerator has headroom | `--device cuda --low-cpu-memory` | Executor stores intermediate tensors on the accelerator rather than CPU. This increases VRAM pressure and transfer sensitivity. |
| Input reads are the bottleneck and VRAM can hold the active input | `--device cuda --read-to-gpu` | `GatherTensors` passes the selected device into `LoadTensor`; checkpoint reads are placed directly on that device. It is not equivalent to `low_cpu_memory`. |
| Independent layer/tensor islands and multiple GPUs | `--multi-gpu`, optionally `--low-cpu-memory` | `MultiGPUExecutor` discovers the accelerator count, partitions weakly connected task islands, and runs workers per device. Verify all devices and their free memory. |
| GPU-rich host intentionally selected | `--gpu-rich` | This is an alias that sets `cuda`, `low_cpu_memory`, `read_to_gpu`, and `multi_gpu`. It does not verify hardware or fit. |
| CUDA unavailable, wrong build, or no free VRAM | `--device cpu` and remove GPU-only flags | `--cuda` is not a CPU fallback once the resolved device is CUDA. Diagnose the backend, device index, driver, and memory before retrying. |

The inspected environment had mergekit 0.1.4, torch 2.13.0 with CUDA 13.0,
eight NVIDIA A100-SXM4-40GB devices at capability 8.0, and a successful one-device
CUDA allocation. Those are host facts, not portable requirements; rerun the
bundled diagnostic on the execution host.

## What each performance switch changes

- `device`: the resolved executor math device. The pre-validator turns `auto`
  into CUDA, XPU, or CPU based on availability. Explicit `cuda:3` selects one
  device; accelerator helper functions treat an explicit index as a count of
  one.
- `cuda`: a boolean default selector. When true and no device is given, it sets
  `device="cuda"`; it does not itself create a stream or choose multi-GPU.
- `low_cpu_memory`: in single-GPU `run_merge`, makes executor storage use the
  selected device. Without it, storage is CPU. This can prevent large CPU
  intermediates but may retain more VRAM.
- `read_to_gpu`: makes `GatherTensors` request the selected device from its
  `LoadTensor` tasks. It can reduce an extra CPU-to-GPU copy but needs room for
  the active input tensors and can worsen OOMs.
- `multi_gpu`: switches from `Executor` to `MultiGPUExecutor`. Main-thread-only
  tasks must be leading or trailing; tasks marked both per-GPU and main-thread
  only are rejected. The worker count defaults to the detected accelerator
  count; the public `MergeOptions` model has no `num_gpus` field.
- `num_threads` / `-j`: calls both `torch.set_num_threads` and
  `torch.set_num_interop_threads` in `apply_global_options`. Set deliberately;
  excessive CPU parallelism can compete with asynchronous writes.
- `lazy_unpickle`: selects mergekit's experimental lazy loader for legacy
  `.bin` checkpoints. Safetensors are already opened through `safe_open` and do
  not need this flag.

A tensor is ultimately moved by `Executor._move_tensors`: accelerator tasks get
inputs on `math_device`, result containers are recursively moved to
`storage_device`, and values are evicted after the schedule's last-use index.
This means peak memory depends on graph live ranges and task grouping, not only
on the final checkpoint size.

## CPU versus CUDA preflight

Run the bundled script before a real merge:

```text
python scripts/mergekit_model_diagnostic.py --check --device cpu  # from this sub-skill directory
python scripts/mergekit_model_diagnostic.py --check --device cuda  # from this sub-skill directory
```

For CUDA, require all of these to be true:

1. the installed torch build reports a CUDA version;
2. `torch.cuda.is_available()` is true;
3. `torch.cuda.device_count()` covers the requested device(s);
4. `get_device_capability()` and free memory are appropriate for the model and
   merge method; and
5. a tiny allocation on the selected device succeeds.

A successful import or `nvidia-smi` alone is not sufficient. If the check fails,
record the exact device string and environment before falling back to CPU. Do
not silently mix CPU tensors into a CUDA-only method; let the executor move
inputs or choose CPU explicitly.

## Input loading and lazy behavior

`ShardedTensorIndex.from_disk` recognizes a single `model.safetensors` or
`pytorch_model.bin`, or either with `.index.json`. For an indexed checkpoint,
its `weight_map` identifies the shard for each key. `LazyTensorLoader` keeps one
current shard under a lock and loads a requested tensor, optionally through an
alias. `flush()` releases the current loader; it is useful between independently
large phases.

Legacy pickle checkpoints have two paths:

- default `DumbPytorchLoader`: `torch.load(..., weights_only=True)` eagerly loads
  a shard (and can still require substantial RAM);
- `LazyPickleLoader`: the experimental `LazyTorchUnpickler` records deferred
  storage offsets in a torch ZIP archive and materializes a tensor on demand.

The lazy unpickler accepts a deliberately narrow set of torch/numpy rebuild
objects and raises `pickle.UnpicklingError` for unsupported classes. It expects
recognized torch archive layout and storage metadata; it is not a general
pickle reader and is not guaranteed for arbitrary old `.bin` files. Use a
trusted checkpoint, disable lazy mode when it fails, and retry with a normal
weights-only load or convert the checkpoint to safetensors. Never treat an
untrusted pickle as safe merely because lazy mode rejected some classes.

## Sharding and safe output

`out_shard_size` is a decimal byte threshold parsed from an integer or a `K/M/B`
suffix; default is 5,000,000,000 bytes. The writer flushes before adding a
non-empty shard that would exceed the threshold, except a single tensor larger
than the threshold is still written as one shard. Estimate a tensor's payload as
`tensor.numel() * tensor.element_size()` and leave headroom for live graph values,
serialization buffers, and asynchronous writes.

Default output is safe serialization:

- one shard: `model.safetensors`;
- multiple shards: standardized numbered safetensors plus
  `model.safetensors.index.json` with a `weight_map` and total size metadata.

`--safe-serialization/--no-safe-serialization` selects safetensors or legacy
`pytorch_model-*.bin`. Prefer safe serialization. The writer requires contiguous
storage; `save_tensor` makes a contiguous copy when necessary. `clone_tensors`
forces another clone and is useful when tied/shared tensors trigger safetensors
memory-sharing errors, at the cost of memory. `async_write` and `write_threads`
can improve throughput but retain in-flight shard buffers and therefore raise
peak host memory. Keep writes synchronous while diagnosing correctness.

The writer creates but does not clean `out_path`. Use a new empty directory for
retries. After finalization, check that every index target exists, that no old
shard with the same name was reused, and that a loader can enumerate the result.
Do not declare success from a directory containing only `config.json`.

## Config, tokenizer, tagalong files, and model card

`run_merge` saves the output config after graph execution. It copies or
reserializes the donor tokenizer when no tokenizer task was configured and
`copy_tokenizer` is enabled. A configured tokenizer task can change embedding
rows and then updates the output vocabulary size (including
`pad_to_multiple_of`). If tokenizer copying fails, mergekit logs that the merge
can still be successful but the tokenizer must be supplied separately. Check:

- tokenizer config plus at least one usable tokenizer asset;
- special-token maps, merges/model files, and any requested chat template;
- output `config.json` vocabulary size versus tokenizer vocabulary;
- architecture-declared tagalong files;
- `README.md` and `mergekit_config.yml` when `write_model_card=True`.

`write_model_card` creates a generated starting point, not a quality or safety
review. If no tokenizer exists and a chat template was requested, the template
is not saved; either configure a tokenizer source or make that limitation
explicit. A missing optional tokenizer should be recovered without rerunning the
expensive tensor merge when possible.
