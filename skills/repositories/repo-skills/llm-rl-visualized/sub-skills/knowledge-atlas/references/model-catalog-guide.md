# Model catalog guide

## How to use the catalog responsibly
The catalog is a fast orientation tool for the open-source LLM and VLM tables in `LLM-VLM-index (汇总).md`. Use it to answer:

- Which family a model belongs to.
- Whether a row has paper, code, and config pointers.
- Whether the prompt is about LLMs, VLMs, MLLMs, world models, or embodied-AI models.

Then verify the exact model page or model card if the user needs freshness, licensing, or deployment details.

## Table columns

| Column | Meaning | Common caveat |
| --- | --- | --- |
| Name | model family or checkpoint name | may be a base, instruct, preview, flash, or thinking variant |
| Organization | lab or company associated with the model | not always the implementation maintainer |
| Date | catalog row date | snapshot-oriented and may lag the official release history |
| Paper | paper, blog, PDF, or report pointer | the pointer type varies by row |
| Code | implementation or framework entry point | may point to a wrapper, adapter, or framework submodule |
| Config | config or model-card pointer | may be missing, moved, or renamed |

## Responsible workflow
1. Identify whether the user wants an LLM row, a VLM row, or a broader multimodal/embodied row.
2. Use the catalog to find the family, paper, code, and config triplet.
3. Treat the table as orientation, then verify with the official model card or project page when the question depends on current state.

## Freshness limitations
- The catalog is manually maintained and snapshot-based.
- Rows can mix blog posts, PDFs, GitHub repos, and Hugging Face files.
- Code links may point to a shared framework implementation rather than a project-owned file.
- Naming changes are common for preview, instruct, chat, thinking, or flash variants.
- Some rows intentionally have `N/A` for code or config.

## When not to rely on the catalog
- Choosing a production model without checking the current official model card.
- Making licensing or redistribution decisions.
- Claiming benchmark leadership or exact training details.
- Inferring runtime compatibility or serving instructions from the table alone.

## Provenance note
This guide was distilled from `LLM-VLM-index (汇总).md` and cross-checked against `README.md`, `src/README_EN.md`, and `src/references.md`.
