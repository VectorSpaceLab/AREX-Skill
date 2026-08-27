---
name: "llm-rl-visualized"
description: "Route bilingual concept lookup, diagram-family navigation,
  citation-aware summaries, and safe asset-maintenance tasks for the
  LLM-RL-Visualized atlas."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# llm-rl-visualized

Use this skill when the user asks about the repository as a bilingual visual atlas of large-model and reinforcement-learning concepts, or when they want to safely inspect and maintain the repository's diagram assets.

## Start here
- Read [references/repo-overview.md](references/repo-overview.md) for the repository shape, language split, and the two main routes.
- Read [references/repo-provenance.md](references/repo-provenance.md) if you need to judge whether the atlas is stale relative to the source checkout.
- Read [references/repo-routing-metadata.json](references/repo-routing-metadata.json) if you are curating or refreshing router placement rather than answering an end-user concept question.
- Read [references/troubleshooting.md](references/troubleshooting.md) when concept routing feels thin, a helper script errors, or an asset/workbook operation needs a safe recovery path.
- Use [scripts/smoke_check.py](scripts/smoke_check.py) to confirm the bundled runtime skill tree is intact.

## Route map

### `knowledge-atlas`
Use this route for concept navigation inside the atlas.

Typical prompts:
- Explain PPO, GRPO, DPO, RLHF, or RLAIF.
- Find the right diagram family for LoRA, Prefix-Tuning, RoPE, RAG, CoT, MCTS, DQN, reward models, or benchmarks.
- Compare LLM basics, SFT, policy optimization, RL basics, and reasoning families.
- Look up a model-catalog row or ask which papers, code links, or config links are summarized.
- Ask for citation, reuse, or license guidance.

Read next:
- `sub-skills/knowledge-atlas/SKILL.md`
- `sub-skills/knowledge-atlas/references/atlas-guide.md`
- `sub-skills/knowledge-atlas/references/model-catalog-guide.md`
- `sub-skills/knowledge-atlas/references/book-code-snippets.md`

### `asset-maintenance`
Use this route for safe maintenance of the bilingual diagram assets and workbook-driven filenames.

Typical prompts:
- Preview slide-to-file renames.
- Refresh the generated name column in the workbook.
- Trim whitespace from PNG diagrams.
- Inspect `images_chinese/`, `images_english/`, `src/assets/`, and `src/conf/*.xlsx`.
- Validate counts, collisions, and Unicode filename assumptions.

Read next:
- `sub-skills/asset-maintenance/SKILL.md`
- `sub-skills/asset-maintenance/references/asset-layout.md`
- `sub-skills/asset-maintenance/references/maintenance-workflows.md`
- `sub-skills/asset-maintenance/references/troubleshooting.md`

## Cross-cutting rules
- The repository is an educational visual atlas, not an installable ML package.
- Do not tell the user to reopen the original checkout for runtime guidance; use the bundled references and scripts instead.
- Do not run destructive asset mutations unless the user explicitly chooses an apply mode in the asset-maintenance route.
- Treat the book-style code snippets as educational orientation, not as a tested production library.
- Prefer the atlas route for concepts and the asset route for file-tree operations; do not mix them unless the user explicitly asks for both.

## Safe helper checks
- `scripts/smoke_check.py` validates the runtime skill tree, bundled JSON index, and helper script help output.
- The knowledge-atlas helper is stdlib-only.
- The asset-maintenance helper expects Pillow for trimming and openpyxl for workbook commands; those are only needed when you use those commands.

## If you are unsure
- If the user names a concept or acronym, start with `knowledge-atlas`.
- If the user names filenames, slide numbers, workbook rows, image trimming, or counts, start with `asset-maintenance`.
- If the ask spans both, answer the concept question first and then describe the safe maintenance step separately.
