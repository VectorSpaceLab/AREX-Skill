---
name: chinese-llama-alpaca-2
description: "Routes Chinese-LLaMA-Alpaca-2 training, inference, serving,
  evaluation, and integration workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Chinese-LLaMA-Alpaca-2

This skill routes work for the Chinese-LLaMA-2 and Chinese-Alpaca-2 repository.
It is intentionally a router, not a full manual.

Use it when a task mentions:

- Chinese-LLaMA-2 or Chinese-Alpaca-2 model paths, tokenizers, or prompts
- pretraining, SFT, LoRA merging, or model conversion
- local generation, Gradio chat, speculative sampling, or long-context helpers
- OpenAI-compatible serving, HTTP endpoints, or deployment wrappers
- C-Eval, CMMLU, LongBench, or benchmark result files
- llama.cpp launch wrappers or the repo's retrieval-style integration notes

## Pick a sub-skill

| Task family | Read |
| --- | --- |
| Dataset prep, pretraining, SFT, or merge/export | `sub-skills/train-and-merge/SKILL.md` |
| Transformers inference, chat UI, speculative sampling, or prompt wrapping | `sub-skills/hf-inference/SKILL.md` |
| OpenAI-style API serving or the FastAPI server | `sub-skills/api-serving/SKILL.md` |
| C-Eval, CMMLU, or LongBench evaluation | `sub-skills/evaluation/SKILL.md` |
| llama.cpp wrappers or external integration notes | `sub-skills/local-integrations/SKILL.md` |

## Bundled assets

- `assets/prompts/alpaca-2.txt`
- `assets/prompts/alpaca-2-long.txt`
- `assets/tokenizer/`

Read `references/prompt-and-tokenizer.md` before changing prompt text or tokenizer assumptions.

## Cross-cutting references

- `references/workflows.md` for the repository's main workflow map
- `references/model-overview.md` for model family, context, and backend compatibility guidance
- `references/troubleshooting.md` for shared failure modes
- `references/repo-provenance.md` for source commit and staleness checks
- `references/repo-routing-metadata.json` for router import metadata

## Router behavior

- Prefer the most specific sub-skill.
- Use the training sub-skill for data preparation or merge/export questions even when the task also mentions inference.
- Use the inference sub-skill for local generation or chat UX questions even when the task mentions prompt templates.
- Use the API-serving sub-skill for OpenAI-compatible HTTP responses, request schemas, or deployment flags.
- Use the evaluation sub-skill for benchmark configuration and result files, not for general model comparison prose.
- Use the local-integrations sub-skill for llama.cpp wrappers and the external integration notes around retrieval-style examples.

## Notes

- The generated runtime skill is self-contained; do not rely on the source checkout staying available.
- If a task needs more detail than this router provides, open the nearest `references/*.md` file instead of widening the router itself.
