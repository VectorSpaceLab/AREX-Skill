# Parallelism, MoE, and Checkpointing Workflows

## Pipeline Parallelism

1. Convert the model into a sequence where each layer accepts and returns either one tensor or a tuple of tensors.
2. Use `LayerSpec` for large layers so construction is delayed to the owning stage; use `TiedLayerSpec` with a shared key for tied embeddings or heads.
3. Choose `num_stages` or a `ProcessTopology`. Ensure total distributed world size is divisible by pipeline stages and any additional data/model axes.
4. Pass a `loss_fn` when labels are consumed on the last stage; make the dataloader yield `(inputs, labels)`.
5. Initialize DeepSpeed with the `PipelineModule`; train with `engine.train_batch(data_iter=...)` and evaluate with `engine.eval_batch(...)`.
6. If activation memory is the bottleneck, start with `activation_checkpoint_interval` on `PipelineModule` before adding global checkpointing configuration.

Minimal pattern:

```python
from deepspeed.pipe import LayerSpec, PipelineModule, TiedLayerSpec

layers = [
    TiedLayerSpec("tok_embed", EmbeddingLayer, vocab_size, hidden_size),
    *[LayerSpec(Block, hidden_size) for _ in range(num_layers)],
    TiedLayerSpec("tok_embed", OutputHead, vocab_size, hidden_size),
]
model = PipelineModule(layers=layers, num_stages=pipe_stages, loss_fn=loss_fn)
loss = engine.train_batch(data_iter=iter(train_loader))
```

Prefer explicit tuple packing for transformer blocks that need masks, position ids, or residual metadata across stages. Avoid ordinary `engine(batch)`, `engine.backward(loss)`, and `engine.step()` calls with `PipelineEngine`.

## MoE and Expert Parallelism

1. Replace a same-input/output-dimension dense sublayer with `deepspeed.moe.layer.MoE(hidden_size, expert=..., num_experts=..., ep_size=...)`.
2. Verify `num_experts % ep_size == 0` before constructing the layer. Treat this as a design-time validation, not a runtime surprise.
3. Unpack MoE outputs and add the auxiliary load-balancing loss to the main objective according to the model's loss scale.
4. Wrap model parameters with `split_params_into_different_moe_groups_for_optimizer()` before `deepspeed.initialize()` when the optimizer must distinguish MoE parameters.
5. For expert tensor parallelism, set `enable_expert_tensor_parallelism=True` only when model-parallel groups are initialized and the expert implementation supports sharding.
6. For PR-MoE, verify the current source behavior around list-valued `num_experts`; if unsupported, use scalar expert counts or a tested version-specific path.

Minimal pattern:

```python
from deepspeed.moe.layer import MoE
from deepspeed.moe.utils import split_params_into_different_moe_groups_for_optimizer

self.moe = MoE(hidden_size=hidden_size, expert=Expert(hidden_size), num_experts=experts, ep_size=ep_size, k=1)

output, l_aux, _ = self.moe(hidden_states)
loss = task_loss + aux_loss_weight * l_aux
param_groups = split_params_into_different_moe_groups_for_optimizer({"params": model.parameters(), "name": "parameters"})
```

Keep basic ZeRO stage selection and offload tuning in the training configuration layer; this sub-skill owns the MoE-specific parameter grouping and expert sizing.

## Sequence Parallelism

### DistributedAttention Path

1. Build sequence-parallel process groups before model construction.
2. Replace the local attention core with `DistributedAttention(local_attention, sequence_parallel_group)`.
3. Ensure attention heads divide evenly by sequence-parallel size.
4. Do not combine the older Ulysses path with unsupported tensor/pipeline parallel combinations unless the target codebase already proves it.

### Hugging Face Ulysses Path

1. Call `UlyssesSPAttentionHF.register_with_transformers(...)` before loading the HF model when registering by model name.
2. Include `sequence_parallel_size` in the DeepSpeed config and pass the returned MPU-like object to `deepspeed.initialize(..., mpu=mpu)`.
3. Wrap the dataloader with `UlyssesSPDataLoaderAdapter` so input ids, position ids, labels, and shifted labels are sharded consistently.
4. Aggregate loss across SP ranks with differentiable collectives, weighted by valid token counts when labels contain ignored positions.
5. If fixed sequence length is used, require `seq_length % sequence_parallel_size == 0`; if variable length is used, validate every batch.

### AutoSP Path

Use AutoSP only for supported multimodal or attention-module patterns. Inspect detected modules and warnings; if AutoSP skips LLM attention wrapping, fall back to explicit Ulysses/HF registration or do not claim full SP coverage.

## Activation Checkpointing

1. Decide whether checkpointing is owned by `PipelineModule` interval settings, global `deepspeed.checkpointing.configure()`, or explicit `checkpoint(function, *args)` calls.
2. Use `partition_activations` only with an MPU/model-parallel object that exposes the expected rank/world/group methods.
3. Use `contiguous_checkpointing` only when `num_checkpoints` is known and activation shapes are compatible.
4. Use `checkpoint_in_cpu` for memory pressure after confirming CPU transfer overhead is acceptable.
5. Avoid stacking pipeline interval checkpointing, manual checkpoint wrappers, and config-driven checkpointing unless the user needs that exact memory trade-off.

Minimal pattern:

```python
import deepspeed.checkpointing as checkpointing

checkpointing.configure(mpu, deepspeed_config=config)
hidden = checkpointing.checkpoint(block_forward, hidden, attention_mask)
```

## Native Verification Candidates

When verifying this skill, use the artifact-owned native candidate map rather than reopening source tests from runtime guidance. Run only tiny CPU-safe or explicitly GPU/distributed-safe selections, and record skips for missing distributed backends.

Useful synthetic cases for this sub-skill:

- Design a tiny tied-embedding pipeline model where two `TiedLayerSpec` entries share a key, tuple data carries `(tokens, mask)`, and training uses only `train_batch()`.
- Diagnose an MoE model with `num_experts=6`, `ep_size=4`, tuple output mishandling, and missing MoE optimizer param-group splitting.
