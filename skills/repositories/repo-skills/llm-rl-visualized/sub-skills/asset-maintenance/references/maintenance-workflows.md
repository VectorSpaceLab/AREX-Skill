# Maintenance workflows

These workflows are intentionally dry-run-first. Use the bundled helper on a copied checkout or copied fixture tree before mutating anything in place.

## 1) Inspect before changing

Run inventory first to learn how many files, workbooks, and special cases are present.

```bash
python scripts/asset_maintenance.py --root <repo-root> inventory
```

Use `--language chinese`, `--language english`, or `--language all` to narrow the report.

What to check:

- `png_big` vs `png_small` stem counts.
- `png_big` vs `source_svg` stem counts.
- Workbook row counts versus image counts.
- Special exceptions such as `AI Roadmap(AI知识架构).png` and the English RoPE workbook-backed diagrams.

## 2) Preview renames for new `幻灯片N` exports

Use the bundled rename planner to preview the exact target names before any mutation.

```bash
python scripts/asset_maintenance.py --root <repo-root> rename-plan --language chinese
```

Typical use cases:

- A fork contains newly exported `幻灯片N.png` or `幻灯片N.svg` files.
- You want to confirm the slide index maps to the workbook row you expect.
- You need to detect collisions before a rename is applied.

Rules:

- The mapping is 1-based: `幻灯片1` maps to the first workbook row.
- The helper should keep the workbook text exactly as written, including spaces and Unicode punctuation.
- If a target file already exists, treat that as a collision and review it before applying.

To apply after review, add `--apply`. If you need to replace an existing target on purpose, add `--force` only after a preview.

```bash
python scripts/asset_maintenance.py --root <repo-root> rename-plan --language chinese --apply
```

## 3) Add or refresh the workbook name column

Use this when the third workbook column needs to be re-derived from the first two columns.

```bash
python scripts/asset_maintenance.py --root <repo-root> add-name-column --language english
```

Recommended safe pattern:

1. Run a preview on the source workbook.
2. Write to a copied workbook tree with `--apply --output-dir <copy-root>`.
3. Compare the original and copied workbook before replacing anything.

Example:

```bash
python scripts/asset_maintenance.py --root <repo-root> add-name-column --language english --apply --output-dir <copy-root>
```

If `--output-dir` is omitted, `--apply` writes in place. Prefer a copied workbook when you do not intend to touch the live tree.

## 4) Trim whitespace without overwriting originals

Always trim into a separate output tree.

```bash
python scripts/asset_maintenance.py --root <repo-root> trim --language english --output-dir <trimmed-root>
```

Recommended pattern:

1. Copy the relevant image tree to a scratch location.
2. Run `trim` against the copied tree or use the default repo-relative tree with a separate output root.
3. Inspect the trimmed output before any replacement decision.
4. Replace the live tree only after manual approval.

Useful options:

- `--padding` to control how much border is kept around cropped content.
- `--apply` to actually write output files.
- `--force` only if you intentionally want to replace existing files in the output tree.

## 5) Validate counts and links after mutation

After any rename or trim pass, re-run inventory and compare the resulting stem sets.

```bash
python scripts/asset_maintenance.py --root <repo-root> inventory
```

Checks worth repeating:

- `png_big` and `png_small` still match per language, aside from deliberate exceptions.
- `source_svg` still matches the high-resolution render tree where expected.
- The workbook row count still matches the slide-export count for the language.
- The README image paths still point at the renamed stems.

## 6) Copy fixtures before mutation

When the task is risky, operate on a copied fixture tree instead of the live checkout.

```bash
cp -R <repo-root>/images_english <scratch-root>/images_english
python scripts/asset_maintenance.py --root <scratch-root> trim --input-dir <scratch-root>/images_english --output-dir <scratch-root>/trimmed --apply
```

This pattern keeps the original files intact while you validate the helper's output.

## Adaptation rationale

The bundled helper preserves the source scripts' core intent:

- `src/rename_images.py`: numeric slide prefix to workbook-derived stem.
- `src/clip_images.py`: white-background trimming with padding.

The helper adds the safety layer the source scripts lack: root selection, dry-run previews, collision checks, and separate output trees.
