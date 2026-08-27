# Troubleshooting

## Dataset and schema issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError: The dataset should have a train split` | The input is not a dataset with a `train` split. | Build or load a dataset that exposes `train` before calling `model.evaluate(...)`. |
| `AssertionError: The dataset should have a column named text` | `TextDataset` input is missing `text`. | Rename or rebuild the dataset so `text` exists. |
| `AssertionError: The dataset should have a column named target if there is more than one column` | `TextDataset` has extra columns without `target`. | Drop the extras or add `target` explicitly. |
| `AssertionError: The dataset should have only two columns, text and target` | `TextDataset` has unsupported extra columns. | Reduce the dataset to `text` and optional `target` only. |
| `AssertionError: The dataset should have a column named instruction` | `InstructionDataset` input is missing `instruction`. | Add the `instruction` column before evaluation. |
| `AssertionError: The dataset should have only three columns, instruction, text and target` | `InstructionDataset` has extra columns. | Keep exactly `instruction`, `text`, and `target`. |
| `ValueError: The jsonl file should have keys text, instruction and target` | The instruction JSONL row schema is incomplete. | Rewrite each row with the exact keys `text`, `instruction`, and `target`. |
| `path does not exist` | The dataset path is wrong or missing. | Point the constructor at an existing directory or `.jsonl` file. |

If the failure is schema-related, fix the dataset first. Evaluation does not repair invalid inputs.

## Perplexity path issues

- `model.evaluate(...)` returns one scalar perplexity tensor, not a table of named metrics.
- The implementation reuses the model's finetuning max length, so very long examples can be truncated.
- The runtime uses `DEFAULT_DEVICE`. If CUDA is unavailable, it falls back to CPU and can be very slow.
- If you see OOM errors, reduce `batch_size` first.

## Adapter scaffold issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `status = "planned"` with no metrics | This is the current `LMEvalAdapter` scaffold behavior. | Treat the result as a contract placeholder. Real benchmark execution is not implemented yet. |
| `metadata["integration_status"] = "scaffold_only"` | Same scaffold limitation. | Use the metadata to confirm that the adapter path is only planning, not executing. |
| Missing result file | `output_path` was not provided or the run failed before persistence. | Pass a writable `output_path` and inspect the adapter call for exceptions. |
| Permission error writing JSON | The parent directory is not writable. | Choose a writable file path; the helper creates parents but cannot bypass permissions. |

## Model and runtime issues that block evaluation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No xturing.json found in local directory ...` | The model directory is a plain checkpoint directory, not a saved xTuring model. | Load a valid xTuring directory or pass `model_name=...` for the local checkpoint path. |
| `The model_name ... is not valid` | The requested model key is not registered. | Use a registered xTuring model key before evaluating. |
| `Int8 models are not supported on CPU` | An int8 model was loaded without a supported backend. | Use a CUDA-capable setup or switch to a non-int8 model. |
| `WARNING: CUDA is not available, using CPU instead, can be very slow` | The runtime is CPU-only. | Accept the slowdown or move the model to a GPU-enabled environment. |

## When you expected a benchmark runner

If you expected lm-evaluation-harness to execute tasks and return benchmark scores, that is outside the current contract. `LMEvalAdapter` is a scaffold-only adapter that records task intent and JSON metadata but does not yet run the external harness.
