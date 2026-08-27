# Cross-cutting troubleshooting

This file covers issues that can affect both sub-skills.

## Concept lookup feels wrong or too thin

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| A query for PPO, DPO, or RoPE returns a weak match. | The user used only one alias or a family boundary is ambiguous. | Search both the acronym and the expanded term. Use the atlas helper and the bilingual alias list in `sub-skills/knowledge-atlas/references/atlas-guide.md`. |
| A comparison mixes adjacent families. | The question spans training signal, runtime role, and update style at once. | Compare by axis: training signal, objective, reference model, update style, and runtime role. |
| The model catalog looks stale. | The catalog is a snapshot-oriented index, not a live mirror of upstream releases. | Treat the catalog as orientation only and verify the current model card or project page when exact freshness matters. |

## Citation and reuse confusion

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| A user wants to reuse a figure online or in a publication. | The repo's license and citation rules differ by medium. | Read `sub-skills/knowledge-atlas/references/citation-and-license.md` and apply the attribution or formal-citation rule that matches the use case. |
| A code snippet is treated as a tested library implementation. | `src/code_from_book.md` is educational orientation, not production code. | Say that the snippet is a conceptual sketch and point to the nearest atlas family instead of promising edge-case safety. |

## Asset maintenance problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `asset_maintenance.py` complains about Pillow or openpyxl. | The inspection environment lacks the required optional packages. | Install only the missing package(s) in the private inspection prefix and rerun the helper. |
| A rename plan shows collisions or no workbook row. | The slide prefix does not map cleanly to the workbook or the target already exists. | Run inventory first, preview the rename plan, and use `--force` only after review. |
| Unicode filenames or Chinese punctuation behave oddly. | The path was normalized or quoted incorrectly. | Preserve the exact workbook text and use UTF-8-safe tooling; do not normalize the figure names. |
| A trim run would overwrite originals. | The helper is being pointed at the live tree without a safe output root. | Trim into a separate output tree or a copied fixture tree first. |

## Staleness and provenance

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| The generated skill no longer matches the current checkout. | The repository changed after skill distillation. | Compare this skill's `references/repo-provenance.md` against the current checkout and refresh if the source commit or dirty state differs materially. |
| A helper script differs from the source scripts. | The bundled helper intentionally adds dry-run safety and root selection. | Use the bundled helper for future work; treat the source scripts only as evidence. |

## Safe defaults to remember

- Use the atlas route for concepts and the asset route for file-tree changes.
- Prefer dry-run and preview modes before any mutation.
- Do not rely on source-checkout paths in runtime guidance.
- The runtime skill tree must remain self-contained.
