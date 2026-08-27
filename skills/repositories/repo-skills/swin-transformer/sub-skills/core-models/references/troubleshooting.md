# Troubleshooting

## Constructor or shape errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NotImplementedError: Unknown model` | `MODEL.TYPE` is not one of the supported families | Set `MODEL.TYPE` to `swin`, `swinv2`, `swin_mlp`, or route to `simmim`/`swin_moe` as appropriate |
| `assert L == H * W` or window-size assertions | The tiny smoke config made the image resolution or window geometry incompatible | Reduce the config consistently: image size, window size, and stage depths must still match |
| Output shape is not `[batch, num_classes]` | The model is being used as an encoder or the smoke path selected the wrong wrapper | Confirm whether you built a classifier model or a SimMIM encoder wrapper |
| Warning about fused window process | The optional CUDA extension is missing | Ignore for CPU smoke or switch to `moe-and-acceleration` if you want to validate the extension |
| Tutel-related warning | MoE optional dependency is missing | Not a failure for the baseline model families |

## Configuration mistakes

- V1 configs expect `MODEL.SWIN.*` fields.
- V2 configs expect `MODEL.SWINV2.*` fields.
- Swin-MLP configs expect `MODEL.SWIN_MLP.*` fields.
- SimMIM smoke checks should use the SimMIM config family or an explicit SimMIM wrapper.

## Recovery steps

1. Inspect the YAML with `scripts/inspect_swin_config.py`.
2. Reduce the model and image size together rather than shrinking only one of them.
3. Run `scripts/smoke_model_build.py` from a checkout root or with `--repo-root`.
4. If the error mentions checkpoints, move to `data-and-checkpoints` or `simmim-workflows`.
