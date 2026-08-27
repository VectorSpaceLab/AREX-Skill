---
name: prompt-gallery
description: "Choose and adapt GPT Image 2 prompt patterns from the curated
  gallery and prompt-craft guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Prompt Gallery

Use this sub-skill when the user needs help choosing, adapting, or composing GPT Image 2 prompts from the gallery patterns: research figures, diagrams, UI mockups, posters, typography, photography, game/anime styles, product imagery, reference-image edits, or hybrid visual directions.

Do **not** run the image API, inspect credentials, or build final shell commands here. For actual `gpt-image` CLI/API execution and preflight, route to `../cli-and-api/SKILL.md`. Do **not** add, remove, or update gallery/repository files here; route repository maintenance to `../repo-maintenance/SKILL.md`.

## Gallery-first operating loop

1. **Classify the user request.** Identify the deliverable type, output surface, required text, subject/domain, style family, and whether it is a generation or edit.
2. **Select categories before writing.** Use `references/gallery-catalog.md` or `scripts/select_gallery_categories.py` to choose one primary category. Load guidance from 2-3 categories only when the user explicitly asks for a hybrid result.
3. **Extract a pattern, not a prompt dump.** Reuse the category's structure: canvas, layout grammar, visible entities, exact labels, style bounds, material/light/palette controls, and avoid-lines.
4. **Apply craft checklists.** Use `references/prompt-craft.md` for exact text, diagrams, UI specs, multi-panel boards, research figures, edits, and size/quality choices.
5. **Return a generation-ready prompt plus routing note.** Provide the final prompt and any parameter suggestions. If the user wants execution, hand off to `../cli-and-api/SKILL.md`.
6. **Preserve provenance discipline.** If adapting an outside-source or community pattern into a public gallery entry, preserve `Author + Source`. Use `Curated` only for repo-created, repo-curated, or substantially reworked material.

## Required user-facing output

For normal prompt-help requests, return:

- selected primary category and optional hybrid categories;
- short rationale for the category choice;
- a polished prompt or structured prompt skeleton;
- exact text block list when typography/labels matter;
- suggested canvas/size family and quality intent;
- API/CLI handoff note without executing anything.

## Quick routing

- Research paper figure, method diagram, data chart, scientific/technical diagram -> `Research Paper Figures`, `Data Visualization`, `Scientific & Educational`, or `Technical Illustration`.
- UI/app/dashboard/product mockup -> `UI/UX Mockups`; combine with `Brand Systems & Identity` if the design system itself is part of the deliverable.
- Posters, covers, dense typography, Chinese copy, event flyers -> `Typography & Posters`, `Infographics & Field Guides`, or `Events & Experience`.
- Product hero image, packaging, beverage/food campaign -> `Product & Food`; combine with `Photography` or `Brand Systems & Identity` when needed.
- Anime/manga/game stills/HUD/worldbuilding -> `Anime & Manga`, `Gaming`, `Character Design`, `Pixel Art`, `Isometric`, `Retro & Cyberpunk`, or `Cinematic & Animation`.
- Reference-image transformations, inpainting, or multi-reference composition -> `Edit Endpoint Showcase` for prompt shape, then route execution to `../cli-and-api/SKILL.md`.

## References

- `references/gallery-catalog.md` — distilled category map, loading policy, and hybrid-selection signals.
- `references/prompt-craft.md` — compact prompt recipes and checklists.
- `references/troubleshooting.md` — failure diagnosis and prompt repair patterns.
- `scripts/select_gallery_categories.py` — safe no-network category selector for task phrases.
