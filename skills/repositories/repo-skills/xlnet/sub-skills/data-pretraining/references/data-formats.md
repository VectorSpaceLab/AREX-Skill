# Data formats

## Raw corpus format

XLNet pretraining reads text as a stream of sentences:

- one sentence per non-empty line
- one empty line = end of document
- optional `<eop>` suffix on a line = end of paragraph

Example:

```text
This is the first sentence.
This is the second sentence and also the end of the paragraph.<eop>
Another paragraph.

Another document starts here.
```

Notes:

- `<eop>` is a paragraph marker, not a document boundary.
- Empty lines are the document boundary used by `data_utils.py`.
- The SentencePiece model should include `<eop>` and `<eod>` in the recipe so the marker survives preprocessing.

## Pre-tokenized id format

If the corpus is already tokenized into ids, set `--from_raw_text=False` and provide:

- one sequence of integer ids per non-empty line
- whitespace-separated ids only
- blank lines still mean document boundaries

Example:

```text
101 2003 1037 3231 102
101 2023 2003 2178 102

101 2178 6251 8349 102
```

Important: `data_utils.py` still loads SentencePiece in id mode, so keep `sp_path` valid even when the input is already numeric.

## Generated artifacts

### `corpus_info.json`

Written once by `task=0` under `save_dir`.

Tracked fields:

- `vocab_size`
- `bsz_per_host`
- `num_core_per_host`
- `seq_len`
- `reuse_len`
- `uncased`
- `bi_data`
- `mask_alpha`
- `mask_beta`
- `num_predict`
- `use_eod`
- `sp_path`
- `input_glob`

### `tfrecords/record_info*.json`

Written under `save_dir/tfrecords/` with the same preprocessing fingerprint as the TFRecord shard.

Contents:

- `filenames`: list of TFRecord shard paths
- `num_batch`: batch count for the shard set

The filename prefix is derived from `split`, `task`, and `pass_id`, then fingerprinted with the batch and sequence settings.

### `tfrecords/*.tfrecords`

The shard filename uses the same fingerprint as the record-info JSON.

Example shape:

```text
record_info-train-0-0.bsz-32.seqlen-512.reuse-256.bi.alpha-6.beta-1.fnp-85.json
record_info-train-0-0.bsz-32.seqlen-512.reuse-256.bi.alpha-6.beta-1.fnp-85.tfrecords
```

## Filename contract

`format_filename()` composes the fingerprint as:

```text
{prefix}.bsz-{bsz}.seqlen-{seq_len}.{reuse?}{uncased?}{bi|uni}.alpha-{mask_alpha}.beta-{mask_beta}.{fnp?}{suffix}
```

Where:

- `reuse-<n>.` appears only when `reuse_len` is set
- `uncased.` appears only when `uncased=True`
- `bi` / `uni` records the bidirectional setting
- `fnp-<n>.` appears only when `num_predict` is set

Important: `use_eod` and `from_raw_text` are not encoded in the output filename. Keep them recorded in `corpus_info.json` and in your command builder inputs.

## SentencePiece recipe contract

The README example requires these key settings:

- `--model_type=unigram`
- `--vocab_size=32000`
- `--character_coverage=0.99995`
- `--shuffle_input_sentence`
- `--input_sentence_size=10000000`
- `--control_symbols=<cls>,<sep>,<pad>,<mask>,<eod>`
- `--user_defined_symbols=<eop>,.,(,),",-,–,£,€`

If the SentencePiece model is missing or does not preserve the special symbols, preprocessing and later masking logic can diverge from the README recipe.
