# Data formats

This guide lists the field shapes that appear most often in text workflows. Use it before you pick operators or write fixtures.

## Storage and step conventions

- `storage.step()` advances the cache step before each operator.
- Step 0 is the source file.
- Later steps are written as `file_name_prefix_stepN.<cache_type>`.
- Common cache types: `json`, `jsonl`, `csv`, `parquet`, `pickle`, and in some flows `xlsx`.
- Many operators append new columns to the current dataframe; filters may also drop rows.

## Common column families

| Family | Common input columns | Common output columns | Notes |
| --- | --- | --- | --- |
| Raw text cleaning | `raw_content`, `text`, `content`, `lines` | cleaned variants of the same text | Used by `general_text`, `text_pt`, and some `core_text` operators |
| Prompt-driven generation | `raw_content`, `problem`, `instruction`, `input`, `text` | `generated_content`, `generated_prompt`, `generated_question`, `generated_answer` | `PromptedGenerator`, `FormatStrPromptedGenerator`, and `Text2QAGenerator` use this family |
| Reasoning | `instruction`, `output`, `golden_answer` | `generated_cot`, `question_difficulty`, `question_category`, `answer_match_result` | Many reasoning filters expect `generated_cot` and `golden_answer` |
| Code | `instruction`, `input`, `text`, `lines`, `filetype`, `filename`, `line_count`, `language` | `generated_instruction`, `generated_code`, `quality_score`, `quality_feedback`, filter labels | File-type / length filters use the file metadata columns |
| Conversations | `category`, `conversation` | conversation lists with `role` and `value` | `conversation` is usually a list of message objects |
| Text2SQL | `SQL`, `db_id`, `question`, `evidence` | `prompt`, `cot_reasoning`, `sql_component_difficulty`, `sql_execution_difficulty` | Database-aware operators need a valid database manager |
| Text pretraining / SFT | `raw_content`, `text`, `instruction`, `output`, `input` | scorer fields and keep/drop labels | Typical for `text_pt` and `text_sft` flows |

## High-value field names

These names appear frequently across workflows:

- `raw_content`: unprocessed text input
- `text`: normalized or merged plain text
- `problem`: math or reasoning prompt
- `instruction`: instruction-tuning prompt
- `input`: auxiliary context for SFT / QA
- `output`: target answer or response
- `golden_answer`: reference answer for validation
- `generated_cot`: generated reasoning trace
- `generated_code`: generated code snippet
- `SQL`: executable SQL string
- `db_id`: database identifier
- `question`: natural-language question
- `evidence`: schema or supporting context
- `conversation`: multi-turn chat transcript

## Run-key conventions

Prefer these patterns when wiring operators:

- Single column transform: `input_key` -> `output_key`
- Multi-column scoring or validation: `input_*_key` and `output_*_key`
- Named family examples:
  - reasoning: `input_question_key`, `input_answer_key`, `input_gt_answer_key`
  - code: `input_instruction_key`, `input_code_key`, `output_score_key`, `output_feedback_key`
  - text2sql: `input_sql_key`, `input_db_id_key`, `input_question_key`, `input_evidence_key`
  - text2model: `instruction`, `input`, `output` in the final QA file

Avoid reusing an output column name that already exists unless the operator explicitly documents in-place overwrite behavior.

## Schema validation tips

- Use a JSON schema when a generation stage must return structured JSON.
- Validate column presence before running an expensive model-backed stage.
- For filters, check both the row count and the new label column.
- For prompt-driven generation, confirm that the output column is aligned with the downstream consumer before moving to the next step.

## Minimal fixture shapes

If you only need tiny offline fixtures, keep these rows in mind:

- text fixture: `raw_content`
- reasoning fixture: `instruction`, `output`, `golden_answer`
- translation fixture: `raw_content`, `source_lang`, `target_lang`
- code fixture: `instruction`, `generated_code`, `lines`, `filetype`, `filename`, `line_count`
- text2sql fixture: `SQL`, `db_id`, `question`, `evidence`
