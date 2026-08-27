# Blender loading and rendering

## Runtime and command syntax

The source wrapper targets Blender 2.80-era Python. Ordinary system Python
cannot import `bpy`; use the Blender executable's bundled Python or a supported
configured interpreter. Command-line invocation separates Blender options from
script options with an extra `--`:

```text
blender --background --python SCRIPT.py -- --bvh_path INPUT.bvh --save_path OUT
```

The bundled command builder emits this argv and supports `load`, `render`,
`skin`, and `fbx2bvh` modes. Dry-run is the safe default.

## Rendering options

The scene options expose a BVH path, save/output path, `cycles` or `eevee`
engine, a render flag, last frame index, and resolution (`resX`, `resY`).
Eevee is the faster real-time path; Cycles is slower and supports higher
quality plus optional acceleration. Verify that the requested engine exists in
the installed Blender build before execution.

The source loader swaps BVH's height axis (y) to Blender's height axis (z) and
normalizes height to 10. The floor is at y=0 in the generated scene and may
need adjustment for a new character. End Sites are discarded by the helper
BVH utilities, so inspect the resulting skeleton before judging geometry.

Always write renders to a new directory and bound frame end/resolution for a
smoke render. A command or `--help` check does not prove the render engine or
scene assets work.
