# Performance and profiling operations

Use this reference when a user has a working verl run and needs post-training diagnostics, profiling, or performance tuning. Do not use it to assemble a full training command from scratch.

## Triage order

1. Clarify the symptom: OOM, slow rollout generation, slow actor/critic update, slow checkpoint save/merge, or noisy throughput.
2. Identify backend and roles involved: FSDP/Megatron training, vLLM/SGLang/TGI rollout, actor/ref/critic/reward profiling targets.
3. Prefer one narrow profiling window (`global_profiler.steps: [N]`) before enabling broad all-rank profiling.
4. Avoid profiling every rank unless diagnosing distributed imbalance; start with rank 0 or the smallest rank set that reproduces the issue.
5. Keep profiling outputs out of checkpoint/export directories.

## PyTorch profiler

Global controls:

```yaml
global_profiler:
  steps: [1, 2, 5]
  save_path: ./outputs/profile
```

Role-level controls:

```yaml
actor_rollout_ref:
  actor:
    profiler:
      enable: True
      all_ranks: False
      ranks: [0]
      tool_config:
        torch:
          discrete: True
          contents: [cpu, cuda]
```

Useful `tool_config.torch.contents` values:

- `cpu`: CPU activities.
- `cuda`: CUDA activities.
- `memory`: tensor allocation/free tracking; useful for OOM analysis but can add overhead.
- `shapes`: operator input shapes.
- `stack`: source stack traces; useful for deep attribution but expensive.

Rollout token-window profiling:

```yaml
actor_rollout_ref:
  rollout:
    profiler:
      enable: True
      all_ranks: False
      ranks: [0]
      tool_config:
        torch:
          discrete: True
          profile_token_start: 12
          profile_token_end: 46
```

For Agent Loop rollout, discrete mode is mandatory. Rollout ranks refer to inference replica rank, not global training rank. vLLM and SGLang inference engines can trigger collection from the inference side; SGLang does not support the memory option in profiling contents.

PyTorch traces are usually JSON or JSON.GZ files under `global_profiler.save_path`. Use Chrome tracing, Perfetto, or the TensorBoard profiler plugin for visualization.

## Nsight Systems profiler

Nsight Systems captures CUDA kernels, memory operations, CPU/GPU synchronization, and NVTX markers. Use it when PyTorch traces are insufficient for GPU timeline or distributed scheduling analysis.

Global controls include:

- `global_profiler.steps`: profiled training steps; `null` disables profiling.
- `global_profiler.profile_continuous_steps`: combines continuous steps into fewer databases when compatible with non-discrete profiling.
- `global_profiler.global_tool_config.nsys.controller_nsight_options`: Nsight options for the controller process.
- `global_profiler.global_tool_config.nsys.worker_nsight_options`: Nsight options for worker processes. Keep `capture-range: cudaProfilerApi` unless there is a deliberate reason to change capture behavior.

Role controls include:

- `profiler.enable`: enable/disable role profiling.
- `profiler.all_ranks` and `profiler.ranks`: rank selection.
- `discrete`: if false, role actions in one training step are dumped in one database; if true, each annotated action gets a discrete report.

In collocated-worker mode, ensure combined workers have consistent discrete behavior. By default, Ray writes Nsight report files under its session logs on each node; centralizing many reports can overload network storage.

Minimal Nsight pattern:

```yaml
global_profiler:
  steps: [1]
  profile_continuous_steps: False
actor_rollout_ref:
  actor:
    profiler:
      enable: True
      all_ranks: False
      ranks: [0]
```

## Performance tuning knobs

Rollout generation:

- Enable rollout stats first, for example by setting `actor_rollout_ref.rollout.disable_log_stats=False`.
- Tune `gpu_memory_utilization`; values around 0.5 to 0.7 are often a safer starting point when training states remain on GPU.
- Increase `max_num_seqs` or `max_num_batched_tokens` when GPU cache utilization is low. `max_num_batched_tokens > 2048` is a common throughput-oriented starting point.
- Reduce rollout tensor parallel size when memory allows more replicas; data parallel replicas can improve throughput but consume more KV cache.
- Use `cudagraph_capture_sizes` only with `enforce_eager=False`; smaller capture sizes can reduce OOM risk at some throughput cost.

Training forward/backward:

- Prefer `*micro_batch_size_per_gpu` over deprecated global-ish `*micro_batch_size` settings.
- Increase actor/critic PPO micro-batches until they reach normalized mini-batch size or hit memory limits.
- Let forward-only micro-batches/token limits be larger than backward-bearing actor/critic PPO limits when memory allows.
- Enable gradient checkpointing (`actor_rollout_ref.model.enable_gradient_checkpointing=True`, same idea for critic) for larger effective batches.
- Enable activation offload for FSDP actor/critic when GPU memory is the blocker.

Dynamic batch size:

- Set `use_dynamic_bsz=True` for actor/ref/critic/reward model paths that support it.
- Tune token limits such as `actor_rollout_ref.actor.ppo_max_token_len_per_gpu`, `critic.ppo_max_token_len_per_gpu`, and log-prob max-token settings.
- Start actor PPO token limits at least around `2 * (max_prompt_length + max_response_length)` when memory permits.

Long context and FSDP:

- Use Ulysses sequence parallel by setting `ulysses_sequence_parallel_size > 1` for long sequence workloads.
- For FSDP, `fsdp_config.forward_prefetch=True` can overlap next forward-pass all-gather with current computation.
- Backward prefetch is intentionally not recommended in verl docs because it can prefetch incorrectly in nested-module cases.
- FSDP2 can reduce memory and improve throughput for transformer models in supported PyTorch environments.

Entropy/logits memory:

- Enable `actor_rollout_ref.ref.entropy_from_logits_with_chunking=True` to chunk entropy calculations from large logits.
- Enable `actor_rollout_ref.actor.entropy_checkpointing=True` to recompute entropy-specific intermediates during actor training.

## Low precision and quantization touchpoints

FP8 rollout and end-to-end FP8 are performance features, not checkpoint-layout fixes:

- Rollout FP8 can be enabled through rollout quantization settings where supported.
- End-to-end FP8 uses Transformer Engine for forward/backward, FP8 optimizer states, and FP8 rollout inference.
- Blockwise FP8 recipes and engine support vary; verify accuracy and backend support before applying to production.

NVFP4 QAT has separate configuration paths for FSDP and Megatron-style setups. Treat these as training/quantization decisions that can change checkpoint semantics and downstream export compatibility.

## Profiling hygiene

- Capture as few steps/ranks as needed; profiling can change timing and memory behavior.
- Store profiles under a dedicated output directory, not under `global_step_*` role directories.
- Pair profiler changes with a clear rollback patch or config override.
- Record exact step numbers and rank meanings in handoff notes.
- For checkpoint-save slowness, profile around the save step and separately inspect checkpoint contents; large optimizer/extra saves can dominate wall time.
