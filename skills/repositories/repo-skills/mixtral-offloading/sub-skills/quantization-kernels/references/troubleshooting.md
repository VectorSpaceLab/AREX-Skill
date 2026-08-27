# Quantization and kernel troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `hqq_aten package not installed` warning | Optional HQQ ATEN backend is absent. | For this repo's selected path, document the warning and use Triton-backed checks. Install/verify ATEN only if the user explicitly needs that backend. |
| `AssertionError: group_size should be divisible...` | Tiny HQQ fixture shape is incompatible with scale/zero quantizer group sizes. | Use realistic Mixtral shapes, a larger smoke shape, or adjust fixture quantization group sizes. Do not treat this as an install failure by itself. |
| `nbits ... isn't yet supported` | `HQQLinearTritonSavable.forward_triton` only dispatches 2, 3, or 4 bits. | Use one of the supported bit widths or implement a new Triton wrapper before changing configs. |
| `A must be contiguous` | Input tensor passed to Triton wrapper is strided/non-contiguous. | Call `.contiguous()` on the activation tensor before the wrapper or fix upstream view operations. |
| Scale/zero/qweight shape assertion | Metadata and packed weight shapes do not match. | Compare `meta['shape']`, `meta['group_size']`, `W_q.shape`, `scale.shape`, and `zero.shape`; regenerate metadata for the same linear shape. |
| CUDA unavailable | CPU-only torch, missing GPU passthrough, or incompatible driver/runtime. | Run the root environment helper with `--require-cuda`; do not mark Triton kernel behavior verified on CPU. |
| Triton compile or launch failure | PyTorch/Triton/CUDA version mismatch, unsupported GPU architecture, or invalid tiny shape. | First run the bundled smoke with default shape; then inspect torch version, CUDA version, GPU compute capability, and Triton error details. |
| State-dict load leaves unexpected `meta.*` keys | Save/load hooks and checkpoint key format differ. | Update both `_add_to_state_dict_hook` and `_load_from_state_dict_hook`, and keep supported metadata paths synchronized. |

## Debug sequence

1. Verify dependency imports and CUDA.
2. Run the CPU packing round-trip helper.
3. Run the Triton smoke on a tiny fixture if CUDA is required.
4. Inspect HQQ metadata shape/group fields before loading large checkpoints.
5. Only then retry model-level inference.
