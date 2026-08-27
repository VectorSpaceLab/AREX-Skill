# Inference workflow troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError: model.safetensors.index.json` | `state_path` points at the wrong directory or an incomplete download. | Point `state_path` at the quantized state directory, not the repo root or base model cache. Validate the index before `build_model`. |
| `KeyError` for `w1.W_q` or `model.embed_tokens.weight` | The checkpoint is not the expected HQQ/offloading safetensors layout. | Use a quantized state generated for this repo's Mixtral offloading format. Do not substitute unquantized Mixtral weights. |
| CUDA unavailable or `torch.cuda.is_available()` is false | CPU-only torch wheel, missing GPU passthrough, incompatible driver/runtime, or no NVIDIA GPU. | Run the root environment check with `--require-cuda`; install a CUDA-capable PyTorch build or move to a CUDA host. |
| OOM during `build_model` | Too many experts are kept on GPU or the prompt/generation is too long. | Increase `offload_per_layer`, start with a shorter prompt, reduce `max_new_tokens`, and clear unused CUDA allocations. |
| Slow generation after increasing offload | More experts are swapped between CPU and GPU. | Lower `offload_per_layer` if VRAM allows, or reduce prompt/generation length. |
| HQQ group-size divisibility assertion in a tiny experiment | Fixture shape is incompatible with HQQ scale/zero quantizer group sizes. | Use realistic Mixtral shapes or a tiny shape whose derived scale tensors are divisible by the quantizer group size. |
| `attention_mask` shape errors in multi-turn generation | Cached sequence length was not accounted for when reusing `past_key_values`. | For later turns, include the cached KV length when constructing the attention mask on the CUDA device. |
| Notebook install commands fail in a script | Notebook cells clone, install, and download with Colab assumptions. | Separate environment setup, model download, and generation; do not embed shell `!` commands in production scripts. |
| HQQ reports `hqq_aten package not installed` | Optional HQQ ATEN backend is absent. | The repo's selected path uses HQQ/Triton kernels; do not claim ATEN support unless that optional backend is deliberately installed and verified. |

## Debug order

1. Verify imports and CUDA before model download or model construction.
2. Validate the safetensors index and weight-map keys.
3. Compute offload sizes and check that at least one expert per layer can remain
   on-device if swaps are expected.
4. Start with low `max_new_tokens` and a single prompt.
5. If the failure occurs in HQQ/Triton rather than model assembly, route to the
   quantization-kernels sub-skill.
