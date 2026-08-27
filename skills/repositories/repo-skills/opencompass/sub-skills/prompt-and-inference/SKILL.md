---
name: prompt-and-inference
description: "Build and debug OpenCompass prompt templates, PromptList dialogue
  prompts, retrievers, Gen/PPL inferencers, reader_cfg answer masking,
  in-context examples, and meta_template role routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenCompass Prompt and Inference

Use this sub-skill when an OpenCompass task involves prompt construction or inference config behavior: `PromptTemplate`, `RawPromptTemplate`, `PromptList` dialogue turns, `ice_template`, `prompt_template`, retrievers, `GenInferencer`, `PPLInferencer`, output-column masking, or `meta_template` role mapping.

## Route the Task

- For prompt syntax, answer masking, missing literal fields, dialogue `PromptList`, raw messages, or CoT wording, use `references/prompt-templates.md`.
- For choosing `ZeroRetriever`/few-shot retrievers and wiring `GenInferencer` vs `PPLInferencer`, use `references/retrievers-and-inferencers.md`.
- For symptoms such as literal `{answer}`, leaked labels, missing system role handling, unsupported PPL candidate templates, or train split failures, use `references/troubleshooting.md`.
- For a no-download local preview of tiny samples and templates, run `python scripts/render_prompt_preview.py --help` from this sub-skill directory.

## High-Value Defaults

- Use `GenInferencer` for free-form answers and keep the dataset answer column in `reader_cfg.output_column` so it is replaced by `gen_field_replace_token` instead of leaking into the generation prompt.
- Use `PPLInferencer` for multiple-choice/discriminative tasks and provide candidate templates keyed by label (`"A"`, `"B"`, etc.) in `prompt_template.template` or `ice_template.template`.
- Use `ZeroRetriever` for 0-shot; use `FixKRetriever` only when the selected in-context examples exist in the dataset train/index split.
- Put model-specific chat wrappers in the model `meta_template`; keep dataset prompt templates model-agnostic and role-based (`HUMAN`, `BOT`, `SYSTEM`).

## Boundaries

- Route dataset class creation, `reader_cfg` source columns, and config file structure to `configuration-and-datasets`.
- Route tokenizer behavior, model chat templates, backend acceleration, and real HF/API inference issues to `model-backends`.
- Do not claim real model inference was verified from this sub-skill; the bundled script renders prompt construction only.
