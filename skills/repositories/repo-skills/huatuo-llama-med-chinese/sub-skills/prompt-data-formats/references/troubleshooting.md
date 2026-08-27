# Prompt and Data Troubleshooting

## `Can't read templates/<name>.json`

Cause: the prompt helper resolves templates relative to the current working directory.

Fixes:

- Run model or validation commands from an asset root that contains `templates/`.
- If embedding the prompt helper in a new script, resolve template paths from an explicit asset root rather than relying on process cwd.
- Do not pass an empty template name unless an `alpaca.json` template is actually present.

## Response extraction fails or returns the wrong substring

Cause: `get_response` splits decoded model output with the exact `response_split` string from the template.

Fixes:

- Confirm `response_split` is present in the template JSON.
- Confirm the prompt's final answer marker and `response_split` are byte-for-byte identical.
- Pay special attention to ASCII colon `:` versus Chinese full-width colon `：`.
- Avoid inserting the same response marker inside expected model answers.

## `KeyError: 'prompt_input'`

Cause: `generate_prompt` uses `prompt_input` whenever the record's `input` value is truthy. The literature template is no-input only.

Fixes:

- Keep literature records' `input` fields empty when using `literature_template`.
- Add and validate a `prompt_input` key before using non-empty `input` with a no-input-only template.
- For ordinary medical instruction JSONL, use a template that defines both prompt variants.

## JSON versus JSONL confusion

Symptoms:

- JSON parser errors near a line boundary.
- Dataset loader sees only one giant record.
- Validator reports that a file is an array when JSONL objects were expected, or that a JSON-list file is not a list.

Fixes:

- Use JSONL for ordinary instruction records: one complete object per line, no surrounding brackets, no commas between lines.
- Use a JSON list for literature and benchmark assets: one complete JSON document beginning with `[`.
- Convert formats with an explicit script that parses then re-serializes records; do not use text-only search-and-replace.

## Malformed Chinese dialogue prefixes

Literature records encode dialogue context inside `instruction` with `<user>:` and sometimes `<bot>:` turns.

Fixes:

- Keep ASCII angle brackets and colon exactly as `<user>:` and `<bot>:`.
- Strip accidental leading BOM characters or non-printing bytes before validation.
- Do not replace the prefixes with `用户：`/`助手：` unless every consumer and prompt template is updated accordingly.
- Ensure the next response remains in `output`; do not append the target answer into `instruction`.

## Benchmark has questions but no answers

Cause: CMCOQA `question.json` stores prompts and ICD-10 categories only.

Fixes:

- Do not treat benchmark objects as supervised records.
- Generate model answers in a separate result artifact.
- Score generated answers on Completeness, Depth, and Professionalism; keep the source question list unchanged.

## Converting literature JSON list to JSONL

Use a parser-based conversion and preserve Unicode text:

```python
import json
from pathlib import Path

records = json.loads(Path("liver_cancer.json").read_text(encoding="utf-8"))
with Path("liver_cancer.jsonl").open("w", encoding="utf-8") as out:
    for record in records:
        out.write(json.dumps(record, ensure_ascii=False) + "\n")
```

After conversion, re-run validation and confirm the selected prompt template supports the record's `input` behavior.
