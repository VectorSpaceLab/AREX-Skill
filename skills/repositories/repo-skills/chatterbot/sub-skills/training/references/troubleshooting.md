# Training Troubleshooting

## `KeyError` from `field_map`

**Symptoms**

- A trainer raises `KeyError` and says to check `field_map`.
- CSV/JSON training starts but fails while reading rows.

**Likely causes**

- A header name in `field_map` does not exist in the file.
- An integer column index is out of range.
- A JSON item lacks a required key.
- You mapped `in_response_to` but some rows do not include that field.

**Recovery**

1. Inspect a tiny sample row and make sure every mapped value exists.
2. For CSV/TSV, choose either header names or integer indexes consistently.
3. For JSON, ensure the root key is `conversation` and each object has the keys in `field_map`.
4. Reproduce with the bundled fixture helper before training real data:

   ```bash
   python sub-skills/training/scripts/file_training_demo.py --format csv
   python sub-skills/training/scripts/file_training_demo.py --format json
   ```

## No files detected

**Symptoms**

- Logs say no `[csv]` or `[json]` files were detected.
- Training completes without adding statements.

**Recovery**

- Pass a file path or a directory containing files with the configured extension.
- For TSV, initialize `CsvFileTrainer(file_extension="tsv", ...)`.
- Remember that directories are searched recursively for `*.csv`, `*.tsv`, or `*.json` based on trainer configuration.

## Missing corpus dependencies

**Symptoms**

- `Unable to import "yaml"`.
- Dotted corpus paths resolve to missing files.
- `chatterbot.corpus.english.greetings` cannot be loaded.

**Recovery**

```bash
python -m pip install pyyaml chatterbot-corpus
```

Then verify:

```python
from chatterbot import corpus
print(corpus.list_corpus_files("chatterbot.corpus.english.greetings"))
```

## spaCy model missing during training

Training runs the bot's tagger to fill `search_text` and `search_in_response_to`. If a default English bot fails, install the model:

```bash
python -m spacy download en_core_web_sm
```

If you intentionally use a storage adapter that does not need text indexing, configure the appropriate tagger before creating trainers.

## Unexpected progress bars in automation

Pass `show_training_progress=False` or set:

```bash
CHATTERBOT_SHOW_TRAINING_PROGRESS=0
```

## Ubuntu corpus downloads or extraction problems

`UbuntuCorpusTrainer` can download a large archive and is pending deprecation. Prefer `CsvFileTrainer` for local TSV data. If you must use the Ubuntu corpus:

- set `limit` while testing;
- use a dedicated data directory;
- do not extract into a symlink;
- expect failures if the URL is unavailable or the archive is not a valid tar file.

The trainer rejects symlinks/hard links and path traversal during extraction, so do not override that safety behavior.

## Export creates no useful conversations

`export_for_training` exports only statements with an `in_response_to` value. If the output is empty, confirm that training actually created response relationships and not only standalone statements.
