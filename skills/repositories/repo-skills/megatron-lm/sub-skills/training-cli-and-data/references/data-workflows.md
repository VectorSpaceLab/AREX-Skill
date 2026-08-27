# Data workflows

## Input format

GPT-style preprocessing expects JSON Lines by default. Each line is a JSON object and the default key is `text`:

```json
{"text": "One training document."}
{"text": "Another training document."}
```

Use `--json-keys` when the text field has another name or multiple fields are needed.

## Preprocess JSONL into indexed datasets

Command shape:

```bash
python tools/preprocess_data.py \
  --input <data.jsonl> \
  --output-prefix <processed_prefix> \
  --tokenizer-type <TokenizerType> \
  --workers <N> \
  --append-eod
```

Tokenizer choices include `NullTokenizer` for tiny synthetic fixtures, `HuggingFaceTokenizer`, `GPT2BPETokenizer`, `SentencePieceTokenizer`, `TikTokenizer`, and others. Real training usually needs tokenizer model/vocab/merge files.

Expected outputs include the selected JSON key and dataset type. With the default `text` key, look for:

```text
<processed_prefix>_text_document.bin
<processed_prefix>_text_document.idx
```

Use `<processed_prefix>_text_document` as the data prefix in later GPT training commands unless the preprocessing command used a different JSON key.

## Tiny fixture pattern

For parser and data-pipeline smoke tests, use `NullTokenizer` to avoid external tokenizer downloads. `NullTokenizer` expects whitespace-separated integer token ids, not arbitrary words, so the tiny JSONL rows should look like `{"text":"1 2 3 4 5"}`:

```bash
python tools/preprocess_data.py \
  --input tiny.jsonl \
  --output-prefix tiny_out \
  --tokenizer-type NullTokenizer \
  --vocab-size 128 \
  --workers 1 \
  --append-eod \
  --json-keys text
```

Use the bundled `create_tiny_preprocess_fixture.py` to create numeric-token `tiny.jsonl` and print a command template. If a smoke fixture contains natural-language text, choose a real tokenizer mode with local tokenizer files instead of `NullTokenizer`.

## Merge small dataset prefixes

Many small prefixes create metadata and file-descriptor overhead at scale. Merge already-preprocessed prefixes in a directory:

```bash
python tools/merge_datasets.py \
  --input <directory-with-prefixes> \
  --output-prefix <merged_prefix>
```

Target fewer, larger prefixes for large jobs.

## Prebuild cache for large jobs

At large node counts, startup time is often dominated by rank-0 dataset-index creation and the barrier while all other ranks wait. Prebuild the GPT dataset cache before training:

```bash
python tools/prepare_cache.py \
  --data-path <data-prefix-or-blend> \
  --split 99,1,0 \
  --data-cache-path <cache-dir> \
  --global-batch-size <GBS> \
  --seq-length <SEQ> \
  --prepare-cache-world-size <future-world-size>
```

Do not use `prepare_cache.py` for unsupported modes such as mock data, SFT, FIM data, or step-batch-size schedules.

## Fast-path training flags

After cache preparation:

```bash
--dataloader-fast-cache-load
--dataloader-defer-npy-index-mmap
--data-cache-path <cache-dir>
--num-workers 2
```

When blending many datasets, generate and pass a per-dataset sequence-count JSON:

```bash
python tools/build_sequences_per_dataset.py \
  --data-path <data-prefixes...> \
  --per-dataset-sequences-path sequences.json
```

Then train with:

```bash
--per-dataset-sequences-path sequences.json
```

## Object storage notes

For object-storage / multi-storage-client data:

- Use `--no-mmap-bin-files` because memory mapping does not apply to object storage.
- Keep index/cache paths visible to the ranks that construct datasets.
- Prebuild caches when possible to avoid all-rank startup stalls.

## Data validation checklist

- JSONL is valid and selected keys exist on every line.
- Tokenizer files/model are present and match the model vocabulary.
- Output prefix directory is writable and has enough space.
- `.bin/.idx` outputs are produced before training; for default GPT text preprocessing the prefix usually ends in `_text_document`.
- `--data-path` points to indexed-dataset prefixes, not necessarily the original `--output-prefix` and not a literal file with extension.
- `--split` matches train/valid/test expectations.
