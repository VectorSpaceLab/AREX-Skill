# Problem types

H2O LLM Studio exposes five supported text problem types. The problem type controls which config dataclass tree loads, which dataset class is used, which fields are visible, and which consistency checks are applied.

## Quick matrix

| Problem type | YAML value | Dataset class behavior | Key data checks |
|---|---|---|---|
| Causal language modeling | `text_causal_language_modeling` | Builds causal-LM samples from prompt, answer, optional system, and optional parent history. | Prompt and answer columns must exist; answers must not be missing; chain ids must be valid when parent IDs are enabled. |
| Causal classification modeling | `text_causal_classification_modeling` | Adds integer `class_label` targets to prompt samples. | Every answer column must exist, contain no missing values, and cast to int; labels are non-negative; parent IDs are rejected. |
| Causal regression modeling | `text_causal_regression_modeling` | Adds float `class_label` targets to prompt samples. | Every target column must exist, contain no missing values, and cast to float; parent IDs are rejected. |
| Sequence-to-sequence modeling | `text_sequence_to_sequence_modeling` | Uses the same prompt/answer data layout with sequence-to-sequence defaults. | Prompt and answer columns must exist; generation sampling flags must be consistent. |
| DPO modeling | `text_dpo_modeling` | Builds chosen/rejected preference samples and prompt-only context. | Chosen and rejected answer columns must exist; `limit_chained_samples` must remain true. |

## Causal language modeling

Use `text_causal_language_modeling` for generation fine-tuning where the model learns to produce an answer from prompt context.

- Default-style columns: `instruction` / `input` prompts, `output` answer, optional `system`, optional `id` and `parent_id`.
- Supports multiple prompt columns joined by `prompt_column_separator`.
- Supports conversation chains with `parent_id_column` and `id_column`.
- `mask_prompt_labels` controls whether prompt tokens are excluded from loss.
- `only_last_answer` is meaningful only with chained conversations and prompt-label masking.
- Typical loss: `TokenAveragedCrossEntropy`.
- Default seeded example: OASST-derived data with `instruction`, `output`, `id`, and `parent_id` columns.

## Causal classification modeling

Use `text_causal_classification_modeling` for binary, multiclass, or multilabel text classification.

- Inputs are prompt text columns.
- Targets are one or more integer answer columns.
- Binary classification: one answer column with labels 0/1 and `num_classes == 1`.
- Multiclass classification: one answer column, `CrossEntropyLoss`, and `num_classes > 1`.
- Multilabel classification: multiple answer columns with binary integer labels and `num_classes == len(answer_column)`.
- Labels should start at 0 and be continuous; non-continuous labels are warned, non-integer or negative labels fail.
- Parent IDs are not supported.
- Default seeded example: IMDB with `text` and `label` columns.

## Causal regression modeling

Use `text_causal_regression_modeling` for text-to-continuous-target tasks.

- Inputs are prompt text columns.
- Targets are one or more float answer columns.
- The regression dataset casts target columns to floats.
- Parent IDs are not supported.
- Typical loss: `MSELoss`; default metric: `MSE`.
- Default seeded example: HelpSteer2 with prompt columns `prompt`, `response` and numeric targets `helpfulness`, `correctness`, `coherence`, `complexity`, and `verbosity`.

## Sequence-to-sequence modeling

Use `text_sequence_to_sequence_modeling` for tasks that transform source text into target text, such as summarization or translation-style data.

- Uses the same prompt/answer column schema as causal language modeling.
- Default backbone selection comes from the sequence-to-sequence model list, preferring `t5-small` when available.
- Architecture defaults differ from causal LM: the seq2seq config uses a bfloat16 backbone dtype by default, and its environment disables mixed precision by default.
- Text start/separator defaults are empty rather than causal-LM prompt markers.
- Temperature and `do_sample` must be consistent: temperature > 0 needs sampling enabled.
- No separate default dataset seeder was present in the inspected behavior; use a prompt/answer text-pair dataset.

## DPO modeling

Use `text_dpo_modeling` for preference optimization with chosen and rejected responses.

- Data format extends causal language modeling with `rejected_answer_column`.
- `rejected_prompt_column` defaults to `None`; set it only when the rejected answer has a different prompt than the chosen answer.
- `answer_column` is the preferred/chosen answer.
- `limit_chained_samples` is enabled by default and required by the DPO dataset class.
- For chained DPO conversations, chosen and rejected histories are the same until the last answer, where the chosen and rejected responses differ.
- Typical loss: `DPOLoss`; DPO training also exposes preference-specific settings such as `beta` and `simpo_gamma`.
- Default seeded example: Orca DPO pairs with `question`, `chosen`, and `rejected` columns.

## Choosing a problem type safely

- If the output is free-form text, choose causal LM or seq2seq.
- If the output is a categorical label, choose causal classification and make labels integer encoded.
- If the output is continuous, choose causal regression and make targets numeric.
- If the output is a preference pair, choose DPO and provide chosen/rejected answer columns.
- If a dataset has parent-id conversation chains, avoid classification and regression because those configs reject parent IDs.
- After changing a problem type, re-run config inspection and dataset validation because problem-specific fields can be dropped during YAML load.
