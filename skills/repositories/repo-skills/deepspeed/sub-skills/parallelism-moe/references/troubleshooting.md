# Parallelism, MoE, and Checkpointing Troubleshooting

## Pipeline Parallelism

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `PipelineEngine` does not behave like a normal module loop | Pipeline schedules own forward/backward/step ordering | Use `engine.train_batch(data_iter=...)` for training and `engine.eval_batch(...)` for evaluation. Do not call ordinary `engine(batch)`, `backward()`, and `step()` loops. |
| Pipeline hangs or consumes unexpected samples | `data_iter` does not have enough micro-batches for gradient accumulation | Wrap loaders with a repeating loader or ensure each call can supply `gradient_accumulation_steps()` entries per pipeline. |
| Stage boundary errors with masks or labels | Layers pass multiple values without tuple packing | Make each layer accept and return one tensor or one tuple; carry masks/position ids through the tuple until no longer needed. |
| Tied weights are not shared | `TiedLayerSpec` keys or `tied_weight_attr` differ | Reuse the same key and compatible module types; verify tied attributes exist on both endpoints. |
| Partition is unbalanced | Default parameter partitioning does not match compute cost | Try a different partition method, revise layer granularity, or use explicit topology/stage planning. |
| Pipeline plus ZeRO stage 2/3 fails | Pipeline engine is incompatible with ZeRO gradient/parameter partitioning in this code path | Keep pipeline examples on compatible ZeRO settings and route basic ZeRO design to training configuration guidance. |

## MoE and Expert Parallelism

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Assertion says experts must divide expert parallel size | `num_experts % ep_size != 0` | Choose an `ep_size` that divides `num_experts`, or change expert count. Validate before constructing `MoE`. |
| Loss is a tuple or auxiliary loss is ignored | `MoE.forward` returns output plus `l_aux` and metadata | Unpack the MoE return value and add scaled `l_aux` to the task loss. |
| Optimizer or ZeRO treats MoE parameters incorrectly | MoE params were passed as a flat parameter list | Use `split_params_into_different_moe_groups_for_optimizer()` before `deepspeed.initialize()`. |
| PR-MoE example drifts from current source behavior | Docs mention list-valued `num_experts`, while current installed signature/source may expect scalar arithmetic | Inspect the target version and prefer scalar expert counts unless tests prove list support. |
| Expert tensor parallelism fails | Model-parallel groups are absent or incompatible | Initialize the required MPU/groups before enabling `enable_expert_tensor_parallelism`; otherwise leave it disabled. |
| Tutel path is unavailable | Optional Tutel dependency is missing | Keep `use_tutel=False` unless the environment and tests prove Tutel support. |

## Sequence Parallelism

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Attention head split fails | Number of attention heads is not divisible by SP size | Pick a sequence-parallel size that divides the head count. |
| Fixed sequence run fails on shape arithmetic | `seq_length` is not divisible by SP size | Use a compatible sequence length or variable-length registration with per-batch validation. |
| HF model is not patched | Registration happened after `from_pretrained()` | Call `UlyssesSPAttentionHF.register_with_transformers()` before model loading when using model-name registration. |
| Loss differs by SP rank or gradients are wrong | Per-shard losses were averaged naively | Use differentiable all-gather and weight by valid token counts, especially when labels use `-100`. |
| Dataloader labels shift incorrectly | Standard dataloader bypasses the SP adapter | Wrap with `UlyssesSPDataLoaderAdapter` for HF Ulysses training. |
| AutoSP logs warnings or skips modules | Detector found unsupported attention/module shapes | Treat AutoSP as partial; inspect wrapped module count and fall back to explicit integration when needed. |
| Legacy Ulysses conflicts with tensor/pipeline parallelism | Older path has documented compatibility limits | Avoid combining these modes unless repo tests or target framework examples prove the combination. |

## Activation Checkpointing

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Checkpointing config has no effect | `configure()` was not called before checkpoint wrappers or the model uses a different checkpoint path | Configure before model execution and verify whether pipeline interval checkpointing or manual wrappers own the path. |
| Contiguous checkpointing errors | `num_checkpoints` or activation shapes are inconsistent | Provide a correct `num_checkpoints` and use contiguous checkpointing only for compatible fixed-shape activations. |
| Partitioned activation checkpointing fails | MPU object lacks expected model-parallel group methods | Pass a compatible MPU or disable `partition_activations`. |
| Memory improves but throughput collapses | CPU checkpointing or excessive recomputation overhead | Reduce checkpoint scope, disable `checkpoint_in_cpu`, or checkpoint only the largest blocks. |
| Duplicate checkpointing causes confusing memory/perf results | Pipeline interval, global config, and manual wrappers overlap | Pick one primary checkpointing mechanism and document why any additional mechanism is needed. |
