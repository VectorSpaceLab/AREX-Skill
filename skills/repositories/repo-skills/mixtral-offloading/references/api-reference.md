# Repo API reference

This is a compact map of user-facing source APIs. Import them from `src.*` after
placing the user's checkout root on `PYTHONPATH`.

## `src.build_model`

| Object | Signature / role |
| --- | --- |
| `OffloadConfig` | `OffloadConfig(main_size: int, offload_size: int, buffer_size: int, offload_per_layer: int)`; frozen dataclass passed to `build_model`. |
| `QuantConfig` | `QuantConfig(ffn_config, attn_config)`; stores separate HQQ configs and caches FFN metadata. |
| `QuantConfig.get_ffn_metas` | `get_ffn_metas(hidden_dim: int, ffn_dim: int)` returns metadata for expert `w1/w3` and `w2`. |
| `replace_attn_layers` | Replaces Mixtral attention projections and gates with HQQ/Triton-compatible layers. |
| `make_empty_expert` | Builds an empty quantized Mixtral expert MLP from model and quant configs. |
| `make_and_load_expert_wrapper` | Loads one expert's quantized safetensors state and wraps it in `MixtralExpertWrapper`. |
| `load_00_expert_state_dict` | Loads layer 0 expert 0 state as a template during model construction. |
| `build_model` | `build_model(device, quant_config, offload_config, state_path)` assembles the offloaded Mixtral model. |

Use the inference sub-skill for end-to-end model construction details.

## `src.custom_layers`

| Object | Role |
| --- | --- |
| `HQQLinearTritonSavable` | HQQ linear wrapper whose forward path dispatches to 2/3/4-bit Triton kernels and whose state-dict hooks save/load compact quantized metadata. |
| `MixtralBLockSparseTop2MLP_HQQ` | Quantized Mixtral expert MLP with HQQ/Triton `w1`, `w2`, and `w3`. |
| `SparseMoeWrapper` | Replaces a Mixtral layer's sparse MoE block and loads selected experts through `ExpertCache`. |

Use the quantization and expert-cache sub-skills for deep internals.

## `src.expert_cache`

| Object | Role |
| --- | --- |
| `ExpertInfo` | Stores expert UID, eviction group, offload flag, and slot index. |
| `EvictionGroupInfo` | Tracks LRU main/offloaded experts plus hit/miss counts per group. |
| `ExpertCache` | Manages main-device expert wrappers, pinned offload storages, temporary buffers, registration, and swaps. |

## `src.expert_wrapper`

`MixtralExpertWrapper(expert_module, device)` replaces an expert's tensors with
views into one `torch.UntypedStorage` and registers state-dict hooks for that
storage. It forwards calls to the wrapped expert module.

## `src.packing`

The module patches HQQ `Quantizer.pack/unpack` and provides helpers:

- `pack_4bit_u8_common`, `unpack_4bit_u8_common`, `unpack_4bit_u8_universal`
- `pack_2bit_u8_common`, `unpack_2bit_u8_common`, `unpack_2bit_u8_universal`
- `pack_3bit_i32_common`, `unpack_3bit_i32_common`, `unpack_3bit_i32_universal`
- `patch_packing()`

## `src.triton_kernels`

Public wrappers:

- `triton_matmul4_transpose(groupsize, a, qweight, scales, zeros, bias=None)`
- `triton_matmul2_transpose(groupsize, a, qweight, scales, zeros, bias=None)`
- `triton_matmul3_transpose(groupsize, a, qweight, scales, zeros, N, bias=None)`

They require CUDA tensors and are covered by the quantization-kernels sub-skill.

## `src.utils`

Utilities include nested-structure helpers (`nested_compare`, `nested_flatten`,
`nested_pack`, `nested_map`) and `with_default_dtype(dtype)`.
