# Data Formats and Prompt Construction

This reference distills the released Alpaca dataset shape and the exact prompt/label flow used by `train.py`.

## Released dataset summary

- File: `alpaca_data.json`
- Verified row count: **52,002**
- Record schema: every row is a JSON object with the keys:
  - `instruction`: string, required, describes the task.
  - `input`: string, required in the released file, but may be empty.
  - `output`: string, required, target answer text.
- Rough composition: about 40% of rows have a non-empty `input` field.
- Training split: the public release uses all 52,002 rows for training; there is no recommended validation split in the source release.

## Accepted file shapes for validation

The bundled validator accepts either:

- a JSON array of Alpaca-style records, or
- JSONL / NDJSON with one record per line.

Each row must still be an object with the same three string keys.

## Prompt templates used by `train.py`

`train.PROMPT_DICT` has exactly two keys:

- `prompt_input`
- `prompt_no_input`

### Template for rows with a non-empty `input`

```text
Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input}

### Response:
```

### Template for rows with an empty `input`

```text
Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Response:
```

## How `train.py` turns rows into model examples

The source flow is:

1. Load the dataset with `utils.jload(data_path)`.
2. For each row, choose the prompt template with `example.get("input", "") != ""`.
3. Build the source string from the chosen template.
4. Build the target string as `example["output"] + tokenizer.eos_token`.
5. Tokenize the concatenated `source + target` text.
6. Copy the tokenized example into the label tensor.
7. Mask the prompt portion with `IGNORE_INDEX = -100` so the loss only applies to the response tokens.

## Signatures verified from the source

- `train.preprocess(sources, targets, tokenizer) -> Dict`
- `train.make_supervised_data_module(tokenizer, data_args) -> Dict`
- `train.SupervisedDataset(data_path, tokenizer)`
- `train.DataCollatorForSupervisedDataset(tokenizer)`

## Label masking and collation details

### `preprocess`

- Tokenizes `examples = [source + target]` and `sources` separately.
- Uses the tokenized source length for each row to set the prompt prefix in `labels` to `IGNORE_INDEX`.
- Returns `input_ids` and `labels` tensors.

### `SupervisedDataset`

- Reads a JSON list from disk.
- Builds `sources` with one of the two prompt templates.
- Builds `targets` as `output + eos_token`.
- Stores the tokenized `input_ids` and `labels` for later indexing.

### `DataCollatorForSupervisedDataset`

- Pads `input_ids` with `tokenizer.pad_token_id`.
- Pads `labels` with `IGNORE_INDEX`.
- Returns an `attention_mask` from `input_ids.ne(tokenizer.pad_token_id)`.

## Tokenizer assumptions in `train.py`

The training script adds special tokens when they are missing from the tokenizer:

- `pad_token` -> `[PAD]`
- `eos_token` -> `</s>`
- `bos_token` -> `<s>`
- `unk_token` -> `<unk>`

It also uses right padding and sets `use_fast=False` when loading the tokenizer.

## Prompt-preview expectations

When you validate a sample row, use these checks:

- Non-empty `input` should render the `prompt_input` variant.
- Empty `input` should render the `prompt_no_input` variant.
- The target text should end with the tokenizer EOS token.
- The prompt prefix should be the only section masked with `-100` in the labels.

## Example row interpretation

A row like this:

```json
{
  "instruction": "Give three tips for staying healthy.",
  "input": "",
  "output": "1. Eat a balanced diet..."
}
```

should be treated as a no-input example. A row with a paragraph in `input` should use the paired-input template.

## Validation notes

- Missing keys are invalid.
- Non-string fields are invalid.
- Blank `instruction` should fail validation.
- Blank `output` is usually a warning in the bundled validator unless strict output checks are enabled.
- Do not bundle the full release dataset into the skill tree; validate user-supplied files instead.
