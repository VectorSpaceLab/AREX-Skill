# Data formats and readers

YiVal represents each example as `InputData(content=<dict>, expected_result=<optional>)`. The keys in `content` become keyword arguments to the configured `custom_function`.

## CSV reader

Registry id: `csv_reader`

Config class: `CSVReaderConfig`

```yaml
dataset:
  source_type: dataset
  file_path: /absolute/path/to/data.csv
  reader: csv_reader
  reader_config:
    chunk_size: 100
    use_first_column_as_id: false
    expected_result_column: expected_result
```

Behavior:

- The first row must be a non-empty header row.
- Rows with any missing value are skipped and logged as warnings.
- If `expected_result_column` is set, that column is removed from `content` and stored as `expected_result`.
- Every remaining column name should match a `custom_function` parameter excluding `state`.
- Rows are yielded in chunks of `chunk_size`.
- Relative paths are first checked under the installed `yival` package root, then as user-specified paths. Prefer absolute paths for generated configs that should work outside the source checkout.

Example CSV:

```csv
question,expected_result
What is 2+2?,4
What is the capital of France?,Paris
```

## Hugging Face dataset reader

Registry id: `huggingface_dataset_reader`

Config class: `HuggingFaceDatasetReaderConfig`

```yaml
dataset:
  source_type: dataset
  file_path: "https://datasets-server.huggingface.co/rows?dataset=owner%2Fname&config=default&split=train"
  reader: huggingface_dataset_reader
  reader_config:
    example_limit: 5
    output_mapping:
      question: question
      answer: expected_answer
    include: []
    exclude: []
```

Behavior:

- The reader appends `&offset=<n>&limit=<limit>` to the configured URL.
- It expects a JSON response containing `rows`, where each row has an inner `row` mapping.
- `output_mapping` maps source fields to custom-function argument names.
- `include` and `exclude` are regex filters applied to transformed values.
- The reader yields up to `example_limit` examples.

Use only when network access and remote dataset availability are acceptable.

## Machine-generated data

For generated examples, `dataset.source_type` is `machine_generated` and `dataset.data_generators` is a mapping from generator id to config. See the prompt-automation sub-skill for full details.

```yaml
dataset:
  source_type: machine_generated
  data_generators:
    openai_prompt_data_generator:
      number_of_examples: 3
      chunk_size: 1000
      input_function:
        name: task_name
        description: Task description.
        parameters:
          field_name: str
```

## User-input source

For interactive mode:

```yaml
dataset:
  source_type: user_input
```

The standard `DataProcessor.process_data()` does not produce rows for `user_input`; `ExperimentRunner` routes this source type to the Dash interactive UI.
