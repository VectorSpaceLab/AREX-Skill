# Performance Options

Tune performance after the distributed topology is coherent. Prefer small, reversible YAML changes and run `axolotl preprocess` before expensive training.

## Precision

| Field | Use when | Watch for |
| --- | --- | --- |
| `bf16: auto` or `bf16: true` | Modern Ampere-or-newer NVIDIA GPUs or supported accelerators | Older GPUs may not support BF16 AMP. |
| `fp16: true` | Older CUDA hardware where BF16 is unavailable | May need gradient scaling and can be less stable. |
| `tf32: auto` or `tf32: true` | Ampere+ matrix multiply throughput for fp32 paths | Numeric differences are expected. |
| `fp8: true` | Experimental speed/memory path on supported hardware/software | Requires compatible FP8 packages; Axolotl schema rejects unsupported environments. |
| `fp8_enable_fsdp_float8_all_gather: true` | FSDP2 FP8 all-gather experiments | Often paired with `fsdp_version: 2`; benchmark before assuming speedups. |

Keep norm layers in fp32 with `fp32_norms: true` only under FSDP2 with `fsdp_config` present.

## Attention and Packing

Canonical attention values include `eager`, `sdpa`, `flash_attention_2`, `flash_attention_3`, `flex_attention`, `xformers`, `sage`, `fp8`, and hub-kernel paths containing `/`. Short aliases such as `flash`, `fa2`, and `sdp` are rejected; use canonical names.

Important interactions:

- `sample_packing: true` improves utilization on short examples, but use a varlen-capable attention backend such as `flash_attention_2`, `flex_attention`, `xformers`, or `sage`.
- Legacy boolean flags such as `flash_attention: true`, `xformers_attention: true`, `sdp_attention: true`, `flex_attention: true`, `sage_attention: true`, and `eager_attention: true` are deprecated. Do not combine any of them with `attn_implementation`.
- `context_parallel_size > 1` needs Flash Attention/ring attention support. Set `attn_implementation: flash_attention_2` unless the user has a deliberate supported alternative.
- Flash Attention 2 needs modern GPU support; Flash Attention 3 is Hopper-focused; `xformers` can be useful on older Turing-class GPUs.
- For GRPO or other method-specific sampling/batching constraints, route the objective details to the owning training sub-skill and keep this sub-skill focused on distributed implications.

## Memory Levers

Apply these roughly from least invasive to most specialized:

1. Lower `micro_batch_size`; preserve throughput with `gradient_accumulation_steps` if needed.
2. Shorten `sequence_len` or enable `sample_packing` if the dataset has many short sequences.
3. Use `gradient_checkpointing: true` to trade compute for activation memory.
4. Use `activation_offloading` modes when long-context full-parameter training still OOMs; `hidden_states` is useful for ALST-style long-context work, while `legacy` offloads more synchronously.
5. Use `layer_offloading: true` for LoRA/QLoRA cases where most decoder layer parameters are frozen and CPU transfer overhead is acceptable.
6. Move from DDP/single-process to FSDP2 or DeepSpeed ZeRO, then consider CPU offload variants if GPU memory is still the bottleneck.
7. For long context, use `context_parallel_size` with a compatible attention backend, remembering that effective data-parallel batch count is divided by context-parallel group size.

## Kernel and Integration Flags

Axolotl includes optional integrations that can improve speed or memory but require matching dependencies and hardware:

- Liger kernels: useful for optimized LoRA, norms, RoPE, and fused linear cross entropy paths. Check tensor-parallel limitations for specific Liger flags; for example Liger RMSNorm and fused linear cross entropy have TP caveats in the integration validators.
- Cut Cross Entropy: reduces cross-entropy memory pressure with an optimized loss path. Treat installer helpers as reference-only; do not run mutable installers from this skill.
- `fused_attn_kernel: true`: opt-in fused RMSNorm+RoPE path for supported Qwen-family and related models; route architecture support questions to `model-loading-and-adapters`.
- Expert kernels: MoE grouped GEMM options such as ScatterMoE and SonicMoE can accelerate expert paths, but SonicMoE is not supported with `expert_parallel_size > 1` in Axolotl's kernel integration.
- `deepcompile: true`: DeepSpeed compile experiment; validate with the selected DeepSpeed JSON and benchmark against a non-compiled baseline.

Do not recommend installing optional kernels blindly. Ask the user which hardware, CUDA/ROCm, PyTorch, and Axolotl extras are available, then keep runtime claims conditional unless the user runs verification.

## Optimizers and Schedulers

Optimizer choice can affect distributed memory and communication:

- Standard AdamW-style optimizers are the safest default for distributed troubleshooting.
- Q-GaLore requires FSDP2 with `use_orig_params: true` according to the optimizer docs.
- DION and other communication-reducing optimizers can be attractive at scale but should be introduced after the base FSDP/DeepSpeed job is stable.
- Axolotl custom scheduler paths can be bypassed by DeepSpeed-controlled scheduling; if a scheduler looks ignored under DeepSpeed, check whether DeepSpeed owns the scheduler.

## Profiling and Observability

Static guidance before a real run:

- Use `profiler_steps` and `profiler_steps_start` to capture PyTorch profiler artifacts into `output_dir` for a short window.
- Keep profiler windows short; full-run profiling can distort performance and create large outputs.
- For team dashboards, SwanLab integration can log distributed metadata and profile-related information when configured by the user. Do not embed API keys or secrets in reusable YAML.
- Compare tokens/sec, step time, GPU memory, data-loader wait, and communication stalls between one change at a time.

## Reference-Only Helpers

Do not bundle or run mutable helper installers here:

- `scripts/analyze_profile.py`: reference-only idea for a user-owned profiler analyzer because profiler artifacts are large and environment-specific.
- `scripts/cutcrossentropy_install.py`: reference-only installer concept; future agents should instead ask the user to install the appropriate Axolotl extra or package in their own environment.

The bundled safe script for this sub-skill is [../scripts/check_distributed_config.py](../scripts/check_distributed_config.py), which only reads YAML/JSON and prints warnings/errors.
