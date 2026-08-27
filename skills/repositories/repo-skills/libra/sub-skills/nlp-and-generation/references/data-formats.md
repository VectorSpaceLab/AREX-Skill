# NLP and generation data formats

## Text classification CSV
Required columns:
- a text column selected by the instruction
- a label column, defaulting to `label` unless `label_column` is provided

Recommended tiny fixture:

```csv
review_text,sentiment
"loved the food",positive
"the room was dirty",negative
```

## Summarization CSV
Required columns:
- a source text column selected by the instruction
- a target summary column, defaulting to `summary` unless `label_column` is provided

If the target column is called `abstract`, `headline`, or `short_summary`, pass it explicitly.

## Text generation file
`generate_text(file_data=True)` expects the client dataset path to be a plain text file. If the user provides a prefix instead of a file, use `file_data=False` and pass `prefix`.

## Named entity recognition CSV
`named_entity_query` selects a single text column from the instruction. The column should contain strings; missing values and non-string values should be cleaned before use.

## Image captioning CSV
The captioning path expects:
- one column containing image paths that exist at runtime
- one caption/label column chosen by `instruction` or `label_column`

The helper tries to discover the path column by testing entries with `os.path.exists`. Keep image paths either absolute or relative to the working directory used for training.

## Preprocessing behavior
- Text cleaning lowercases, strips URLs/punctuation-like noise, lemmatizes, and encodes vocabulary for classification.
- Summarization prefixes examples with `summarize: ` and tokenizes with T5.
- Captioning writes temporary `.npy` feature files next to images and removes them after training.
