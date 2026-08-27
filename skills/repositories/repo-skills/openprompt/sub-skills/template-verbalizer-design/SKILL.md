---
name: template-verbalizer-design
description: "Design, load, validate, and troubleshoot OpenPrompt templates,
  verbalizers, calibration, LM-BFF generators, and bundled prompt assets without
  depending on the original repository checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: OpenPrompt
  package: openprompt
  source-version: "1.0.1"
  source-commit: f6fb080ef755c37c01b7959e7560d007049510e8
license: Apache 2.0
---

# OpenPrompt Template and Verbalizer Design

Use this sub-skill when a task asks you to write or debug OpenPrompt prompt components: template grammar, hard/mixed/soft/prefix/P-tuning/PTR templates, manual/one2one/knowledgeable/automatic/generation/soft/proto/PTR verbalizers, LM-BFF template or label-word generation, calibration, or prompt asset files.

Do **not** use this sub-skill for full training loops, dataset acquisition, runner selection, or benchmark reproduction. Route those to the OpenPrompt data/config and training/generation sub-skills when available.

## Required mental model

OpenPrompt separates prompt design into two cooperating objects:

1. A `Template` wraps each `InputExample` into pieces containing literal text, placeholders from `text_a`/`text_b` or `meta`, soft tokens, special tokens, and one or more mask positions.
2. A `Verbalizer` maps language-model outputs at mask positions into task labels, usually through label words.

The most common failure mode is treating template text, class order, and label-word files as independent. They are coupled:

- every ordinary classification template needs at least one `{"mask"}`;
- each verbalizer file must match the dataset class order or class names;
- multi-mask templates need a multi-mask-aware verbalizer such as `PTRVerbalizer` or generation logic;
- label words that tokenize into multiple tokens are model/tokenizer-dependent and should be checked before training.

## Fast operating procedure

1. **Choose the prompt family.**
   - Hard textual prompt: `ManualTemplate` + `ManualVerbalizer`.
   - Hard + learned soft tokens: `MixedTemplate` or `PtuningTemplate`.
   - Prefix-tuning for supported T5/GPT2-style models: `PrefixTuningTemplate`.
   - Appended soft prompt: `SoftTemplate`; learned head verbalizer: `SoftVerbalizer`.
   - Relation extraction with several masks: `PTRTemplate` + `PTRVerbalizer`.
   - Text-generation labels or dynamic target text: `GenerationVerbalizer`.
   - Search/auto prompt design: `T5TemplateGenerator`, `RobertaVerbalizerGenerator`, or `AutomaticVerbalizer`.
2. **Write the template string.** Use OpenPrompt's Python-dict-like grammar: `{"placeholder": "text_a"}`, `{"placeholder": "text_b"}`, `{"meta": "field"}`, `{"mask"}`, `{"text": "literal"}`, `{"special": "<sep>"}`, `{"soft"}`, `{"soft": "seed text"}`, and optional `shortenable`, `post_processing`, `soft_id`, `duplicate`, or `same` attributes.
3. **Choose class mapping.** For dict verbalizers, pass `classes=[...]` matching dataset labels exactly. For list/text verbalizers, ensure the file line order matches label ids.
4. **Load from code or assets.** Use `from_file(path, choice=...)` for one-line-per-template files and OpenPrompt verbalizer files. Use the bundled assets under `references/prompt-assets/scripts/` when you need repo-maintained examples without the original checkout.
5. **Validate before model work.** Run the bundled static validator:

   ```bash
   python scripts/validate_prompt_assets.py
   # or, from this sub-skill directory:
   python scripts/validate_prompt_assets.py --assets-dir references/prompt-assets/scripts
   ```

   Add `--tokenizer /path-or-name --allow-remote-tokenizer` only if the user permits downloads; otherwise it uses local tokenizer files only.
6. **Only then connect training.** `PromptForClassification` extracts model outputs at `loss_ids > 0`, then the verbalizer processes them. `PromptForGeneration` and `GenerationVerbalizer` use generation-style targets instead of fixed class label words.

## Runtime references

- `references/api-reference.md` — class signatures, loader keys, base method behavior, and file format contracts.
- `references/workflows.md` — tested design workflows for manual/mixed/soft/PTR/generation/LM-BFF/calibration usage.
- `references/troubleshooting.md` — common grammar, mask, prefix-space, class-order, tokenizer, calibration, and file-format failures.
- `references/prompt-assets.md` — bundled asset corpus layout, adaptation notes, and validation policy.
- `references/prompt-assets/scripts/` — self-contained copy/adaptation of the repo `scripts/**/*.txt|json|jsonl` prompt assets.
- `scripts/validate_prompt_assets.py` — static checker for bundled or user-supplied prompt assets.

## Evidence provenance

This sub-skill was distilled from OpenPrompt commit `f6fb080ef755c37c01b7959e7560d007049510e8` using `openprompt/prompt_base.py`, `openprompt/prompts/*.py`, `openprompt/utils/calibrate.py`, `docs/source/notes/template.rst`, `docs/source/notes/verbalizer.rst`, tutorials `1.*`, `3.1_LMBFF.py`, `4.1_all_tasks_are_generation.py`, and the repository `scripts/` prompt assets.

## Acceptance checklist before handing work to another agent

- Template strings parse with balanced dict/set tokens and contain expected masks.
- Verbalizer assets parse as OpenPrompt `.txt`, `.json`, or `.jsonl` formats.
- Class names/order and number of label groups are documented.
- Multi-mask designs name the matching verbalizer strategy.
- Multi-token label words are checked statically and, when model choice matters, with the target tokenizer.
- Any generated/edited assets are copied into the self-contained prompt-asset subtree or supplied explicitly by the user.
