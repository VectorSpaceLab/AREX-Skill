---
name: blender-visualization
description: "Guides Deep Motion Editing Blender BVH loading, Eevee/Cycles
  rendering, FBX skinning, and FBX-to-BVH conversion with safe command
  construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Blender visualization

Use this route when a BVH must be loaded, rendered, skinned with an FBX mesh,
or converted through Blender. Blender is a separate runtime: `bpy` and
`mathutils` are not available in ordinary Python. This host did not expose a
Blender executable, so Blender-native execution remains explicitly unverified.

## Route by goal

- **Load or inspect a BVH in Blender**: read
  [`references/loading-and-rendering.md`](references/loading-and-rendering.md).
- **Render Eevee/Cycles output**: use
  [`scripts/build_blender_command.py`](scripts/build_blender_command.py) with
  dry-run first, then read the rendering caveats. For a bounded FBX→BVH
  conversion, the builder uses the skill-owned Blender adapter
  [`scripts/fbx_to_bvh.py`](scripts/fbx_to_bvh.py), not the source helper's
  bulk directory traversal.
- **Skin or convert FBX/BVH**: read
  [`references/conversion-and-skinning.md`](references/conversion-and-skinning.md)
  and validate both external asset paths before execution.
- **Generate the motion first**: route to
  [`motion-retargeting`](../motion-retargeting/SKILL.md) or
  [`motion-style-transfer`](../motion-style-transfer/SKILL.md).

## Guardrails

1. Use a Blender 2.80-compatible runtime when following the original scene
   scripts; confirm the actual Blender version before relying on `bpy` APIs.
2. Put Blender arguments after the extra `--` separator. Use
   `--background --python SCRIPT --` for command-line execution.
3. Remember that BVH height is y-axis while Blender uses z-axis in the source
   loader, and the loader normalizes height; floor/camera alignment may need
   manual correction.
4. Dry-run the bundled command builder first. It never installs Blender,
   downloads FBX assets, or overwrites outputs unless `--execute` is explicit.
   `load` and `skin` are interactive scene operations; `render` and
   `fbx2bvh` use background mode and require explicit output paths.

Read [`references/troubleshooting.md`](references/troubleshooting.md) for
missing `bpy`, argument separator, renderer, coordinate, and asset failures.
