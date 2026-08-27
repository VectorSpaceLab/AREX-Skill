# Data formats

This sub-skill covers the three xTuring dataset families that the current runtime supports:

- `TextDataset` for text completion / continuation
- `InstructionDataset` for instruction tuning
- `PreferenceDataset` for DPO-style preference pairs

It also covers the `ListPromptTemplate` helper used by `InstructionDataset`.

## Supported constructor inputs

| Dataset | Accepted inputs |
| --- | --- |
| `TextDataset(path)` | Hugging Face `Dataset`, `DatasetDict`, a Python `dict` of column lists, or a saved dataset directory |
| `InstructionDataset(path, infix_instruction=False, promt_template=None)` | Hugging Face `Dataset`, `DatasetDict`, a Python `dict` of column lists, a saved dataset directory, or a `.jsonl` file |
| `PreferenceDataset(path)` | Hugging Face `Dataset`, `DatasetDict`, a Python `dict` of column lists, a saved dataset directory, or a `.jsonl` file |

All three datasets validate the `train` split.

## `TextDataset`

### Schema

Required column:

- `text`

Optional column:

- `target`

Validation rules:

- `train` split must exist.
- `text` must be present in `train`.
- If there is more than one column, `target` must also be present.
- If `target` is present, the `train` split must have exactly two columns.

### Examples

Dictionary input:

```python
from xturing.datasets import TextDataset

dataset = TextDataset({
    "text": ["first text", "second text"],
})
```

With labels / targets:

```python
TextDataset({
    "text": ["first text", "second text"],
    "target": ["first target", "second target"],
})
```

Saved dataset directory:

```python
TextDataset("saved_text_dataset")
```

### Save behavior

`TextDataset.save(path)` delegates to the underlying Hugging Face dataset object and saves the full dataset object to disk. If you passed a `DatasetDict`, its splits are preserved.

## `InstructionDataset`

### Schema

Required columns:

- `instruction`
- `text`
- `target`

Validation rules:

- `train` split must exist.
- `train` must contain `instruction`, `text`, and `target`.
- The `train` split must have exactly three columns.

### Constructor options

- `infix_instruction=False`: enable infix formatting when the instruction string contains `{text}` and `{target}` markers.
- `promt_template=None`: current keyword name in the runtime API; if set, it is wrapped in `ListPromptTemplate`.

### `ListPromptTemplate`

`ListPromptTemplate(template, input_variables)` formats a single string template and checks that every required variable is provided to `build(...)`.

The current runtime expects these variables:

- `instruction`
- `text`

If a variable is missing, `build(...)` raises `ValueError("Missing input variable ...")`.

### Examples

Dictionary input:

```python
from xturing.datasets import InstructionDataset

dataset = InstructionDataset({
    "instruction": ["Summarize the text"],
    "text": ["A long article..."],
    "target": ["A short summary."],
})
```

JSONL input:

```jsonl
{"instruction": "Summarize the text", "text": "A long article...", "target": "A short summary."}
{"instruction": "Translate to French", "text": "Hello", "target": "Bonjour"}
```

Infix formatting example:

```python
InstructionDataset(
    {
        "instruction": ["Rewrite {text} as bullet points with answer {target}"],
        "text": ["source text"],
        "target": ["bullet list"],
    },
    infix_instruction=True,
)
```

Prompt-template example:

```python
InstructionDataset(
    {
        "instruction": ["Summarize the text"],
        "text": ["A long article..."],
        "target": ["A short summary."],
    },
    promt_template="Instruction: {instruction}\nContext: {text}\nAnswer:",
)
```

### Save behavior

`InstructionDataset.save(path)` saves only the `train` split to disk.

### Generated-data note

`InstructionDataset.generate_dataset(...)` returns a new `InstructionDataset` backed by the generated `sampled_generated.jsonl` cache. The resulting rows use the same three columns: `instruction`, `text`, and `target`.

## `PreferenceDataset`

### Schema

Required columns:

- `prompt`
- `chosen`
- `rejected`

Validation rules:

- `train` split must exist.
- `train` must contain `prompt`, `chosen`, and `rejected`.
- The `train` split must have exactly three columns.

### Examples

Dictionary input:

```python
from xturing.datasets import PreferenceDataset

dataset = PreferenceDataset({
    "prompt": ["What is AI?"],
    "chosen": ["AI is a field of computer science."],
    "rejected": ["AI is magic."],
})
```

JSONL input:

```jsonl
{"prompt": "What is AI?", "chosen": "AI is a field of computer science.", "rejected": "AI is magic."}
```

### Save behavior

`PreferenceDataset.save(path)` saves only the `train` split to disk.

## Alpaca conversion mapping

The Alpaca-style source JSON uses:

- `instruction`
- `input`
- `output`

Convert it to the `InstructionDataset` schema:

- `instruction` → `instruction`
- `input` → `text`
- `output` → `target`

The bundled conversion script writes a saved Hugging Face dataset with a single `train` split containing exactly those three columns.

## Unsupported gap

`Text2ImageDataset` is registered but not implemented. Its constructor raises `NotImplementedError`, so image data should not be routed here.
