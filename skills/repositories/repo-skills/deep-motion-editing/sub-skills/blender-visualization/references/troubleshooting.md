# Blender troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: bpy` or `mathutils` | The command used ordinary Python, not Blender's interpreter | Locate a supported Blender executable and run the script through it; do not pip-install arbitrary `bpy` wheels as a substitute. |
| Blender reports unknown arguments | Script options were not placed after the extra `--` separator | Use the bundled command builder and inspect the emitted argv. |
| BVH loads with wrong orientation or floor placement | BVH y-up vs Blender z-up conversion, height normalization, or character-specific offsets | Compare source and loaded rest pose, adjust floor/camera/material settings, and preserve a reference render. |
| Eevee/Cycles fails or produces no frames | Engine unavailable, render flag omitted, frame range invalid, or output path unwritable | Run Blender version/help, choose a supported engine, bound `frame_end`, and use a fresh writable output directory. |
| Automatic skinning fails | FBX/BVH skeleton names, scales, rest pose, or mesh topology do not match | Use a copy of the assets, inspect alignment, try manual parenting, and keep temporary files isolated. |
| FBX conversion changes many files unexpectedly | Bulk directory traversal and output naming are implicit in the source helper | Start with a single-file command, back up outputs, and review the command before `--execute`. |
| Blender render is slow or OOM | Cycles quality/resolution/frame count or GPU contention | Use a bounded Eevee smoke render first; lower resolution/frame range and record engine/device settings. |

The current skill was generated without a Blender executable, so these routes
must remain marked unverified until a real Blender runtime is supplied.
