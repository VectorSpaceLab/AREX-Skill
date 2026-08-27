# TurboT2AV Acceleration Notes

TurboT2AV borrows TurboDiffusion acceleration ideas but adapts them to the LTX-2 joint audio-video transformer. Do not assume that every core TurboDiffusion Wan flag or kernel has identical behavior in TurboT2AV.

## Cumulative acceleration stages

The public TurboT2AV latency table is cumulative and was measured as generator-only latency on a single NVIDIA H20 at `1024x1792` with 121 frames.

| Stage | Latency | Speedup vs previous | Speedup vs teacher | Interpretation |
| --- | ---: | ---: | ---: | --- |
| LTX-2-19B teacher, 40 steps | 318.7405s | - | 1.00x | Dense teacher baseline. |
| + TileLang W8A8 and FastNorm | 233.3424s | 1.37x | 1.37x | Same teacher with linear/norm acceleration. |
| + four-step TurboT2AV student | 12.1655s | 19.18x | 26.20x | Distilled student with W8A8/FastNorm retained. |
| + SageSLA `topk=0.3` and text trimming | 5.8505s | 2.08x | 54.48x | Final recommended accelerated student path. |

The pure four-step student without these inference optimizations is reported at 16.5245s/video, so the final accelerated student is 2.82x faster than that pure student path.

Important interpretation limits:

- The measurement is H20-specific. Other NVIDIA GPUs may prefer different kernels, top-k ratios, tile choices, or even the dense baseline.
- The table reports generator-only timing, not end-to-end download/setup time and not necessarily decode/audio-video muxing time.
- SageSLA sparsity is an approximation. Revalidate quality when changing resolution, prompt distribution, or model checkpoint.

## Attention choices

The AV inference runner accepts:

```text
--attention_type default|sageattn|sla|sagesla
--attention_scope self|video_self|self_av
--sla_topk FLOAT
--sla_topk_schedule START-END:TOPK,...
--sla_block_q INT
--sla_block_k INT
```

Guidance:

- `default` leaves LTX attention unchanged.
- `sageattn` uses SageAttention for selected unmasked LTX attention modules.
- `sla` uses TurboDiffusion's Sparse Linear Attention adapter for LTX self-attention.
- `sagesla` uses the SageSLA path and is the recommended final TurboT2AV mode.
- `self` targets video/audio self-attention and is the recommended scope for SageSLA.
- SLA/SageSLA support only unmasked self-attention in this integration. Masked text cross-attention remains native.
- `self_av` can target unmasked audio-video cross-attention for compatible backends, but SLA/SageSLA skip unsupported modules.

### `topk=0.3`

`--sla_topk 0.3` is the public speed/quality setting used in the final H20 result. The code accepts values in `(0, 1]`; out-of-range values such as `0`, negative numbers, or values greater than `1` are rejected. The implementation may raise the effective per-layer top-k to at least one key block so extremely small values do not select zero blocks.

Use `--sla_topk_schedule` to vary top-k by transformer layer, for example:

```text
--sla_topk_schedule 0-15:0.35,16-31:0.3,32-47:0.25
```

Unmatched layers use the global `--sla_topk`. Invalid layer ranges or top-k values are rejected.

## FastNorm and text context trimming

`--fast_norm` applies two kinds of replacements:

- module replacements for RMSNorm/LayerNorm using TurboDiffusion fused norm modules; and
- functional patches for LTX-specific RMSNorm, modulation, residual, and rotary helper calls.

The functional kernels have runtime fallbacks for unsupported shapes, dtypes, devices, or errors, but import/build failures still need to be fixed or the flag disabled.

`--trim_text_context` explicitly sets the TurboT2AV text-trimming behavior. It drops padded text tokens before inference and removes the attention mask from the trimmed context. It is disabled by default and should be treated as an optimization that may need revalidation for a new text encoder configuration.

## W8A8 linear choices

The runner accepts:

```text
--quant_linear
--quant_linear_scope all|transformer_blocks|ffn|video_ffn|audio_ffn|video_heavy|non_attention
--quant_linear_backend turbodiffusion|tilelang_postscale
```

Scope meanings:

| Scope | Meaning |
| --- | --- |
| `all` | Replace every eligible loaded `torch.nn.Linear` module. This is the public recommended TurboT2AV student setting. |
| `transformer_blocks` | Replace linears under transformer blocks, excluding the SLA compensation projection. |
| `ffn` | Replace video and audio feed-forward linears. |
| `video_ffn` | Replace only video feed-forward linears. |
| `audio_ffn` | Replace only audio feed-forward linears. |
| `video_heavy` | Replace video feed-forward linears and video self-attention projections. |
| `non_attention` | Replace linears that are not attention projections. |

Backend meanings:

- `turbodiffusion` uses the original TurboDiffusion INT8 linear path and CUDA extension. It mirrors the core repo conceptually but depends on TurboDiffusion acceleration imports and kernels.
- `tilelang_postscale` uses the LTX/H20-tuned TileLang post-scale INT8 GEMM path and is the recommended TurboT2AV public setting.

### Difficult semantic case: TurboDiffusion `quant_linear` vs TurboT2AV TileLang W8A8

Do not tell users that core TurboDiffusion `--quant_linear` and TurboT2AV `--quant_linear --quant_linear_backend tilelang_postscale` are identical.

Correct interpretation:

- Both are W8A8-style inference replacements for Linear modules.
- TurboT2AV keeps a BF16 copy/fallback path because unsupported shapes use native Linear, so the path targets compute speed rather than checkpoint compression.
- The TileLang post-scale backend applies activation and weight scales in the epilogue and keeps INT8 accumulation continuous across the K dimension.
- The TileLang path was selected because the original TurboDiffusion W8A8 kernel did not outperform BF16 Linear on the tested H20 LTX shapes.
- If the user wants the original TurboDiffusion CUDA-kernel semantics, use `--quant_linear_backend turbodiffusion`, but expect different performance and build dependencies.

## Acceleration report

The runner prints a report like:

```text
[TurboT2AV][accel] attention_type=sagesla attention_scope=self replaced_attention=... skipped_attention=... replaced_linear=... fused_attention_projection=... quant_linear_scope=all quant_linear_backend=tilelang_postscale sla_topk=0.3 sla_topk_schedule=none replaced_norm=... replaced_functional_norm=...
```

Use this report to confirm that requested replacements actually happened. A command can include acceleration flags but still replace fewer modules than expected if imports fail, unsupported attention scopes are skipped, or the model structure differs from the public checkpoint.

## Useful environment controls

These environment variables affect advanced acceleration behavior. Use them only when diagnosing or benchmarking; do not set them by default in normal user commands.

| Variable | Effect |
| --- | --- |
| `TURBOT2AV_TRIM_TEXT_CONTEXT=1` | Equivalent to enabling text context trimming; the CLI flag sets it automatically. |
| `TURBOT2AV_TILELANG_W8A8_FUSE_QKV=0` | Disables TileLang QKV/KV fusion when diagnosing fused projection issues. |
| `TURBOT2AV_TD_W8A8_PREALLOC_QUANT=0` | Disables preallocated activation quantization workspaces for the original TurboDiffusion W8A8 backend. |
| `TURBOT2AV_TD_W8A8_SWIZZLE=DIRECTION,LOG_SIZE` | Overrides original TurboDiffusion W8A8 swizzle choice for debugging. |
| `TURBOT2AV_SLA_SKIP_ZERO_LINEAR=0` | Disables SageSLA's zero-compensation-projection shortcut. |
| `AV_EVAL_CACHE_STATE_DICTS=1` | Keeps loaded checkpoint state dicts in CPU RAM during initialization. Higher RAM, sometimes faster repeated initialization. |
| `AV_EVAL_INIT_LOCK_DIR=DIR` | Changes the default model-initialization lock directory for multi-shard runs. |
| `AV_EVAL_NO_INIT_LOCK=1` | Disables the multi-shard model-initialization lock. |

## Recommended presets

For the public fast student path:

```text
--attention_type sagesla \
--attention_scope self \
--sla_topk 0.3 \
--trim_text_context \
--fast_norm \
--quant_linear \
--quant_linear_scope all \
--quant_linear_backend tilelang_postscale
```

For a dense teacher baseline:

```text
--attention_type default
```

For teacher ablations with only W8A8 and FastNorm, enable `--fast_norm --quant_linear --quant_linear_scope all --quant_linear_backend tilelang_postscale` while leaving attention default.
