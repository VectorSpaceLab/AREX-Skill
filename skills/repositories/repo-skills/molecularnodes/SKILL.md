---
name: molecularnodes
description: "Use MolecularNodes 5.2 in a Blender 5.2 host to import, style,
  animate, annotate, analyze, and render molecular structures, trajectories,
  density maps, and ensembles with verified API and recovery guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MolecularNodes operating skill

Use this skill when a Researcher must plan or execute a MolecularNodes workflow
in Blender: install or diagnose the add-on, load a structure or trajectory,
compose styles and selections, import density/STAR/CellPack data, add
annotations, persist a session, or configure a reproducible scene/render.

## Route by the user's next action

- **Install, import, download, cache, or format diagnosis:**
  [setup-and-import](sub-skills/setup-and-import/SKILL.md)
- **Static molecules, styles, selections, attributes, materials, or Geometry
  Nodes:** [molecules-and-styles](sub-skills/molecules-and-styles/SKILL.md)
- **Trajectory playback, frame mapping, IMD streaming, annotations, or session
  recovery:** [trajectories-and-annotations](sub-skills/trajectories-and-annotations/SKILL.md)
- **EM density, STAR, CellPack, or cryo-EM map/model workflows:**
  [density-and-ensembles](sub-skills/density-and-ensembles/SKILL.md)
- **Canvas, cameras, engines, compositor, snapshots, animation, or render
  recovery:** [scene-and-rendering](sub-skills/scene-and-rendering/SKILL.md)

Read the nearest sub-skill first; its references contain the detailed API
contracts and failure matrices. Cross-cutting failures are in
[references/troubleshooting.md](references/troubleshooting.md). Source version
and evidence are recorded in [references/repo-provenance.md](references/repo-provenance.md);
router placement is in [references/repo-routing-metadata.json](references/repo-routing-metadata.json).

## Installation and minimal verification

For a public Python inspection environment, install the package's declared
Blender API extra with `python -m pip install "molecularnodes[bpy]==5.2.0"`.
For the actual desktop add-on, use Blender 5.2 Preferences → Get Extensions →
Molecular Nodes. Run the bundled read-only checker before importing data:

```bash
python sub-skills/setup-and-import/scripts/check_install.py
```

The checker does not install, fetch, or write files. A headless `bpy` pass is
useful for data/API checks but is not proof of the desktop extension panel,
viewport, or GPU rendering.

## Global operating rules

1. Confirm a Blender 5.2-compatible host (`bpy.app.version`) before claiming
   Blender object, Geometry Nodes, material, annotation, or scene behavior.
   Python parsing can be a preflight but is not a substitute for the host.
2. Prefer small local fixtures and cache-first/offline checks. Treat remote
   downloads, EMDB/PDB services, IMD servers, missing micrographs, and large
   renders as explicit external boundaries.
3. Preserve source paths, world scale, entity type, named attributes, selection
   names, node links, collection ownership, and session state when handing work
   between routes. Reacquire Blender references after scene reset/load.
4. Read back outputs rather than trusting a call return: object/modifier,
   attributes, node links, materials, frames, collections, camera settings,
   render files, or `.MNSession` state as appropriate.
5. Do not promise interactive viewport, desktop extension UI, or GPU rendering
   from a headless `bpy` import. See the nearest troubleshooting reference.
6. Never make runtime instructions depend on the original MolecularNodes
   checkout or private inspection environment.
