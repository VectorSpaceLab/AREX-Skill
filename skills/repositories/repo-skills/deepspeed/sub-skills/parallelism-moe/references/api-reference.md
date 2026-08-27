# Parallelism, MoE, Sequence, and Checkpointing API Reference

This reference summarizes public APIs that future agents commonly need when designing DeepSpeed parallel training. Validate current imports with `scripts/inspect_parallelism_api.py` before generating code for a specific checkout or installed package.

## Pipeline Parallelism

| API | Signature or role | Notes |
| --- | --- | --- |
| `deepspeed.pipe.PipelineModule` | `(layers, num_stages=None, topology=None, loss_fn=None, seed_layers=False, seed_fn=None, base_seed=1234, partition_method='parameters', activation_checkpoint_interval=0, activation_checkpoint_func=checkpoint, checkpointable_layers=None, dynamic_shape=False)` | Wraps a sequential layer graph and partitions it across stages. `layers` may be modules, callables, `LayerSpec`, or `TiedLayerSpec`. |
| `deepspeed.pipe.LayerSpec` | `(typename, *module_args, **module_kwargs)` | Delays layer construction so each stage builds only its local modules, reducing peak memory during large-model construction. |
| `deepspeed.pipe.TiedLayerSpec` | `(key, typename, *module_args, forward_fn=None, tied_weight_attr=['weight'], **module_kwargs)` | Declares layers whose weights must be tied across pipeline stages. Reuse the same `key` for tied instances and ensure compatible forward behavior. |
| `deepspeed.runtime.pipe.ProcessTopology` | `(axes, dims)` | Names and sizes process-grid axes such as `pipe`, `data`, and model-parallel dimensions. Use it when simple `num_stages` is not enough. |
| `PipelineEngine.train_batch` | `train_batch(data_iter=None)` | Advances an entire pipelined batch, including forward, backward, gradient reduction, and optimizer step. Ordinary `forward` / `backward` / `step` loops do not apply. |
| `PipelineEngine.eval_batch` | `eval_batch(data_iter, return_logits=False, compute_loss=True, reduce_output='avg')` | Runs evaluation through the pipeline schedule; use instead of calling the engine like a normal module. |

Pipeline model inputs and outputs should be one tensor or a tuple of tensors between layers. Dataloaders for pipeline training conventionally return `(inputs, labels)`, where the first stage consumes inputs and the last stage consumes labels for `loss_fn`.

## MoE and Expert Parallelism

| API | Signature or role | Notes |
| --- | --- | --- |
| `deepspeed.moe.layer.MoE` | `(hidden_size: int, expert: torch.nn.Module, num_experts: int = 1, ep_size: int = 1, k: int = 1, capacity_factor: float = 1.0, eval_capacity_factor: float = 1.0, min_capacity: int = 4, use_residual: bool = False, noisy_gate_policy: Optional[str] = None, drop_tokens: bool = True, use_rts: bool = True, use_tutel: bool = False, enable_expert_tensor_parallelism: bool = False, top2_2nd_expert_sampling: bool = True) -> None` | Creates an MoE layer whose expert module preserves `hidden_size`. Source asserts `num_experts % ep_size == 0`. |
| `deepspeed.moe.utils.split_params_into_different_moe_groups_for_optimizer` | Splits parameter groups into ordinary and MoE-aware groups | Use when passing `model_parameters` to `deepspeed.initialize()` for MoE models, especially with ZeRO stage 2/offload. |
| `MoE.forward` | Returns tuple-like output including model output and auxiliary load-balancing loss | Training code must unpack the output and include `l_aux` in the objective as appropriate. |
| `enable_expert_tensor_parallelism` | MoE constructor flag | Requires compatible model-parallel state/groups. Do not enable by default in ordinary expert-parallel examples. |

MoE `num_experts` is the total experts per layer. `ep_size` is the expert-parallel group size. For PR-MoE, repository docs describe list-valued expert counts with `use_residual=True`; verify current behavior before relying on list-valued `num_experts` because the installed signature annotates `int` and current source enforces divisibility arithmetic.

## Sequence Parallelism

| API | Signature or role | Notes |
| --- | --- | --- |
| `deepspeed.sequence.layer.DistributedAttention` | Wraps a local attention module with Ulysses sequence-parallel all-to-all communication | Legacy Ulysses path used with explicitly created sequence-parallel groups. Attention head count must be divisible by sequence-parallel size. |
| `deepspeed.runtime.sequence_parallel.ulysses_sp.UlyssesSPAttentionHF.register_with_transformers` | Registers Ulysses attention adapters for supported Hugging Face Transformers models and returns an MPU-like object | Must run before `AutoModelForCausalLM.from_pretrained()` when registering by model name. Sequence length must be divisible by SP size when fixed. |
| `UlyssesSPDataLoaderAdapter` | Wraps a dataloader to shard sequence-dimension batches and prepare shifted labels | Required for HF Ulysses examples so each rank sees its sequence shard and loss can be aggregated correctly. |
| `deepspeed.sequence.auto_sp.auto_wrap_model_for_sp` | One-call AutoSP wrapper for supported multimodal sequence-parallel injection | Wraps recognized ViT attention in place, warns and skips HF-style LLM attention, and warns that projection-layer automation is incomplete. |

Sequence parallelism depends on distributed process groups and usually on NCCL/GPU execution. Keep local scripts import-only unless the user explicitly asks to launch distributed tests.

## Activation Checkpointing

| API | Signature or role | Notes |
| --- | --- | --- |
| `deepspeed.checkpointing.configure` | `(mpu_, deepspeed_config=None, partition_activations=None, contiguous_checkpointing=None, num_checkpoints=None, checkpoint_in_cpu=None, synchronize=None, profile=None)` | Configures activation partitioning, contiguous checkpoint buffers, CPU checkpointing, synchronization, and profiling. |
| `deepspeed.checkpointing.checkpoint` | `(function, *args)` | Wraps a function for activation recomputation using the configured DeepSpeed checkpointing behavior. |
| `deepspeed.checkpointing.reset` | Resets checkpointing state | Useful between eval phases or tests that reuse process state. |

When using `PipelineModule`, its `activation_checkpoint_interval`, `activation_checkpoint_func`, and `checkpointable_layers` provide pipeline-local checkpointing controls. Avoid simultaneously configuring overlapping checkpoint policies without a clear memory/performance goal.
