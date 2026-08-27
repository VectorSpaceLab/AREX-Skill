---
name: prompt-data-formats
description: "Explains Huatuo-Llama-Med-Chinese prompt templates, Prompter
  behavior, data schemas, and benchmark assets for format validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Prompt and Data Formats

Use this sub-skill when a task is about Huatuo-Llama-Med-Chinese prompt construction, template selection, instruction-data schemas, literature-dialogue records, or CMCOQA benchmark questions.

## What this sub-skill covers

- Prompt template semantics and `Prompter` edge cases: [references/prompt-templates.md](references/prompt-templates.md).
- Inference, supervised fine-tuning, knowledge-tuning sample, and literature data schemas: [references/data-formats.md](references/data-formats.md).
- CMCOQA benchmark question schema and scoring dimensions: [references/benchmark.md](references/benchmark.md).
- Common format and template failures: [references/troubleshooting.md](references/troubleshooting.md).
- A bundled stdlib validator for template, data, and benchmark asset bundles: [scripts/validate_assets.py](scripts/validate_assets.py).

## Route elsewhere

- Running generation or loading model weights belongs to the inference owner, not this format skill.
- Fine-tuning commands, LoRA settings, and training resource planning belong to the finetuning owner.
- Merging, exporting, or selecting checkpoint artifacts belongs to the checkpoint-export owner.

## Minimal workflow

1. Identify the asset family: templates, instruction JSONL, literature JSON list, knowledge-tuning text, or benchmark questions.
2. Read the matching bundled reference above before editing or converting assets.
3. For asset validation, run the bundled validator against the asset root that contains `templates/`, `data/`, `data-literature/`, and/or `benchmark/`:

   ```bash
   python sub-skills/prompt-data-formats/scripts/validate_assets.py \
     --asset-root <asset-root> \
     --check templates,data,benchmark \
     --max-records 1000
   ```

4. Treat validator failures as schema issues, not model-quality issues. Fix formatting before routing any task to inference or training.
