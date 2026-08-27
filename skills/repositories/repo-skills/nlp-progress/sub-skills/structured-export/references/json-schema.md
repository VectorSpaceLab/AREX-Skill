# NLP-progress structured JSON schema

The exporter writes a JSON array. Each item represents one H1 task parsed from one Markdown page. Fields are emitted only when the corresponding Markdown evidence exists, so consumers must treat many fields as optional.

## Top-level task object

```json
{
  "task": "Language modeling",
  "description": "Task-level prose from the H1 section.",
  "source_link": {
    "title": "NLP-progress",
    "url": "https://github.com/sebastianruder/NLP-progress"
  },
  "subtasks": [],
  "datasets": []
}
```

Fields:

- `task` string: H1 text without the leading `#`.
- `description` string: lines after the H1 up to the next heading, joined and stripped.
- `source_link` object: fixed source attribution with `title` and `url`.
- `subtasks` list, optional: H2 sections under the task.
- `datasets` list, optional: H3 datasets directly under the task when no H2 subtask is active.

## Subtask object

```json
{
  "task": "Word Level Models",
  "description": "Subtask prose from the H2 section.",
  "source_link": {
    "title": "NLP-progress",
    "url": "https://github.com/sebastianruder/NLP-progress"
  },
  "datasets": []
}
```

Fields:

- `task` string: H2 text without the leading `##`.
- `description` string: lines after the H2 up to the next heading, joined and stripped.
- `source_link` object: fixed source attribution.
- `datasets` list, optional: H3 datasets seen while this subtask is active.

## Dataset object

```json
{
  "dataset": "Penn Treebank",
  "description": "Dataset prose excluding detected SOTA table lines.",
  "dataset_links": [
    {"title": "Mikolov et al., (2011)", "url": "https://example.invalid/paper"}
  ],
  "sota": {
    "metrics": ["Validation perplexity", "Test perplexity", "Number of params"],
    "rows": []
  },
  "subdatasets": []
}
```

Fields:

- `dataset` string: H3 text without the leading `###`.
- `description` string: H3 prose, with detected SOTA table lines removed.
- `dataset_links` list, optional: Markdown links found in the dataset description. Each link has `title` and `url`.
- `sota` object, optional: emitted when the dataset section has one valid SOTA table.
- `subdatasets` list, optional: emitted when multiple SOTA tables are assigned subdataset labels or when H4 subdataset sections with valid SOTA tables are parsed under this H3 dataset.

## SOTA object

```json
{
  "metrics": ["BLEU", "Accuracy"],
  "rows": [
    {
      "model_name": "Transformer Big",
      "metrics": {
        "BLEU": "29.3",
        "Accuracy": "-"
      },
      "paper_title": "Scaling Neural Machine Translation",
      "paper_url": "https://example.invalid/paper",
      "code_links": [
        {"title": "Official", "url": "https://example.invalid/code"}
      ]
    }
  ]
}
```

Fields:

- `metrics` list: table header names other than `Model`, `Paper` or `Paper / Source`, and optional `Code`.
- `rows` list: one object per parsed data row after the Markdown separator row.

Row fields:

- `model_name` string or null: model cell with a parenthesized author suffix removed. For example, `M-BERT (Scialom et al., 2020)` becomes `M-BERT`. If the cell consists only of parenthesized text, `model_name` may be null.
- `metrics` object: maps every metric header name in `sota.metrics` to the row's raw cell string.
- `paper_title` and `paper_url`, optional: emitted only when the paper/source cell contains a Markdown link. Plain text such as `--` produces no paper fields.
- `code_links`, optional: emitted only when the table has a `Code` column. It is a list and may be empty when the row's code cell has no Markdown links.

## Subdataset object

```json
{
  "subdataset": "General",
  "sota": {
    "metrics": ["MAP", "MRR", "P@5"],
    "rows": []
  }
}
```

Fields:

- `subdataset` string: inferred label for a SOTA table. The label is either the H4 heading text or the nearest non-empty line before a table in a multi-table H3 section. Inferred labels are stripped of `**` and a trailing colon.
- `sota` object: same shape as the SOTA object above.

## Minimal complete skeleton

```json
[
  {
    "task": "Machine translation",
    "description": "Machine translation is the task of translating a sentence.",
    "datasets": [
      {
        "dataset": "WMT 2014 EN-DE",
        "description": "Models are evaluated using BLEU.",
        "sota": {
          "metrics": ["BLEU"],
          "rows": [
            {
              "model_name": "Transformer Big",
              "metrics": {"BLEU": "29.3"},
              "paper_title": "Scaling Neural Machine Translation",
              "paper_url": "https://example.invalid/paper"
            }
          ]
        }
      }
    ],
    "source_link": {
      "title": "NLP-progress",
      "url": "https://github.com/sebastianruder/NLP-progress"
    }
  }
]
```

## Consumer guidance

- Do not assume every task has both `subtasks` and direct `datasets`.
- Do not assume every dataset has `sota`; some sections are prose-only or have tables that do not satisfy SOTA header rules.
- Do not assume `Code` exists. When `Code` is absent, rows omit `code_links` entirely.
- Do not parse metrics as numbers without a cleanup step. Values are raw Markdown cell strings and may contain `-`, parentheticals, asterisks, spaces, or text notes.
- Do not rely on model author names in JSON. Parenthesized author text is used only to strip the visible `model_name`; it is not emitted as a separate field.
