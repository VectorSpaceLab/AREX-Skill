# Troubleshooting

Use the bundled helper first. If a problem only appears in the original repo scripts, treat that as a signal to switch to the safer helper rather than to copy the original behavior.

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| `ImportError: No module named PIL` when trimming | Pillow is missing from the inspection environment | Install Pillow in the private inspection environment, then rerun `trim`. The bundled helper should mention that only the trim command needs Pillow. |
| `ImportError` for `pandas` or `openpyxl` while running the source scripts | The original repo scripts read Excel workbooks with pandas/openpyxl | Prefer the bundled helper. If you intentionally inspect the source scripts, install the missing workbook dependency before retrying. |
| Workbook rows do not match image counts | The repo is not perfectly symmetric: Chinese has the extra `AI Roadmap(AI知识架构).png`, and English uses workbook-backed RoPE sources | Treat the mismatch as expected unless a different file set is being maintained. Re-run inventory to confirm the exact drift. |
| File names with spaces or full-width brackets break shell commands | Unicode and whitespace were not quoted correctly | Use Python paths or quote shell arguments exactly. Do not normalize stems before rename/trim operations. |
| `幻灯片10` maps to the wrong figure | Off-by-one slide numbering or an unexpected blank row in the workbook | Confirm that row 1 is slide 1, not zero. Preview the rename plan before applying it. |
| The original `src/clip_images.py` changes live assets | That script trims into `.tmp` and copies back over the source tree | Do not run it on the live checkout. Use the bundled helper with a separate output tree. |
| The original `src/rename_images.py` overwrites image or workbook files | That script mutates the workbook and images in place | Use the bundled `rename-plan` command first, then apply only on a copied checkout or a deliberate maintenance branch. |
| English workbook rows appear to be missing SVG sources | Two RoPE diagrams are backed by `images_english/source_xlsx/rope.xlsx` and `rope-2.xlsx` instead of SVGs | Check `source_xlsx/` before assuming a source file is missing. |
| Git shows a dirty tree after a maintenance pass | The helper was applied to the live checkout or an output tree was reused | Review the diff, compare against a copied fixture, and rerun on a scratch output root if needed. |
| Crop results look too tight or too loose | Padding is too small or the figure background is not white | Adjust `--padding`. The helper uses the same white-background assumption as the source trim script. |
| A rename target already exists | The preview tree already contains the destination stem | Rerun `rename-plan`, inspect the collision, and only then decide whether `--force` is justified. |

## Minimal recovery sequence

1. Run `inventory`.
2. Reproduce the issue on a copied fixture or copied checkout.
3. Re-run the relevant helper command with `--apply` only on the scratch tree.
4. Compare the output tree to the source tree before touching the live assets.
