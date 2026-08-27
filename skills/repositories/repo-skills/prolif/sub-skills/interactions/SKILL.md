---
name: interactions
description: "Choose, parameterize, customize, and troubleshoot ProLIF interaction classes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProLIF Interactions

Use this sub-skill when an agent must choose interaction classes, tune interaction parameters, inspect direct residue-level matches, use implicit-hydrogen hydrogen bonds, or configure bridged interactions such as `WaterBridge`.

## Route First

- For molecule conversion, residue labels, water selections, or hydrogen preparation, use `../molecules-and-io/` first.
- For running trajectories, docking poses, single-pair generation, DataFrame export, bitvectors, countvectors, or pickle I/O, use `../fingerprints/` after the interaction setup is chosen.
- For ligand networks, barcode plots, 3D views, or residue display, use `../visualization/` after a fingerprint exists.

## Start Here

1. Discover supported names with `scripts/list_interactions.py`; add `--include-bridged` when `WaterBridge` is relevant.
2. Choose interaction names for `prolif.Fingerprint(interactions=...)`; default interactions are documented in `references/interaction-catalog.md`.
3. Pass constructor overrides through `parameters={"InteractionName": {...}}`; keep keys case-sensitive and matching the class name.
4. Use `count=True` when every matching atom combination matters; otherwise ProLIF stores only the first match per residue pair and interaction.
5. Use `implicit_hydrogens=True` or explicit `ImplicitHBAcceptor`/`ImplicitHBDonor` names for heavy-atom-only hydrogen-bond workflows.
6. Use `parameters={"WaterBridge": {"water": water_selection_or_molecule, ...}}` whenever `WaterBridge` is included.

## Reference Map

- `references/api-reference.md`: constructor signatures, metadata structure, direct methods, `ignore`, and bridge APIs.
- `references/interaction-catalog.md`: available names, defaults, geometric/SMARTS parameter names, and interaction roles.
- `references/workflows.md`: practical setup patterns for parameter tuning, implicit hydrogen bonds, water bridges, direct residue checks, counts, and custom interactions.
- `references/troubleshooting.md`: recovery steps for unknown names, implicit/explicit hydrogen mismatches, water bridge errors, VdW radii failures, missing metadata, overbroad searches, and count confusion.
