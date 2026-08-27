# Layer, Module, and Model Troubleshooting

Use this when FLA layer/model construction, Hugging Face integration, generation, training, or evaluation fails.

## Import and registration failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: torch` or `triton` | Bare package install without a backend extra. | Route to `../../setup-and-backends/SKILL.md` and install the backend-specific extra. |
| `from fla import GLAConfig` fails | Top-level `fla` omits Config exports by design. | Import configs from `fla.models`: `from fla.models import GLAConfig`. |
| `AutoModelForCausalLM.from_config(config)` does not find the class | FLA model package was not imported before using auto classes. | Import the relevant config from `fla.models` or import `fla` before constructing the auto model. |
| Hybrid attention construction requires FlashAttention | The config's `attn` field selected standard `Attention`, which depends on optional attention backend packages. | Install the optional dependency or remove/disable hybrid attention for the smoke check. |

## Layer forward failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Shape assertion on hidden states | Layer expects `[batch, sequence, hidden_size]`; projection dimensions must align with heads and expansion. | Check `hidden_size`, `num_heads`, `num_kv_heads`, `expand_k`, `expand_v`, and `head_dim` compatibility. |
| Cache update error | `past_key_values` used without a valid `layer_idx`, or mode/cache pair is unsupported. | Pass `layer_idx` when using cache state and simplify to no-cache for smoke checks. |
| Short convolution dependency error | `use_short_conv=True` may need the optional `causal-conv1d` backend or a supported fallback. | Disable short convolution for construction checks or install the optional conv dependency. |
| CUDA/Triton compile error | Backend wheel mismatch or unsupported device/backend for the fused path. | Verify install/backend with the setup checker, then try a smaller no-fused config to isolate model logic. |

## Config and fused-loss failures

- `fuse_cross_entropy=True` and `fuse_linear_cross_entropy=True` should not be enabled together; use one loss route.
- Fused linear cross entropy is memory-efficient but can reduce numerical precision. If training loss diverges, disable `fuse_linear_cross_entropy` and compare against a non-fused loss.
- `attn` hybrid configs require valid layer indices, positive head counts, positive finite `rope_theta`, and non-overlapping layer sets across a list of specs.
- Tiny CPU construction checks should disable `fuse_norm`, `fuse_swiglu`, and fused CE when the purpose is only config registration or class wiring.

## Generation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Tokenizer/model load tries network | `from_pretrained` was given a remote id and files are not cached. | Ask for network/cache approval or use a local path. |
| OOM during generation | Model/checkpoint too large, context too long, or cache enabled on insufficient VRAM. | Reduce `max_new_tokens`, batch size, context length, dtype, or choose a smaller checkpoint. |
| Unsupported cache or generation strategy error | Some FLA models support fewer cache-manipulating generation paths than standard Transformers. | Retry with a simpler greedy/sample generation path before editing model internals. |
| Unexpected slow generation | Fused/recurrent path not selected, optional backend unavailable, or benchmark mode differs from real generation. | Check model config mode/cache, backend env vars, and route performance analysis to benchmarking. |

## Training and evaluation failures

- Training with Flame/torchtitan, dataset streaming, W&B logging, and checkpoint conversion are side-effect-heavy. Confirm GPU count, data paths, logging permissions, and wall-clock budget first.
- LM evaluation harness and perplexity workflows can download datasets and model weights. Use local paths or explicit network approval.
- Long-context evaluation needs careful `max_length`, block size, bucket size, dtype, and GPU memory planning.
- If a harness cannot find tasks, initialize the task manager in the harness environment before calling evaluation APIs.

## Safe local smoke path

From this sub-skill directory:

```bash
python scripts/smoke_layer_model.py --help
python scripts/smoke_layer_model.py --device cpu
python scripts/smoke_layer_model.py --device cuda --require-cuda
```

The CPU route verifies imports and tiny config/model construction. The CUDA route also runs a tiny `GatedLinearAttention` forward and should be used only when CUDA is expected.
