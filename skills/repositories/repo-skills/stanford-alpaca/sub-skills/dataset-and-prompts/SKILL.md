---
name: dataset-and-prompts
description: "Guides Stanford Alpaca dataset schema, prompt formatting, label
  masking, validation, intended use, and license checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Dataset and Prompts

Use this sub-skill when the task is about the released Alpaca instruction dataset, Alpaca-style data files, prompt rendering, source/target construction, label masking, or pre-flight validation before training or generation.

## Route here for

- Explaining the released `alpaca_data.json` record schema and the verified 52,002-row release count.
- Checking whether a JSON or JSONL file can be consumed as Alpaca-style supervised fine-tuning data.
- Rendering the exact prompt form used for records with a non-empty `input` and records with an empty `input`.
- Explaining how `train.py` constructs `sources`, appends the tokenizer EOS token to `targets`, and masks prompt labels with `IGNORE_INDEX = -100`.
- Answering dataset datasheet, model-card, intended-use, and license questions before using Alpaca data or generated derivatives.

## Reroute instead

- OpenAI/Self-Instruct data generation, seed tasks, completion parsing, cost, network, or API keys: route to `instruction-generation` at `../instruction-generation/SKILL.md`.
- Trainer/FSDP/DeepSpeed commands, model downloads, checkpoint directories, or full supervised fine-tuning execution: route to `fine-tuning` at `../fine-tuning/SKILL.md`.
- Alpaca/LLaMA weight diff creation, recovery, checksums, or weight artifact licenses: route to `weight-diff-recovery` at `../weight-diff-recovery/SKILL.md`.
- Repository-wide install or route selection issues: return to the root router at `../../SKILL.md`.

## Bundled references and scripts

- Read [data formats](references/data-formats.md) for the schema, prompt templates, training source/target construction, label masking, and validator semantics.
- Read [intended use and licenses](references/intended-use-and-licenses.md) before distributing, modifying, training on, or generating derivatives of Alpaca data.
- Read [troubleshooting](references/troubleshooting.md) when validation fails, prompt text differs from expected Alpaca format, tokenizer padding/EOS behavior is confusing, or license constraints are unclear.
- Run [validate_alpaca_data.py](scripts/validate_alpaca_data.py) to validate JSON/JSONL records and preview the exact Alpaca prompt branch selected for each row.

## Safe validation workflow

1. Start with the offline validator; it never calls OpenAI, downloads models, imports Torch, or reads the original repository.

   ```bash
   python scripts/validate_alpaca_data.py path/to/alpaca_or_generated.json --preview 2
   ```

2. For the public release, expect a JSON array with exactly 52,002 objects and the keys `instruction`, `input`, and `output` on every row:

   ```bash
   python scripts/validate_alpaca_data.py alpaca_data.json --expect-count 52002
   ```

3. For generated data handoff, validate JSONL or JSON first, then send schema-clean examples to `instruction-generation` if the question is about producing more examples or to `fine-tuning` if the question is about training with the file.

4. Treat empty `input` as valid: it selects the no-input prompt template. Treat missing `input` as invalid because the released dataset uses the key on every row.

5. Treat blank `output` as a warning by default because the released dataset contains a small number of blank outputs; use `--require-nonempty-output` when building a stricter training corpus.

## Core facts to remember

- The verified `train.PROMPT_DICT` keys are `prompt_input` and `prompt_no_input`.
- The verified `train.preprocess` signature is `preprocess(sources, targets, tokenizer) -> Dict`.
- `SupervisedDataset` loads a JSON list, selects the prompt template with `example.get("input", "") != ""`, and sets each target to `output + tokenizer.eos_token`.
- `preprocess` tokenizes `source + target` and the `source` alone, then masks prompt-token labels with `-100` so loss is only taken on the response portion.
- `DataCollatorForSupervisedDataset` pads `input_ids` with `tokenizer.pad_token_id`, pads `labels` with `-100`, and returns `attention_mask = input_ids.ne(tokenizer.pad_token_id)`.

## Validation before downstream work

Before training or generation, confirm:

- The file parses as JSON array or JSONL object rows.
- Every row is an object with string `instruction`, `input`, and `output` fields.
- `instruction` is non-empty after trimming whitespace.
- Any blank `output` rows are intentional, filtered, or accepted by the downstream owner.
- Prompt previews match the exact Alpaca templates in [data formats](references/data-formats.md).
- The intended use is research/non-commercial where the data license or generated-data restrictions apply; see [intended use and licenses](references/intended-use-and-licenses.md).
