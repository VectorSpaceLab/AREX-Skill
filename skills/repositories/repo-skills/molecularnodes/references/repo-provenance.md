# MolecularNodes provenance

```yaml
schema: disco.repo-provenance.v1
```

- **Package/repository:** MolecularNodes
- **Source branch:** `main`
- **Source commit:** `041c00bba95861acabebbbf8706a8ec22850a35a`
- **Source dirty state at inspection:** clean
- **Package version:** `5.2.0`
- **Runtime baseline:** Blender/bpy 5.2; Python 3.13
- **Inspection evidence:** `molecularnodes/`, `pyproject.toml`,
  `molecularnodes/blender_manifest.toml`, `README.md`, selected tutorials and
  API pages under `docs/`, selected fixtures under `tests/data/`, and selected
  native candidates under `tests/`.
- **Selected evidence scope:** installation/import; molecule loading and
  styles; selections and attributes; trajectories, IMD, annotations, and
  sessions; density, STAR, CellPack, and cryo-EM workflows; Canvas, cameras,
  compositor, and rendering.
- **Excluded evidence:** CI/release/docs-build internals, broad contributor
  workflows, large/network/credential-bound data, and expensive rendering.

This skill is distilled operating guidance and does not require the source
checkout at runtime. Recheck the source snapshot and installed signatures when
MolecularNodes or Blender versions change. Headless `bpy` compatibility does
not imply interactive UI, viewport redraw, or GPU-render verification.
