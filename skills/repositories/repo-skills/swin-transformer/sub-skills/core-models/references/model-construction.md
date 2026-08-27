# Model Construction Notes

## When to read

Read this when you need to choose a model family or reduce a config for a CPU smoke test.

## Family map

| Family | `MODEL.TYPE` | Key config block | Notes |
| --- | --- | --- | --- |
| Swin V1 | `swin` | `MODEL.SWIN` | Baseline shifted-window attention backbone |
| Swin V2 | `swinv2` | `MODEL.SWINV2` | Adds continuous relative position bias and `PRETRAINED_WINDOW_SIZES` |
| Swin-MLP | `swin_mlp` | `MODEL.SWIN_MLP` | Replaces attention with windowed spatial MLP layers |
| SimMIM encoder | `swin` or `swinv2` | `MODEL.SWIN` / `MODEL.SWINV2` plus `MODEL.SIMMIM` | Used through `models.simmim.build_simmim` |

## Small CPU smoke patterns

A practical tiny smoke test usually changes only a few fields:

- `DATA.IMG_SIZE`: reduce to 32 or 64.
- `MODEL.*.WINDOW_SIZE`: keep it valid for the reduced image size.
- `MODEL.*.DEPTHS`: reduce to `[1, 1, 1, 1]` or another tiny tuple.
- `MODEL.*.NUM_HEADS`: keep divisibility consistent with embedding dims.
- `MODEL.NUM_CLASSES`: set to a small positive value for classifier smoke checks.

## Derived rules

- If a model family expects `MODEL.SWIN` fields, do not mix in `MODEL.SWINV2` field names.
- `SwinTransformerV2` ignores V1 relative-position assumptions and expects `pretrained_window_sizes` instead.
- If `fused_window_process` is unavailable, the model still runs with the pure-PyTorch path.
- If Tutel is unavailable, Swin-MoE should be treated as an unverified optional workflow, not as a baseline model family.

## When a smoke test is enough

A CPU smoke test is enough to confirm:

- the config dispatches to the correct constructor,
- the model builds without syntax/config errors,
- a forward pass returns a tensor of the expected rank,
- the model's parameter count is finite and non-zero.

It is not enough to confirm GPU kernel performance, long training stability, or pretrained accuracy.
