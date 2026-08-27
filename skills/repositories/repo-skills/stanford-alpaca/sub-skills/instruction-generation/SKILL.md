---
name: instruction-generation
description: "Guide Self-Instruct-style instruction data generation with prompt
  rendering, completion parsing, filtering, ROUGE-L deduplication, and safe
  credential/network handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Instruction Generation

Use this sub-skill for the Stanford Alpaca instruction-generation workflow: render seed-task prompts, inspect or parse saved OpenAI completion text, apply the source filters, and understand how the live generator resumes through `regen.json`.

## Use this sub-skill when
- You want to render prompts from seed records in the repo's `prompt.txt` style.
- You need to parse or debug saved completion text without calling OpenAI.
- You want to understand the live generation loop, filter rules, ROUGE-L deduplication, or resume behavior.
- You need a safe place to reason about credential, network, and legacy OpenAI client requirements.

## Route elsewhere when
- The question is about released Alpaca dataset schema, license, or training-record formatting for SFT: see [`dataset-and-prompts`](../dataset-and-prompts/SKILL.md).
- The question is about turning generated records into supervised fine-tuning input or Trainer data modules: see [`fine-tuning`](../fine-tuning/SKILL.md).
- The question is about checkpoint diffs or recovery: see [weight-diff-recovery](../weight-diff-recovery/SKILL.md).

## Bundled references
- [`references/workflows.md`](references/workflows.md) — offline prompt debugging, saved-completion parsing, live-generation gates, and `regen.json` resume semantics.
- [`references/prompt-template.md`](references/prompt-template.md) — bundled copy of the prompt template used by the generator.
- [`references/api-reference.md`](references/api-reference.md) — verified signatures, defaults, and record schemas.
- [`references/troubleshooting.md`](references/troubleshooting.md) — API key, rate limit, client compatibility, parsing, multiprocessing, and ROUGE/tokenization guidance.

## Bundled scripts
- [`scripts/render_instruction_prompt.py`](scripts/render_instruction_prompt.py) — offline prompt renderer for tiny fixtures or user-provided seed-task files.
- [`scripts/parse_openai_response.py`](scripts/parse_openai_response.py) — offline parser for saved completion text or JSON payloads.

## Safety and workflow notes
- Offline prompt rendering and saved-response parsing are deterministic and do not call OpenAI.
- Live generation requires `OPENAI_API_KEY`, network access, and a legacy OpenAI completion client compatible with `openai.Completion.create`.
- The generator loads `regen.json` from the output directory when present, appends accepted records, and rewrites that file after each batch.
- ROUGE-L deduplication uses the source thresholding behavior; if you are only debugging formatting, use the bundled scripts first and keep networked runs separate.

## Quick orientation
1. Read the workflow notes and the API reference.
2. Render a tiny prompt fixture with the bundled renderer to validate formatting.
3. Parse a saved completion sample with the bundled parser to inspect the filter behavior.
4. Only move to live API generation after the credential and network gate is satisfied.
