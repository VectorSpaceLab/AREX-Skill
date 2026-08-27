---
name: utilities
description: "Use alphafold2_pytorch utilities to validate and transform protein
  coordinates, distograms, masks, MDS reconstructions, sidechain layouts,
  alignments, and structure-quality metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Utilities

Use this route for coordinate and structure-data work around
`alphafold2_pytorch.utils`: distogram-to-distance conversion, masks and padded
node compaction, MDS, SidechainNet-style atom packing, distance losses, LDDT,
Kabsch alignment, GDT, and the package's simplified TM-score.

## Choose the operation

- Read [api-reference.md](references/api-reference.md) for exact signatures,
  layouts, return values, wrapper quirks, and the `37` distance-bucket
  convention.
- Read [structure-data.md](references/structure-data.md) before mixing model
  coordinates with SidechainNet coordinates. It records atom order, masks,
  padding, MDS reflection ambiguity, and metric interpretation limits.
- Read [troubleshooting.md](references/troubleshooting.md) when imports fail,
  shapes or masks do not agree, MDS becomes non-finite, or a metric result
  seems scientifically implausible.

Common routes:

1. For a distogram, provide nonnegative bin masses to
   `center_distogram_torch`, mask diagonal and padded pairs, symmetrize if
   needed, then call `MDScaling`. Use `fix_mirror=False` for a generic point
   cloud; provide flattened N/CA/C masks only for a protein backbone.
2. For atom data, keep the atom order and occupancy mask beside every tensor.
   Use `scn_backbone_mask` for flattened N/CA/C selectors,
   `mat_input_to_masked` for padded graph nodes, and
   `sidechain_container` only when SidechainNet/mp-nerf prerequisites and
   sequence padding semantics are satisfied.
3. For evaluation, use `Kabsch` only on two corresponding `(3, N)` point sets;
   then use `GDT`, `TMscore`, or `RMSD` on matched layouts. Use
   `lddt_ca_torch` only with `(B, L, 14, 3)` SidechainNet-style coordinates and
   `(B, L, 14)` cloud masks. Use `distmat_loss_torch` when alignment should
   not affect the loss.
4. Run the bundled deterministic CPU helper when a small API check is enough:
   `python /path/to/alphafold2/sub-skills/utilities/scripts/utility_smoke.py`.
   Replace `/path/to/alphafold2` with the installed skill directory. It has no
   download, model, training, or CUDA path and reports a clean skip when the
   utility module's import-time scientific dependencies are absent.

## Boundaries and source drift

This route does not build or run the main model, structure module/IPA/recycling
path, or external pretrained embedding models. Route those requests to
`core-model`, `structure-and-recycling`, or `embeddings`.

The README describes model-facing flattened coordinates as `(B, L * atoms,
3)` and displays the model backbone order as C, C-alpha, N (optionally C-beta).
The utility mask `scn_backbone_mask` marks flattened slots as N, CA, C, and
several utility functions use `(B, L, 14, 3)`. Treat these as different
contracts; do not reshape or reorder without an explicit atom map.
