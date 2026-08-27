# MolecularNodes cross-cutting troubleshooting

Use the nearest sub-skill matrix first, then classify the failure as one of these
boundaries:

- **Host/dependency:** MolecularNodes 5.2.0 targets Blender 5.2/Python 3.13;
  check `bpy`, `databpy`, `nodebpy`, Biotite, and MDAnalysis together.
- **Input/data:** validate local files, suffixes, schema, atom counts, source
  paths, dimensions, and referenced micrographs before invoking Blender.
- **Assets/context:** missing node groups/materials, unregistered operators,
  stale scene references, or UI-only operators require a registered Blender
  context and asset installation.
- **API misuse:** use the exact installed signatures and route STAR/CellPack,
  trajectories, density, and static structures to their distinct loaders.
- **External boundary:** network services, IMD endpoints, EMDB/PDB accessions,
  GPU devices, interactive viewport redraw, and expensive rendering are not
  silently substituted or retried forever.

## Minimal evidence loop

1. Preserve the original input, path, error, and scene state.
2. Reproduce with a small local fixture or cached file when possible.
3. Check the host version and package imports.
4. Inspect the returned entity/object, modifier, attributes, node links,
   materials, collection ownership, and output paths.
5. Apply the narrowest recovery and rerun one bounded check.
6. Report unresolved host or external limits explicitly.

Do not leak a local checkout, virtual-environment prefix, activation command, or
machine-specific path into a reusable workflow. For route-specific recovery,
read:

- [setup-and-import](../sub-skills/setup-and-import/references/troubleshooting.md)
- [molecules-and-styles](../sub-skills/molecules-and-styles/references/troubleshooting.md)
- [trajectories-and-annotations](../sub-skills/trajectories-and-annotations/references/troubleshooting.md)
- [density-and-ensembles](../sub-skills/density-and-ensembles/references/troubleshooting.md)
- [scene-and-rendering](../sub-skills/scene-and-rendering/references/rendering-troubleshooting.md)
