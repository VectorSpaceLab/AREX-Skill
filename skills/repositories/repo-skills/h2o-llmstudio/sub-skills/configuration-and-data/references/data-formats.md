# Data formats

This reference covers the dataset shapes that H2O LLM Studio config and data helpers expect. It focuses on local validation and does not launch training or download models.

## Connectors and accepted files

The app import flow supports these connector families: local upload, local path, AWS S3, Azure Datalake, H2O Drive, Kaggle, and Hugging Face. Imported data should resolve to CSV or Parquet dataframe files. The upload/import layer also allows zip archives containing dataframe files.

Direct dataframe readers accept only:

- `.csv` / `.CSV` and mixed-case CSV extensions
- `.pq` / `.PQ`
- `.parquet` / `.PARQUET` and mixed-case Parquet extensions

The direct reader uses pandas CSV loading with newline line termination for CSV and the PyArrow engine for Parquet. Zip files are import artifacts, not direct inputs to `read_dataframe()`.

## Dataframe read and missing-value rules

- `read_dataframe(path)` returns a dataframe for CSV or Parquet paths and raises for unsupported extensions.
- `is_valid_data_frame(path)` is a lightweight validity probe for CSV / Parquet readability.
- `read_dataframe(..., non_missing_columns=[...])` drops rows with missing values in those columns. With `handling="error"`, missing required values become an exception instead of a warning.
- `read_dataframe(..., fill_columns=[...], fill_value="")` fills missing values in selected columns before required-column filtering.
- `read_dataframe_drop_missing_labels()` treats prompt columns as non-missing columns, fills prompt columns with strings, and fills a scalar answer column when present. Multi-target classification/regression answers are validated by the dataset sanity checks.

## Core column meanings

| Config field | Meaning |
|---|---|
| `prompt_column` | One or more columns containing user/input text. Multiple columns are joined with `prompt_column_separator`. |
| `prompt_column_separator` | Separator used only when more than one prompt column is selected. It is decoded with unicode-escape behavior, so `\\n\\n` becomes blank-line separation. |
| `system_column` | Optional system text prepended to the first turn. Missing selected system columns are treated as empty systems by the conversation handler. |
| `answer_column` | Expected text output for generation, chosen answer for DPO, or one/more label or target columns for classification/regression. |
| `rejected_prompt_column` | Optional DPO rejected prompt column. Keep it `None` when chosen and rejected answers share the same prompt. |
| `rejected_answer_column` | Required DPO rejected response column. |
| `parent_id_column` | Optional chain link pointing from a row to a prior row. Requires an `id_column` when active. |
| `id_column` | Row id used by `parent_id_column` to reconstruct conversation ancestry. |

## Problem-specific dataframe shapes

| Problem type | Required columns | Additional rules |
|---|---|---|
| Causal language modeling | Prompt column(s), answer column; optional system, id, parent id | Supports single-turn and chained conversations; answer must be present and non-null. |
| Sequence-to-sequence modeling | Prompt column(s), answer column; optional system, id, parent id | Same text-pair layout as causal language modeling, with seq2seq model defaults. |
| Causal classification | Prompt column(s), one or more integer answer columns | Labels must cast to integers. Binary uses one 0/1 column with `num_classes == 1`; multiclass uses one integer class column with `num_classes > 1`; multilabel uses multiple binary columns and `num_classes == len(answer_column)`. Parent IDs are not supported. |
| Causal regression | Prompt column(s), one or more float answer columns | Targets must cast to floats. Parent IDs are not supported. |
| DPO modeling | Prompt column(s), chosen answer column, rejected answer column; optional rejected prompt, id, parent id | `limit_chained_samples` must stay enabled. For chained conversations, chosen and rejected histories match until the final chosen/rejected answer. |

## Conversation chains

`ConversationChainHandler` reconstructs conversations from `id_column` and `parent_id_column`.

- Without a configured parent-id column, each row is one conversation turn.
- With parent IDs and `limit_chained_samples: false`, every row becomes a sample containing all ancestor turns up to that row.
- With parent IDs and `limit_chained_samples: true`, only complete conversations ending at leaf rows are sampled.
- IDs and parent IDs may be strings or numbers; ids are compared after casting to the parent-id dtype.
- Parent IDs not present in the data are treated as missing parents.
- Valid chained data needs at least one root row with an empty or missing parent, unique ids, no self-references, and no cycles.
- Automatic validation splitting keeps conversation-chain groups together by splitting on reconstructed chain ids.

## Sampling behavior

When `data_sample < 1.0`, `data_sample_choice` controls whether the train split, validation split, or both are sampled. Non-chain data samples rows with a minimum target of 10 rows. Chained data samples by conversation root to avoid splitting a conversation across sampled and unsampled subsets.

## Text assembly behavior

For generation-style datasets:

1. Prompt columns are converted to strings and joined when multiple columns are selected.
2. The system text, prompt start token, answer separator, and optional EOS tokens are assembled around each turn.
3. When prompt labels are masked, loss is applied to answer tokens rather than prompt tokens.
4. For `only_last_answer`, only the final answer in a chain is supervised while earlier conversation context remains available.

## Default seeded datasets

On app initialization, the default dataset seeding logic can prepare several example datasets. If a local demo-dataset directory is configured, the seeders read local Parquet files; otherwise, they use the corresponding Hugging Face datasets.

| Seeded dataset | Problem family | Configured columns |
|---|---|---|
| OASST conversation data | Causal language modeling | `instruction`, `output`, `id`, `parent_id` |
| Orca DPO pairs | DPO modeling | `question`, `chosen`, `rejected` |
| IMDB | Causal classification | `text`, `label` |
| HelpSteer2 | Causal regression | prompt columns `prompt`, `response`; target columns `helpfulness`, `correctness`, `coherence`, `complexity`, `verbosity` |

There is no separate default seeder for sequence-to-sequence in the inspected behavior; use a prompt/answer text-pair dataset with the seq2seq problem type.
