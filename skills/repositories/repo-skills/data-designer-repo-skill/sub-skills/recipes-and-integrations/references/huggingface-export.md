# Hugging Face Export and Hub Upload

## Purpose

Read this when adapting a recipe that should export generated artifacts or publish a DataDesigner dataset to Hugging Face Hub. For the exact `DatasetCreationResults` API, also read [`../../generation-runtime/references/artifacts-results-and-resume.md`](../../generation-runtime/references/artifacts-results-and-resume.md).

## Choose local export or Hub upload

| Need | Use | Safety note |
| --- | --- | --- |
| Single local file for downstream tools | `results.export("dataset.jsonl" | "dataset.csv" | "dataset.parquet")` | Local and non-credentialed; supported formats are jsonl, csv, and parquet |
| Publish a dataset immediately after create | `results.push_to_hub(repo_id, description, token=None, private=False, tags=None)` | Credentialed network upload; preflight folder and metadata first |
| Publish an existing DataDesigner artifact folder | `HuggingFaceHubClient.push_to_hub_from_folder(dataset_path, repo_id, description, token=None, private=False, tags=None)` | Useful when the original `DatasetCreationResults` object is gone |
| Publish selected composite workflow output | Usually export first, or push the stage result directly | `CompositeWorkflowResults.push_to_hub` does not support selected output overrides yet |

## Dataset folder preflight

Before any Hub upload, verify the artifact folder is a DataDesigner dataset directory:

- It exists and is a directory.
- `metadata.json` exists and contains valid JSON.
- `parquet-files/` exists and contains at least one `*.parquet` batch file.
- `builder_config.json` exists if you want the dataset card to summarize configured column types, but the client can upload without it.
- Optional `images/` may contain generated images; upload skips it when missing or empty.
- Optional `processors-files/<processor_name>/` directories become separate Hub configs named by processor.

Do not upload blindly from a workflow artifact root. Point at the concrete dataset folder that contains `metadata.json` and `parquet-files/`.

## What the Hub upload does

The Hugging Face client uploads a complete DataDesigner dataset package:

| Local artifact | Hub location | Notes |
| --- | --- | --- |
| `parquet-files/*.parquet` | `data/*.parquet` | Main dataset config |
| `images/**` | `images/**` | Uploaded only when image files exist |
| `processors-files/<name>/*.parquet` | `<name>/*.parquet` | Each processor output becomes its own dataset config |
| `builder_config.json` | `builder_config.json` | Uploaded when present |
| `metadata.json` | `metadata.json` | File paths are rewritten from local artifact paths to Hub paths |
| generated dataset card | `README.md` | Includes quick-start loading code, schema/statistics, config type counts, tags, and citation |

Default dataset card tags are `synthetic` and `datadesigner`; custom tags are appended. Size categories are computed from record count.

## Repo id, token, and privacy rules

- `repo_id` must be exactly `username/dataset-name`; missing slash, extra slash, spaces, or invalid Hugging Face repo syntax fail before upload.
- `token=None` means the client resolves credentials from `HF_TOKEN` or cached `hf auth login` credentials.
- Use `private=True` for sensitive, licensed, embargoed, trace-derived, internal, or human-review data.
- Review `builder_config.json` and `metadata.json` before upload. They can reveal prompt templates, column names, dataset names, model aliases, processor names, or source-like metadata.
- Never publish raw private assistant traces, API keys, local machine paths, or credential-bearing seed fields.

## Recipe-specific export decisions

### Image recipes

Created image datasets include relative image paths in the dataframe and image files under the artifact folder. Hub upload includes the `images/` folder if it exists. Before upload:

- verify image paths referenced in the dataset exist under the dataset artifact base;
- confirm generated images are safe to publish for the domain;
- prefer private repos for medical, autonomy, drone, robotics, or human-looking synthetic images until reviewed;
- consider local `export` or a seed-parquet export when downstream VQA work should happen privately.

### Workflow-chaining recipes

For a composite workflow with reviewed or selected outputs:

- If the final selected output is the final stage dataset path, `CompositeWorkflowResults.push_to_hub(...)` can delegate to the final stage result.
- If the workflow used `stage_output_overrides`, selected a processor output, or exported a final merged parquet outside the stage dataset path, use `results.export(...)` for the selected output or push the concrete stage result directly.
- Do not push a `review_candidates` artifact unless the user explicitly wants to publish review inputs.

### Trace-ingestion recipes

Trace-derived datasets are high risk. Before upload:

- confirm trace content has been redacted or approved;
- review columns for project paths, branch names, user messages, tool logs, source metadata, and private file names;
- use `private=True` by default;
- record what was filtered and judged, but do not include raw private traces in the public dataset card.

## Common failures and recoveries

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Invalid repo_id format` | Not exactly `username/dataset-name`, invalid characters, or extra slash | Fix repo id before trying network upload |
| `Dataset path does not exist` or `not a directory` | Pointed at wrong artifact root or local export file | Use the dataset directory with `metadata.json` and `parquet-files/` |
| `Required file not found: metadata.json` | Not a DataDesigner dataset folder | Use a result artifact folder from `create`, not a preview-only object |
| `Required directory not found: parquet-files` or folder empty | Generation produced no durable batches, wrong path, or failed run | Re-run/repair generation through generation-runtime before upload |
| `Invalid JSON` in metadata or builder config | Corrupt or partial artifact | Do not upload; regenerate or recover from checkpoint |
| Authentication failed | Invalid/missing Hugging Face token | Set `HF_TOKEN`, pass `token=...`, or run `hf auth login` |
| Permission denied | Token lacks rights or namespace is wrong | Use an authorized namespace/token or create a private repo under an owned account |
| Failed to upload images or parquet | Network/storage/API failure or huge files | Retry only after checking folder size, network, and whether upload is approved |
| Dataset card generation fails | Metadata shape unexpected | Validate `metadata.json` and builder config; upload only after repair |

## Minimal safe Hub-upload plan

When the user asks for export but credentials are unavailable, return a plan like:

1. Run or receive a completed `create` artifact folder.
2. Locally verify `metadata.json`, `parquet-files/*.parquet`, optional `images/`, optional processor outputs, and row count.
3. Review metadata/config for sensitive fields.
4. Decide repo id, visibility, description, and tags.
5. Set `HF_TOKEN` or use `hf auth login`.
6. Call result-level or folder-level push.
7. Verify returned URL and sample `datasets.load_dataset(repo_id, "data", split="train")` only if network access is permitted.
