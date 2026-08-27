# Troubleshooting

## Schema and constructor failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError: The dataset should have a train split` | The saved dataset or in-memory `DatasetDict` does not contain `train` | Save a `train` split or wrap the rows in a `DatasetDict({"train": ...})` |
| `AssertionError: The dataset should have a column named text` | `TextDataset` input is missing `text` | Add a `text` column |
| `AssertionError: The dataset should have a column named target if there is more than one column` | `TextDataset` has extra columns but no `target` | Add `target` or remove the extra column(s) |
| `AssertionError: The dataset should have only two columns, text and target` | `TextDataset` has more than two columns | Drop extra columns before saving |
| `AssertionError: The dataset should have a column named instruction` | `InstructionDataset` is missing `instruction` | Add the column or route to a different dataset family |
| `AssertionError: The dataset should have only three columns, instruction, text and target` | `InstructionDataset` has extra columns | Strip extras before conversion |
| `AssertionError: The dataset should have a column named prompt/chosen/rejected` | `PreferenceDataset` schema is incomplete or the source used names like `accepted`/`rejected` | Rename columns to `prompt`, `chosen`, and `rejected` |
| `AssertionError: The dataset should have only three columns: prompt, chosen, and rejected` | `PreferenceDataset` has extra columns | Keep only the three required columns |
| `path does not exist` | The path passed to a dataset constructor is wrong | Verify the path and use a saved dataset directory or supported `.jsonl` file |
| `Unsupported file format: ... Use a directory or .jsonl file.` | `PreferenceDataset` was pointed at an unsupported file type | Convert to a saved dataset directory or `.jsonl` |

## JSONL and row-level failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: The jsonl file should have keys text, instruction and target` | A line in the instruction JSONL file is missing one of the required keys | Add the missing key or repair the line |
| `ValueError: The jsonl file should have keys: prompt, chosen, and rejected` | A line in the preference JSONL file is missing one of the required keys | Rename or add the required columns |
| `json.JSONDecodeError` while reading JSONL | The file is not valid JSON per line | Fix the malformed line before conversion |
| `Could not infer a supported schema from the train split columns: ['instruction', 'input', 'output']` | A raw Alpaca file was passed to the xTuring validator before conversion | Convert it with the Alpaca helper first, or validate the converted dataset with `--schema instruction`. |
| Empty or missing rows after conversion | Source rows contained `None`, bad types, or missing fields | Re-run the converter with row validation enabled |

## Alpaca conversion failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The converter stops on a specific row | A source record is missing `instruction`, `input`, or `output` | Repair that row and re-run the conversion |
| The converted dataset loads but later validation fails | The output directory was written with the wrong column names | Make sure the output columns are `instruction`, `text`, and `target` |

## Self-instruct and document-extraction failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No document text is extracted | `textract` is missing, or the path is not a directory | Install `textract` and the required system libraries, then pass a directory |
| `generated_tasks.jsonl` appears in the wrong place | The helper writes it in the current working directory | Run from the intended workspace or remove the stale file before retrying |
| Generation seems to reuse old output | The cache directory already exists | Delete the cache directory if you want a clean run |

## API wrapper failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: The anthropic SDK is required for ClaudeTextGenerationAPI...` | `anthropic` is not installed | Install `anthropic` before using the Claude wrapper |
| Repeated `OpenAIError` or `CohereError` messages | API quota, network, or request-size issues | Check the key, network access, and prompt length; then retry |
| OpenAI retries keep shrinking the target length | The prompt is too large for the requested completion | Shorten the prompt or lower the requested output length |
| Claude returns no response after retries | All retry attempts failed | Check the API key, network path, and rate limits |

## Keyword and template pitfalls

- The `InstructionDataset` constructor keyword is spelled `promt_template` in the current runtime API.
- If you enable `infix_instruction=True`, the instruction string must contain exactly one `{text}` and one `{target}` marker.
- `ListPromptTemplate.build(...)` raises `ValueError` when a required variable is missing.

## Unsupported gap

- `Text2ImageDataset` is registered but not implemented.
- Its constructor raises `NotImplementedError`, so image data should be routed elsewhere.
