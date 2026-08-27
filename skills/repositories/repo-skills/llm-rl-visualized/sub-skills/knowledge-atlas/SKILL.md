---
name: knowledge-atlas
description: "Route concept lookup, bilingual terminology, diagram-family
  selection, model-catalog orientation, citation/license guidance, and
  book-snippet orientation for the LLM-RL-Visualized atlas."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# knowledge-atlas

Use this sub-skill when the user wants concept navigation inside the atlas rather than model training or asset editing.

## Primary triggers
- Explain or compare PPO, GRPO, DPO, RLHF, RLAIF, TRPO, GAE, or DDPG.
- Find the diagram family for LLM structure, decoding, LoRA, RoPE, RAG, MCTS, reward models, DQN, or benchmarks.
- Map Chinese and English terms for a concept or figure.
- Orient to the LLM/VLM model catalog.
- Check citation, license, or book-snippet meaning.

## How to route
1. Search [references/atlas-index.json](references/atlas-index.json) or [scripts/search_atlas.py](scripts/search_atlas.py).
2. Use [references/atlas-guide.md](references/atlas-guide.md) to synthesize the answer.
3. For model rows, use [references/model-catalog-guide.md](references/model-catalog-guide.md).
4. For citations and reuse rules, use [references/citation-and-license.md](references/citation-and-license.md).
5. For LoRA, DPO, GAE, PPO, or jq snippets, use [references/book-code-snippets.md](references/book-code-snippets.md).
6. If the prompt is missing a term, language, or family boundary, use [references/troubleshooting.md](references/troubleshooting.md).

## Response rules
- Answer in the user's language when possible, and include the canonical English acronym when helpful.
- State the closest family and the main boundary with adjacent families.
- Say clearly that the repository is an educational visual atlas, not a training or serving package.
- Treat book code snippets as educational orientation only.

## Boundaries
- Do not run training, serving, or model-download workflows.
- Do not mutate image trees or Excel naming maps here.
- Do not present snippets as production code.

## Provenance
Distilled from these source anchors: `README.md`, `src/README_EN.md`, `AI-Roadmap(AI知识架构).md`, `LLM-VLM-index (汇总).md`, `src/references.md`, `src/code_from_book.md`, `LICENSE`.
