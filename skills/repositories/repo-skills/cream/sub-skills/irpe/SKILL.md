---
name: irpe
description: "Routes iRPE relative-position-encoding integration for DeiT and
  DETR workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# iRPE

Use this sub-skill when the user wants to equip a model with iRPE or work with the bundled DeiT-with-iRPE / DETR-with-iRPE implementations.

## What this route owns

- iRPE configuration generation and `build_rpe` wiring.
- DeiT-with-iRPE classification workflows.
- DETR-with-iRPE detection workflows.
- Optional custom-op build guidance for the `rpe_ops` extension.

## When to use it

Choose this route for prompts like:

- "add iRPE to DeiT"
- "run DETR with iRPE"
- "build the RPE config"
- "fix the relative-position encoding settings"
- "check whether the custom RPE ops are available"

## What to read next

- `references/api-reference.md` for the verified `get_rpe_config`, `build_rpe`, and transformer entry points.
- `references/workflows.md` for the integration steps and launcher shapes.
- `references/troubleshooting.md` for `rpe_ops`, shape, and dataset issues.
- `scripts/build_irpe_config.py` to print a ready-to-copy Python snippet for the RPE config.
- `scripts/build_irpe_command.py` to print safe command templates.
- `../../scripts/check_custom_ops.py` to report whether the optional compiled extension is present.

## Important boundaries

- Do not route MiniViT here just because it uses iRPE internally; MiniViT has its own route.
- Keep the custom-op guidance optional. The Python path is enough for inspection even when `rpe_ops` is absent.
- Do not depend on the original checkout for runtime instructions; the generated skill must stand on its own.

## Working pattern

1. Identify whether the target is DeiT or DETR.
2. Read the API reference for the model and transformer entry points.
3. Use the config builder to generate the `get_rpe_config` snippet.
4. Use the command builder to print the launcher template and then adapt it to the user's environment.

## Common signals

- `get_rpe_config` and `build_rpe` are the core integration helpers.
- `--enc_rpe2d` is the DETR flag that carries the encoding choice.
- `rpe_ops` missing is a warning for speed, not a complete failure of the Python path.
