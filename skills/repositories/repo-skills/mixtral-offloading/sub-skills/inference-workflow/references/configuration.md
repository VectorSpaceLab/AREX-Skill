# Inference configuration reference

## OffloadConfig

`OffloadConfig` is a frozen dataclass with these fields:

| Field | Meaning |
| --- | --- |
| `main_size` | Number of expert wrapper slots kept on the CUDA/main device. |
| `offload_size` | Number of expert storages held in pinned CPU/offload memory. |
| `buffer_size` | Number of temporary device/offload buffers used during swaps. |
| `offload_per_layer` | Number of experts per transformer layer initially stored off-device. |

The demo computes sizes from the model config:

```python
num_experts = config.num_local_experts
offload_config = OffloadConfig(
    main_size=config.num_hidden_layers * (num_experts - offload_per_layer),
    offload_size=config.num_hidden_layers * offload_per_layer,
    buffer_size=4,
    offload_per_layer=offload_per_layer,
)
```

Increasing `offload_per_layer` lowers GPU VRAM pressure and raises CPU RAM use
and transfer overhead. Decreasing it keeps more experts on GPU and improves
speed at the cost of VRAM. The demo notes that `offload_per_layer=4` is the
normal Colab setting and `offload_per_layer=5` is the starting point for about
12 GB of VRAM.

## QuantConfig

`QuantConfig(ffn_config, attn_config)` stores two HQQ quantization configs:

- `attn_config`: used when replacing attention projections with
  `HQQLinearTritonSavable`.
- `ffn_config`: used for Mixtral expert MLP weights.

The notebook uses:

```python
attn_config = BaseQuantizeConfig(
    nbits=4,
    group_size=64,
    quant_zero=True,
    quant_scale=True,
)
attn_config['scale_quant_params']['group_size'] = 256

ffn_config = BaseQuantizeConfig(
    nbits=2,
    group_size=16,
    quant_zero=True,
    quant_scale=True,
)
quant_config = QuantConfig(ffn_config=ffn_config, attn_config=attn_config)
```

`QuantConfig.get_ffn_metas(hidden_dim, ffn_dim)` is cached and returns metadata
for the `w1/w3` and `w2` expert shapes. If you experiment with smaller test
shapes, HQQ can raise group-size divisibility assertions; use shapes compatible
with the quantizer's group sizes or reduce the scale quantizer group size in the
fixture.

## Choosing values safely

- `0 <= offload_per_layer <= num_experts` must hold.
- `main_size` should not be zero for workflows that need evictable on-device
  experts; otherwise cache swaps may have no candidate to evict.
- `buffer_size` must be positive for overlapped expert movement. The demo uses
  `4`.
- Do not infer `num_hidden_layers` or `num_local_experts` by hand when a matching
  config is available; read them from `AutoConfig` for the quantized state.

Use `scripts/create_offload_config.py` for offline arithmetic and warnings.
