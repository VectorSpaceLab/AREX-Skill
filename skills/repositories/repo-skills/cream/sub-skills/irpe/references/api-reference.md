# iRPE API Reference

## Purpose

Read this when you need the verified iRPE helper signatures and the key model entry points.

## Verified helper signatures

From `iRPE/DeiT-with-iRPE/irpe.py`:

- `get_rpe_config(ratio=1.9, method=3, mode='contextual', shared_head=True, skip=0, rpe_on='k')`
- `build_rpe(config, head_dim, num_heads)`

The repo docs show the more readable call pattern:

```python
rpe_config = get_rpe_config(
    ratio=1.9,
    method="product",
    mode='ctx',
    shared_head=True,
    skip=1,
    rpe_on='k',
)
```

## Verified model entry points

### DeiT-with-iRPE

`rpe_models.py` registers model constructors such as:

- `deit_tiny_patch16_224_ctx_product_50_shared_k`
- `deit_small_patch16_224_ctx_euc_20_shared_k`
- `deit_small_patch16_224_ctx_quant_51_shared_k`
- `deit_small_patch16_224_ctx_cross_56_shared_k`
- `deit_small_patch16_224_ctx_product_50_shared_qk`
- `deit_small_patch16_224_ctx_product_50_shared_qkv`
- `deit_base_patch16_224_ctx_product_50_shared_k`
- `deit_base_patch16_224_ctx_product_50_shared_qkv`

The package also exposes a `hubconf.py` with dependencies `torch`, `torchvision`, and `timm`.

### DETR-with-iRPE

`models/transformer.py` provides the DETR transformer entry path and the `RPE_HELP` string consumed by `--enc_rpe2d`.

## Notes from inspection

- Importing the Python path emits a warning when `rpe_ops` has not been built.
- The Python path remains usable for inspection even without the compiled extension.
- The DeiT and DETR branches use different launcher and config surfaces, so keep them separate in commands.

## What to avoid

Do not confuse the `mode='ctx'` style shown in the docs with the `mode='contextual'` default in the lower-level helper signature.
Use the bundled workflow reference to keep the shorthand consistent.
