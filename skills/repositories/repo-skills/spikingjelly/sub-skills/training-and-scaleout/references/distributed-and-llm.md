# Distributed vision and reference-only LLM scale-out

This reference covers the bounded distributed-vision surface owned by the `training-and-scaleout` sub-skill and keeps Megatron Core / LLM scale-out as reference-only.

## 1) Verified live signatures

### `distributed.vision`

- `ModelConfig(time_steps: int = 4, num_classes: int = 1000, step_mode: Literal['s', 'm'] = 'm')`
- `ModelBuilder(config: ModelConfig) -> None`
- `SEWResNet34Config(time_steps: int = 4, num_classes: int = 1000, step_mode: Literal['s', 'm'] = 'm', image_size: int = 224, in_channels: int = 3, connection: str = 'ADD', neuron_backend: str = 'torch', tau: float = 2.0, detach_reset: bool = True)`
- `SpikformerConfig(time_steps: int = 4, num_classes: int = 1000, step_mode: Literal['s', 'm'] = 'm', image_height: int = 224, image_width: int = 224, in_channels: int = 3, neuron_backend: str = 'torch')`
- `SpikformerCIFAR10Config(time_steps: int = 4, num_classes: int = 10, step_mode: Literal['s', 'm'] = 'm', neuron_backend: str = 'torch')`
- `TrainingConfig(model: ModelConfig, dataset_builder: str, dataset_kwargs: dict[str, Any] = ..., input_layout: Literal['NCHW', 'NTCHW'] = 'NCHW', epochs: int = 1, batch_size: int = 32, workers: int = 4, optimizer: str = 'torch.optim.AdamW', optimizer_kwargs: dict[str, Any] = ..., loss_function: str = 'torch.nn.functional.cross_entropy', loss_kwargs: dict[str, Any] = ..., mixup_alpha: float = 0.0, scheduler: Optional[str] = None, scheduler_kwargs: dict[str, Any] = ..., tensor_parallel_size: int = 1, pipeline_parallel_size: int = 1, pipeline_microbatches: int = 1, data_parallel: Literal['ddp', 'fsdp2'] = 'ddp', precision: Literal['fp32', 'bf16', 'fp16'] = 'bf16', memopt_level: int = 0, memopt_compress_inputs: bool = False, max_steps: Optional[int] = None, timing_warmup_steps: int = 0, checkpoint_dir: Optional[Path] = None, checkpoint_interval: int = 0, resume: Optional[Path] = None, seed: int = 1234)`
- `build_imagefolder_datasets(root, image_size=224, train_subdirectory='train', validation_subdirectory='val')`
- `train_classification(config: TrainingConfig) -> dict[str, float]`

### `distributed.tensor_parallel`

- `ChannelShardConv2d(source: nn.Module, process_group: Optional[Any], mode: Literal['colwise', 'rowwise'])`
- `ChannelShardBatchNorm2d(source: nn.Module, process_group: Optional[Any])`
- `ChannelShardConv1d(source: nn.Module, process_group: Optional[Any], mode: Literal['colwise', 'rowwise'])`
- `ChannelShardBatchNorm1d(source: nn.Module, process_group: Optional[Any])`

### `distributed.llm` reference-only surface

- `ModelConfig(*, transformer, vocab_size, max_sequence_length, time_steps, share_embeddings_and_output_weights=False, position_embedding_type='rope')`
- `ModelBuilder(config: ModelConfig) -> None`
- `TrainingConfig(model, optimizer, dataset_builder, sequence_length, micro_batch_size, global_batch_size, train_steps, timing_warmup_steps=0, dataset_kwargs=..., eval_interval=0, eval_steps=0, log_interval=10, lr_warmup_steps=0, lr_decay_steps=None, lr_decay_style='cosine', checkpoint_dir=None, checkpoint_interval=0, resume=None, seed=1234, use_snn_memopt=False)`
- `plan_training(config, *, world_size, device_memory_bytes, objective='throughput', memory_fraction=0.9)`
- `train(config) -> dict[str, float]`

## 2) Distributed-vision contract

`distributed.vision` is the canonical entry point for bounded multi-GPU image-classification training.

### What the config owns

- Image and topology facts: `time_steps`, `step_mode`, `input_layout`, `tensor_parallel_size`, `pipeline_parallel_size`, `pipeline_microbatches`, and `data_parallel`.
- Optimization facts: optimizer import path, optimizer kwargs, scheduler import path, scheduler kwargs, loss import path, loss kwargs, precision, memopt, and checkpointing.
- Dataset builder facts: full import path plus a JSON-serializable kwargs dict.

### What the runtime owns

- NCCL process-group initialization.
- `DeviceMesh` construction across DP / PP / TP.
- Model construction through `ModelBuilder.build(...)`.
- DDP or FSDP2 wrapping.
- The training loop, validation loop, and checkpoint lifecycle.

### Topology rules that matter

| Rule | Why it exists |
| --- | --- |
| `world_size % (tensor_parallel_size * pipeline_parallel_size) == 0` | The mesh must split cleanly into model-parallel groups and DP replicas |
| `batch_size` is per DP rank | The config batch is local, not global |
| Global batch is `batch_size * data_parallel_size` | TP and PP do not multiply the sample count |
| `batch_size % pipeline_microbatches == 0` | PP microbatches must evenly divide the local batch |
| `step_mode='m'` is required for PP in the built-in vision configs | PP expects time-major model execution |
| `precision='fp16'` is rejected for PP in the built-in vision configs | Built-in PP currently supports `fp32` and `bf16` only |
| `memopt_level > 0` is rejected with PP for the built-in SEW/Spikformer builders | The builders explicitly disallow that combination |
| `SpikformerConfig` requires `step_mode='m'` | The architecture is naturally multi-step |
| `SEWResNet34Config` accepts both `s` and `m` | It can be used in legacy or distributed mode |
| `SpikformerCIFAR10Config` fixes the 32×32 / 4×4 / 384 / 12-head / 4-block layout | This is the official CIFAR-10 variant |

### Input-layout rule

`input_layout` is explicit and must match the DataLoader batch layout:

- `NCHW` for static images `[N, C, H, W]`
- `NTCHW` for batch-first sequences `[N, T, C, H, W]`

Do not infer layout from tensor rank.

### Output-layout rule

The distributed trainer accepts classifier outputs in either of these forms:

- `[N, C]`
- `[T, N, C]`

If the model returns a sequence, the trainer reduces it over time before the loss.

## 3) Vision model-builder seam

The required builder contract is the seam between declarative config and runtime topology.

```python
class MyModelBuilder(vision.ModelBuilder):
    def build(
        self,
        *,
        process_group,
        pipeline_rank,
        pipeline_size,
        pipeline_microbatches,
        device,
        micro_batch_size,
        memopt_level,
        memopt_compress_inputs,
    ):
        ...
        return model, fsdp_roots, pipeline_input_shape, pipeline_output_shape
```

### What `build(...)` must return

- A local model shard for the current PP rank.
- A tuple of FSDP2 root module names, ordered from inner to outer.
- `pipeline_input_shape` when PP is enabled, otherwise `None`.
- `pipeline_output_shape` when PP is enabled, otherwise `None`.

### Built-in builder behavior

- `SEWResNet34Builder` applies `ChannelShardConv2d` and `ChannelShardBatchNorm2d` inside each `BasicBlock`.
- `SpikformerBuilder` applies channel sharding to patch-stem convolutions, head-sharded QKV projection, and MLP projections.
- Both builders reject PP + memopt combinations.
- `SpikformerBuilder` rejects ragged image dimensions when PP is enabled.

## 4) Tensor-parallel building blocks

The public `distributed.tensor_parallel` modules are the primitives for architecture-specific channel sharding.

### Channel-shard behavior

- `colwise` shards output channels.
- `rowwise` shards input channels.
- The wrappers support only `groups=1` convolutions.
- They preserve the `step_mode` of the wrapped module.
- Multi-step mode expects `[T, N, C, H, W]` or `[T, N, C, L]` shapes.

### When to use which primitive

| Primitive | Typical use |
| --- | --- |
| `ChannelShardConv2d(..., 'colwise')` | First convolution in a residual block or any layer whose output channels are partitioned |
| `ChannelShardConv2d(..., 'rowwise')` | Downstream convolution that consumes local channels from the preceding colwise shard |
| `ChannelShardBatchNorm2d` | Normalize the local channel slice after a channel-sharded convolution |
| `ChannelShardConv1d(..., 'colwise')` | Spikformer QKV or MLP 1D projections that shard by feature channels |
| `ChannelShardConv1d(..., 'rowwise')` | Spikformer projections that consume local feature slices |
| `ChannelShardBatchNorm1d` | Normalize 1D local channel slices in token-first or token-last projections |

### Topology caution

The sharded tensor-parallel modules do not replace the need for a valid data-parallel or pipeline-parallel topology. They only define the local model parallelism within a rank group.

## 5) Built-in distributed vision configs

### `SEWResNet34Config`

Use this when you want the built-in SEW-ResNet34 distributed path.

Key facts:

- `image_size` must be positive.
- `in_channels` must remain `3`.
- `connection` must be one of `"ADD"`, `"AND"`, or `"IAND"`.
- `tau` must be greater than `1.0`.
- `step_mode='s'` is allowed, but PP and memopt are then unavailable.

### `SpikformerConfig`

Use this when you want the ImageNet-style Spikformer-S path.

Key facts:

- `step_mode` must be `"m"`.
- `image_height`, `image_width`, and `in_channels` must be positive.
- PP requires the image dimensions to be divisible by the patch size used by the model.

### `SpikformerCIFAR10Config`

Use this for the official CIFAR-10 Spikformer.

Key facts:

- It hardcodes the 32×32, 4×4-patch, 384-channel, 12-head, 4-block layout.
- It also requires `step_mode='m'`.
- It is the best built-in target for a fast topology smoke because its PP boundary shapes are deterministic.

## 6) Practical topology guidance

A good bounded decision order is:

1. **DDP only** — simplest and best for small or medium models.
2. **FSDP2** — use when memory is the main constraint and the model already fits the built-in FSDP2 root structure.
3. **TP** — use when the architecture has natural channel or head splits and the built-in builder already exposes them.
4. **PP** — use when the architecture cleanly stages and you can satisfy time/layout constraints.
5. **TP + PP + FSDP2** — only after the simpler cases are working and the builder explicitly supports the combination.

Recommended starter choices:

- `SEWResNet34Config` with `data_parallel='ddp'` when you want the least moving parts.
- `SEWResNet34Config` with `data_parallel='fsdp2'` when memory is tight.
- `SpikformerConfig` with `pipeline_parallel_size > 1` only when you are ready to respect the multi-step and patch-grid constraints.
- `SpikformerCIFAR10Config` as the smallest deterministic PP smoke target.

## 7) Reference-only LLM scale-out

The LLM surface is intentionally not the primary owner of this sub-skill.

Treat it as reference-only unless a future scope explicitly prepares Python 3.12 plus Megatron Core and asks for LLM scale-out.

### What the reference surface means

- `distributed.llm` reuses the same high-level `ModelConfig` / `ModelBuilder` / `TrainingConfig` pattern, but for Megatron Core.
- `plan_training(...)` searches TP / PP / CP combinations and memory policy for a given world size and memory budget.
- `train(...)` requires the Megatron Core runtime and its distributed optimizer.

### Current scope boundary

The prepared inspection environment for this repo did **not** prepare the optional Megatron stack. Do not describe those workflows as verified runtime guidance here.

## 8) Evidence anchors

Primary evidence used for this reference:

- `spikingjelly/activation_based/distributed/vision/config.py`
- `spikingjelly/activation_based/distributed/vision/training.py`
- `spikingjelly/activation_based/distributed/vision/sew_resnet.py`
- `spikingjelly/activation_based/distributed/vision/spikformer.py`
- `spikingjelly/activation_based/distributed/tensor_parallel/channel.py`
- `spikingjelly/activation_based/distributed/llm/{config,planning,training}.py`
- `docs/source/tutorials/en/distributed_training.rst`
- `docs/source/changelog.rst`
- `test/activation_based/test_distributed_vision.py`
- `test/activation_based/test_distributed_tensor_parallel.py`
- `test/activation_based/test_distributed_config.py`
- `test/activation_based/test_distributed_planning.py`
- `skills/tests/spikingjelly/reports/environment/repo_env_report.json`
