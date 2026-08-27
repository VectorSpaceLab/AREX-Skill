# Quantization API reference

## HQQLinearTritonSavable

`HQQLinearTritonSavable(layer, quant_config, meta=None, **kwargs)` extends HQQ's
linear layer wrapper for the repository's savable Triton-backed path.

Key behavior:

- The quantization config must use `weight_quant_params['nbits']` equal to `2`,
  `3`, or `4`.
- If the base HQQ layer did not create metadata during construction, `meta` is
  required and copied.
- `quantize()` delegates to HQQ and then calls `repack()` so packed weights
  match the stored metadata shape.
- `forward()` calls `forward_triton()`; it does not choose HQQ ATEN.
- `set_backend()` is a no-op in this repository wrapper.
- `dequantize()` exists for compatibility and reconstructs estimated weights
  from packed tensors and quantized scales/zeros.

## Metadata generation

`HQQLinearTritonSavable.get_hqq_meta(linear_shape, quant_config)` constructs a
small HQQ linear layer and removes tensor values from the metadata so the result
can be reused when building empty quantized experts.

For the repository's Mixtral path, metadata is generated for real hidden/FFN
shapes. When making tiny tests, respect HQQ group-size divisibility. For
example, an 8x8 fixture can fail because HQQ's scale quantizer has a larger
default group size than the derived scale tensor. Use a compatible fixture shape
or adjust the fixture's scale/zero quantization settings.

## QuantConfig usage

`QuantConfig(ffn_config, attn_config)` stores separate HQQ configs for expert
MLPs and attention projections. Its cached `get_ffn_metas(hidden_dim, ffn_dim)`
returns two metadata objects:

- `(hidden_dim, ffn_dim)` for `w1` and `w3`.
- `(ffn_dim, hidden_dim)` for `w2`.

The demo attention config uses 4-bit quantization with `group_size=64` and sets
`scale_quant_params.group_size=256`. The expert FFN config uses 2-bit
quantization with `group_size=16`.

## Packing monkey patches

The repository patches HQQ's `Quantizer.pack` and `Quantizer.unpack` maps at
import time:

| Key | Pack helper | Unpack helper | Storage idea |
| --- | --- | --- | --- |
| `4bit_u8` | `pack_4bit_u8_common` | `unpack_4bit_u8_universal` | two 4-bit rows per uint8 row |
| `2bit_u8` | `pack_2bit_u8_common` | `unpack_2bit_u8_universal` | four 2-bit rows per uint8 row |
| `3bit_32` | `pack_3bit_i32_common` | `unpack_3bit_i32_universal` | ten 3-bit rows per int32 row |

The `PackedTensor` marker lets universal unpack helpers distinguish tensors
packed by the repository helpers from HQQ's original packed representation.

## State-dict hooks

`HQQLinearTritonSavable` saves packed `W_q`, optional `bias`, and scale/zero
metadata tensors under stable state-dict keys. On load, it consumes those keys,
reconstructs `meta`, sets `ready=True`, and calls `repack()`.

When debugging a missing-key or unexpected-key error, compare the state dict's
`meta.*` keys with these supported paths:

- `meta.scale_q`, `meta.meta_scale.scale`, `meta.meta_scale.zero`
- `meta.zero_q`, `meta.meta_zero.scale`, `meta.meta_zero.zero`
- `meta.scale`, `meta.zero`

Do not add new metadata tensor paths without updating both save and load hooks.
