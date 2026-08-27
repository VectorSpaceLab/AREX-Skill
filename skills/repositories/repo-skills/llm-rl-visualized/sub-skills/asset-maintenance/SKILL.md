---
name: asset-maintenance
description: "Safely inspect, preview, and maintain the bilingual diagram asset tree."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Asset maintenance

Use this sub-skill when you need to inspect, validate, rename, or trim the repo's bilingual diagram assets without reopening the source checkout or running the original in-place scripts first.

## Start here

1. Read [references/asset-layout.md](references/asset-layout.md) to understand the asset tree, workbook assumptions, generated-versus-source assets, and special cases.
2. Read [references/maintenance-workflows.md](references/maintenance-workflows.md) for dry-run-first rename, name-column, and whitespace-trim flows.
3. Use [scripts/asset_maintenance.py](scripts/asset_maintenance.py) for inventory, rename-plan, add-name-column, and trim operations.
4. If a command fails or a dependency is missing, check [references/troubleshooting.md](references/troubleshooting.md) before touching the live tree.

## Router boundaries

- Concept lookup, diagram-family explanations, roadmap navigation, and model-catalog questions route to `../knowledge-atlas/SKILL.md`.
- Do not use `src/clip_images.py` or `src/rename_images.py` as the first execution path; they are source behavior references and mutate in place.
- Do not bulk rewrite assets unless the user explicitly passes `--apply` to the bundled helper and has chosen a safe output tree or accepted the in-place rename effect.

## Critical operating facts

- `images_chinese/` and `images_english/` each contain `png_big/`, `png_small/`, and `source_svg/`; English also has `source_xlsx/` for selected source workbooks.
- `src/conf/info-ch.xlsx` and `src/conf/info-en.xlsx` are headerless naming maps. Row 1 is slide 1, not zero.
- Chinese `AI Roadmap(AI知识架构).png` is a special asset present in the image tree but absent from the Chinese naming workbook.
- English `source_svg/` is not a 1:1 mirror of `png_big/`; the RoPE diagrams use `source_xlsx/` instead.
- File names may contain Chinese punctuation, spaces, full-width brackets, and other Unicode characters; preserve them exactly.
- The bundled helper defaults to dry-run previews and requires `--apply` before any mutation.

## Safe maintenance pattern

- Inventory first.
- Stage copied fixtures before applying rename or trim operations.
- Validate counts, workbook rows, and stem alignment after every change.
- Prefer output trees or copied workbooks over touching originals when trimming.
- Keep source-script adaptation rationale in the bundled references, not in the live repo files.
