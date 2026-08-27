# DeepResearch ReAct Data Formats

Use this reference when preparing input questions, validating file references, or interpreting rollout files.

## Supported Input Files

The ReAct runner accepts only `.jsonl` and `.json` files.

### JSONL

Each non-empty line must be one JSON object. Blank lines fail because the runner parses every line directly.

```json
{"question": "What is the capital of France?", "answer": "Paris"}
{"question": "Explain quantum computing", "answer": ""}
```

JSONL is the recommended format because it streams naturally and matches the sample data.

### JSON

The file must be a JSON array. Each item must be an object.

```json
[
  {"question": "What is the capital of France?", "answer": "Paris"},
  {"question": "Explain quantum computing", "answer": ""}
]
```

## Required Record Fields

| Field | Required | Type | Runtime use |
|---|---|---|---|
| `question` | Yes for normal use | string | User prompt and resume key. Empty questions are skipped unless the runner can recover text from `messages[1].content`. |
| `answer` | Yes | string | Ground-truth/reference answer copied into rollout output and later used by benchmark evaluation. It may be empty for exploratory inference. |

The runner has a fallback for some chat-style records: if `question` is empty, it tries to read `messages[1].content` and split after `User:`. Prefer explicit `question` strings because fallback failures only print warnings and skip the item.

Duplicate stripped question text is risky: resume logic records processed questions by stripped `question`, so duplicates can be treated as already complete.

## Uploaded File References

The file parser tool expects file names embedded in the `question` text. The sample pattern is:

```json
{"question": "(Uploaded 1 file: ['hello.txt'])\n\nHello!", "answer": ""}
```

Rules for future agents:

1. Put the upload marker near the start of `question` so the model sees the available file name before the task.
2. Use a Python/JSON-like list of string file names inside the marker, for example `['report.pdf']` or `["table.xlsx", "notes.txt"]`.
3. Place referenced files in the `eval_data/file_corpus` directory that is visible from the inference working directory.
4. Keep file names relative to `file_corpus`; do not use absolute paths or `..` traversal.
5. Match names exactly, including case and extension.

The ReAct tool dispatcher calls `parse_file` with `file_root_path="./eval_data/file_corpus"`. If the launcher has changed into the inference working directory, that means the corpus directory must be under that working directory. If a future agent runs the Python runner from another directory, it must either change into the expected working directory first or adapt the file-root path deliberately.

## File Types

The prompt exposes `parse_file` for local files such as PDF, DOCX, PPTX, TXT, CSV, XLSX, DOC, ZIP, MP4, and MP3. The implementation separates ordinary document files from MP3/media handling and may require Dashscope or optional IDP/video model settings for richer parsing.

For simple text fixtures, a plain `.txt` file in `file_corpus` is sufficient for preflight validation. Full PDF/Office/media parsing is credentialed and should be treated as a runtime capability check, not a safe default unit test.

## Validation Commands

From this sub-skill directory or any other working directory, call the script by path:

```bash
python scripts/validate_deepresearch_dataset.py path/to/questions.jsonl
```

With file references:

```bash
python scripts/validate_deepresearch_dataset.py path/to/questions.jsonl --file-corpus path/to/eval_data/file_corpus
```

Useful options:

- `--allow-empty-answer` suppresses warnings for exploratory datasets with blank references.
- `--allow-messages-fallback` allows empty `question` if the record has a usable chat-style fallback.
- `--json` emits a machine-readable report.

## Rollout Output Records

Successful result lines contain:

| Field | Meaning |
|---|---|
| `question` | Input question text after fallback recovery if any. |
| `answer` | Input reference answer. |
| `messages` | Full ReAct transcript: system/user, assistant tool calls, user tool responses, and final assistant output. |
| `prediction` | Text extracted from `<answer>...</answer>` when present, otherwise a failure/no-answer string. |
| `termination` | Reason such as `answer`, `answer not found`, `exceed available llm calls`, `generate an answer as token limit reached`, or a token-limit format error. |

Error records add:

| Field | Meaning |
|---|---|
| `rollout_idx` / `rollout_id` | Rollout number associated with the failed task. |
| `error` | Exception or timeout summary. |
| `prediction` | Usually `[Failed]`. |
| `messages` | Empty list when the failure occurred outside the ReAct transcript. |

These rollout files are inference outputs. Metric judging, Pass@k, and invalid-answer accounting belong to the `benchmark-evaluation` sub-skill.
