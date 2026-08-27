---
name: kda-and-context-parallel
description: "KDA ops, KimiDeltaAttention/KDAConfig, safe-gate gating, optional
  FlashKDA/TileLang routing, and context-parallel guidance for
  flash-linear-attention."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# KDA and Context Parallel

Use this sub-skill when the task is specifically about Kimi Delta Attention (KDA), KDA layer/model configuration, KDA gate modes, `safe_gate`/`lower_bound`, KDA optional backends, or KDA context-parallel behavior.

## Route here for

- Calling or diagnosing `chunk_kda`, `fused_recurrent_kda`, `KimiDeltaAttention`, `KDAConfig`, `KDAModel`, or `KDAForCausalLM`.
- Choosing between chunk KDA, fused recurrent KDA, KimiDeltaAttention's training/decode modes, and KDA model config fields.
- Handling raw gate inputs versus precomputed log decays, `A_log`, `dt_bias`, `use_qk_l2norm_in_kernel`, `use_gate_in_kernel`, `use_beta_sigmoid_in_kernel`, `allow_neg_eigval`, `safe_gate`, and `lower_bound`.
- Deciding whether a KDA call can use FlashKDA, TileLang KDA backward, Triton-Ascend KDA, distributed `cp_context`, or intra-card context parallel.
- Planning KDA native validation candidates without launching native tests or distributed jobs by default.

## Do not use this sub-skill for

- Generic backend registry mechanics, non-KDA dispatch policy, or broad Triton kernel style; route to the ops/dispatch sub-skill if present.
- Generic benchmark loops, result tables, or autotuning methodology; route to the benchmarking sub-skill if present.
- Non-KDA linear-attention families unless the task is comparing their context-parallel contract with KDA.

## First actions

1. Identify the surface: operator call, KDA layer/model config, optional backend, distributed CP, or intra-card CP.
2. Read the bundled reference that matches the surface:
   - `references/kda-workflows.md` for KDA APIs, gate contracts, layer/model config, backend gates, and native validation candidates.
   - `references/context-parallel.md` for `cp_context`, distributed KDA CP, intra-card CP, prerequisites, and skip rules.
   - `references/troubleshooting.md` for common failures and the fastest diagnosis path.
3. If a quick environment sanity check is useful, run the bundled helper with `--help` first. Use `scripts/smoke_kda.py --require-cuda` only when a CUDA device is intentionally available; it does not launch distributed work.

## Core operating rules

- KDA tensors use q/k heads `H` and value/gate heads `HV`; grouped value attention is valid only when `HV % H == 0`.
- `chunk_kda` is the training-capable high-throughput route and the only KDA operator route that accepts `cp_context`.
- `fused_recurrent_kda` is the recurrent route for decode/small-token inference and does not accept `cp_context`.
- For raw gates, pass `use_gate_in_kernel=True`, `A_log`, optional `dt_bias`, and raw `g`; for precomputed gates, pass `use_gate_in_kernel=False` and ensure `g` is already the log-space decay tensor expected by the operator.
- Prefer the explicit safe-gate contract `use_gate_in_kernel=True`, `safe_gate=True`, `lower_bound=-5.0`; if using precomputed gates with `safe_gate=True`, make the clamp/provenance of `g` explicit because the operator will not apply `lower_bound` in that mode.
- Do not mix `cp_context` with `initial_state` or `output_final_state=True`; `cp_context` owns the rank-local `cu_seqlens` metadata.
- Treat FlashKDA and intra-card CP as inference-only optional accelerators. If their verifier conditions are not all satisfied, expect silent fallback to the default path unless backend dispatch is disabled globally.
