# Verified API reference

This catalog records the installed mergekit 0.1.4 interfaces inspected from the
package source and live environment. It is intentionally a decision aid, not a
copy of implementation internals. Signatures use Python notation and retain
keyword-only markers where the package requires them.

## Model identity and loading

| API | Signature / contract | Operational use |
|---|---|---|
| `ModelPath` | `ModelPath(*, path: str, revision: Optional[str] = None)` | Frozen Pydantic model. A string is accepted by validation and becomes `path` plus an optional `revision`. `str(ModelPath)` emits `path@revision` when a revision exists. |
| `ModelReference` | `ModelReference(*, model: ModelPath, lora: Optional[ModelPath] = None, override_architecture: Optional[str] = None)` | Frozen reference to a model and optional LoRA. String validation accepts `MODEL` or `MODEL+LORA`; each component may have one `@REVISION`. |
| `ModelReference.parse` | `parse(value: str) -> ModelReference` | The stable string entry point. It is verified to accept a string, including local paths, Hub IDs, revisions, and `+` LoRA syntax. More than one `+` component or more than one `@` in a component raises `RuntimeError`. |
| `ModelReference.config` | `config(trust_remote_code: bool = False) -> transformers.PretrainedConfig` | Calls `AutoConfig.from_pretrained` with the model path and revision. `override_architecture` replaces `config.architectures` with a one-item list. It may resolve/download Hub metadata. |
| `ModelReference.local_path` | `local_path(cache_dir: Optional[str] = None, ignore_lora: bool = False) -> str` | Returns a local directory unchanged when it exists; otherwise uses Hub file listing and `snapshot_download`. It selects JSON/tokenizer files plus safetensors when available, otherwise BIN. An unmerged LoRA is rejected unless `ignore_lora=True`; normal merge flow should call `merged()`. |
| `ModelReference.merged` | `merged(cache_dir: Optional[str] = None, trust_remote_code: bool = False, lora_merge_dtype: Optional[str] = None) -> ModelReference` | No-op without LoRA. With LoRA, requires `cache_dir`, loads the base through an architecture-selected Transformers auto class, applies PEFT, calls `merge_and_unload`, and saves a safe-serialized cached model. |
| `ModelReference.config` | `config(trust_remote_code: bool = False) -> PretrainedConfig` | Loads the source config, optionally replacing its architecture list with `override_architecture`. |
| `ModelReference.tensor_index` | `tensor_index(cache_dir: Optional[str] = None) -> ShardedTensorIndex` | Builds an index from the resolved local path. This inspects model files/index metadata. |
| `ModelReference.lazy_loader` | `lazy_loader(cache_dir: Optional[str] = None, lazy_unpickle: bool = True) -> LazyTensorLoader` | Creates a sharded loader. The default here is `True`; merge options default `lazy_unpickle=False`, so pass the actual policy explicitly. |
| `dtype_from_name` | `dtype_from_name(name: Optional[str]) -> Optional[torch.dtype]` | Recognizes `bfloat16`, `float16`, `float32`, `int64`, with or without `torch.`. Other names raise `RuntimeError`. |
| `parse_kmb` | `parse_kmb(value: Union[str, int]) -> int` | Parses decimal integer strings and suffixes `k`, `m`, `b` as powers of 1000, not binary IEC units. |

`ModelReference` is hashable/frozen and is used as a loader-cache key. A model
revision is part of its identity; do not strip it when reporting a run or
sharing a cache. A LoRA reference is not itself a checkpoint layout.

## Architecture and planning

| API | Signature / contract | Operational use |
|---|---|---|
| `arch_info_for_config` | `arch_info_for_config(config: PretrainedConfig) -> Optional[ModelArchitecture]` | Requires exactly one `config.architectures` entry. Selects a bundled JSON definition, or the special AFMoE/GLM4-MoE definitions; returns `None` when no definition is found. |
| `get_architecture_info` | `get_architecture_info(config: MergeConfiguration, options: MergeOptions) -> ModelArchitecture` | Checks that models are referenced, resolves every config, rejects differing known architectures unless `allow_crimes`, then falls back to auto inference. |
| `WeightInfo` | `WeightInfo(*, name: str, is_embed: bool = False, optional: bool = False, aliases: Optional[Tuple[str, ...]] = None, force_dtype: Optional[str] = None, tied_names: Optional[Tuple[str, ...]] = None)` | Describes an output tensor. `optional` permits absence, `aliases` are alternative checkpoint names, `tied_names` aid tied-weight lookup, and `force_dtype` overrides the merge/output dtype for this weight. |
| `ConfiguredModuleArchitecture` | `ConfiguredModuleArchitecture(*, info: ModuleArchitecture, config: PretrainedConfig, weight_prefix: Optional[str] = None)` | Binds a module definition to a config; exposes `num_layers`, `pre_weights`, `layer_weights(index)`, `post_weights`, and `all_weights`. |
| `ConfiguredModelArchitecture` | `ConfiguredModelArchitecture(*, info: ModelArchitecture, config: PretrainedConfig)` | Binds a model architecture to a config and exposes `all_weights()` and `get_module(module_name)`. |
| `MergePlanner` | `MergePlanner(config, arch_info, options, out_model_config)` | Constructor is positional in the inspected source. `normalize_config()` expands `models` into module model lists, `slices` into one module, and module models into full-range input slices. `plan_to_disk(out_path)` returns writer/save/finalize/tokenizer tasks; `plan_in_memory()` returns `ReturnTensor` tasks. |
| `Task` | Abstract frozen Pydantic generic with `arguments() -> Dict[str, Task]` and `execute(**kwargs) -> ValueT` | A task declares its dependencies by argument name. Scheduling hooks are `priority() -> int`, `group_label() -> Optional[str]`, `uses_accelerator() -> bool`, `main_thread_only() -> bool`, and `duplicate_per_gpu() -> bool`. |
| `TaskUniverse` | `TaskUniverse(tasks: Optional[Iterable[Task]] = None)` | Registers tasks and recursively registers dependencies. `add_task(task, recursive=True) -> TaskHandle`; `get_handle(task) -> Optional[TaskHandle]`. |
| `build_schedule` | `build_schedule(targets: List[TaskHandle], cached_values: Dict[TaskHandle, Any]) -> ExecutionSchedule` | Topologically orders dependencies, uses group/priority as tie-breakers, and records the last schedule index at which each result is needed. |
| `Executor` | `Executor(targets: Union[List[Task], List[TaskHandle]], math_device: torch.device = torch.device("cpu"), storage_device: torch.device = torch.device("cpu"), cached_values: Optional[Dict[TaskHandle, Any]] = None)` | Runs one graph. Accelerator tasks receive tensors on `math_device`; every result is moved to `storage_device`; expired values are evicted after last use. `run(quiet=False, desc=None)` yields target task/value pairs; `execute(desc=None)` discards them. |
| `MultiGPUExecutor` | `MultiGPUExecutor(targets: List[Task], num_gpus: Optional[int] = None, storage_device: Optional[torch.device] = None)` | Discovers the accelerator type/count when `num_gpus` is omitted, partitions independent islands, runs GPU workers, and keeps main-thread-only leading/trailing work on the main thread. It is selected by `run_merge` when `options.multi_gpu` is true. |

`TaskHandle` belongs to one `TaskUniverse`; do not mix handles from different
universes. `Executor` accepts strings for `math_device` and `storage_device` in
practice because its constructor converts them with `torch.device`.

## Checkpoint IO and output

| API | Signature / contract | Operational use |
|---|---|---|
| `ShardedTensorIndex.from_disk` | `from_disk(base_path: str) -> ShardedTensorIndex` | Searches for `model.safetensors` or `pytorch_model.bin`, including `.index.json`; an index maps each tensor to a shard. Raises `RuntimeError` if no supported model file is found. |
| `ShardedTensorIndex.from_file` | `from_file(file_path: str) -> ShardedTensorIndex` | Inspects a single safetensors file or loads a BIN checkpoint to `meta` to enumerate keys. Handles a top-level `state_dict` wrapper for BIN. |
| `LazyTensorLoader` | `LazyTensorLoader(index: ShardedTensorIndex, lazy_unpickle: bool = True)` | Holds one current shard under a lock. `get_tensor(key, device="cpu", aliases=None, raise_on_missing=True) -> Optional[Tensor]` resolves aliases and loads only the needed tensor; `flush()` drops the current shard; `from_disk(base_path, lazy_unpickle=True)` is a convenience constructor. |
| `TensorLoader.get` | `get(shard_path: str, use_lazy_unpickle: bool = False, device: Optional[str] = None) -> TensorLoader` | Safetensors uses `safe_open`; BIN uses `LazyPickleLoader` only when requested, otherwise `DumbPytorchLoader` with `torch.load(..., weights_only=True)`. |
| `LoadTensor` | `LoadTensor(*, model, tensor, dtype=None, device=None, optional=False, aliases=None, tied_names=None, per_gpu=False)` | Graph task that resolves exact/alias/tied names, then asks checkpoint conversion for a missing target. Required absence raises; optional absence returns `None`. |
| `GatherTensors` | `GatherTensors(*, weight_info: ImmutableMap[ModelReference, WeightInfo], dtype=None, device=None)` | Creates one `LoadTensor` dependency per model and returns a model-to-tensor dictionary, omitting optional `None` values. |
| `TensorWriter` | `TensorWriter(out_path: str, max_shard_size: int = 5000000000, safe_serialization: bool = True, override_basename: Optional[str] = None, use_async: bool = False, max_write_threads: int = 1)` | Buffers tensors until the decimal byte threshold, writes `.safetensors` by default or `.bin` otherwise, then renames shards to standard HF names and writes an index for multiple shards. `save_tensor(name, tensor, clone=False)` and `finalize()` are the core calls. |
| `run_merge` | `run_merge(merge_config, out_path: str, options: MergeOptions, config_source: Optional[str] = None)` | Resolves architecture, initializes loader cache, warms loaders, plans disk tasks, chooses `Executor` or `MultiGPUExecutor`, saves config, model card/config YAML, tokenizer, and architecture tagalong files. |

For output, `TensorWriter` creates the destination directory but does not clean
old files. A one-shard safe output is `model.safetensors`; multiple shards are
`model-00001-of-NNNNN.safetensors` plus `model.safetensors.index.json`. Unsafe
pickle output uses the analogous `pytorch_model` names. A failed or repeated
run can leave collisions; use a new empty directory or clean it after
confirming no required artifact remains.

## `MergeOptions` fields and defaults

The inspected Pydantic signature is:

```text
MergeOptions(*, allow_crimes=False, transformers_cache=None,
  lora_merge_cache=None, lora_merge_dtype=None, cuda=False, device=None,
  low_cpu_memory=False, out_shard_size=5000000000, copy_tokenizer=True,
  clone_tensors=False, trust_remote_code=False, random_seed=None,
  lazy_unpickle=False, write_model_card=True, safe_serialization=True,
  verbosity=0, quiet=False, read_to_gpu=False, multi_gpu=False,
  num_threads=None, gpu_rich=False, async_write=False, write_threads=1)
```

The pre-validation rules set `device="cuda"` when `cuda` or `gpu_rich` is true,
otherwise `device="cpu"`; `device="auto"` selects CUDA, then XPU, then CPU.
`gpu_rich` additionally enables `cuda`, `low_cpu_memory`, `read_to_gpu`, and
`multi_gpu`. `cuda` is therefore a default-device selector; `device` is the
explicit compute choice consumed by the merge executor.
