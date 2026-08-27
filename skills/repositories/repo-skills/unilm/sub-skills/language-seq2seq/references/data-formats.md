# Data Formats

## `s2s-ft` JSONL input

Each line is a complete JSON object. Training lines require both `src` and `tgt`; decoding requires `src` and ignores `tgt` if present.

Raw text format:

```json
{"src": "Messages posted on social media claimed the user planned to kill as many people as possible.", "tgt": "Threats to kill pupils are being investigated by police."}
```

Tokenized WordPiece/list format:

```json
{"src": ["messages", "posted", "on", "social", "media"], "tgt": ["threats", "to", "kill", "pupils"]}
```

Native `s2s-ft` detection is based on the Python type of `src`: if `src` is a list, it treats `src` and `tgt` as already-tokenized tokens; otherwise it calls the selected tokenizer on string values.

## JSONL validation checklist

- One JSON object per line; no outer JSON array.
- `src` is present on every line.
- `tgt` is present on every training line.
- `src` and `tgt` are both strings or both token lists for a given example.
- Token lists contain string tokens, not token ids.
- Tokenized examples use the exact tokenizer/vocab family used by the checkpoint.
- For uncased models, raw text workflows include `--do_lower_case`; tokenized workflows should already be cased/uncased consistently.
- Source and target lengths fit the planned `--max_source_seq_length` and `--max_target_seq_length` after tokenization.

## `s2s-ft` cached features

`--cached_train_features_file` stores tokenized IDs. Reuse it only when all of these are unchanged:

- tokenizer vocabulary and casing;
- `src`/`tgt` input file content;
- max source/target lengths;
- LMDB vs tensor-file mode;
- train vs decode mode.

If tokenization, casing, or lengths change, delete or regenerate the cache.

## UniLMv1 parallel files

Legacy UniLMv1 training reads parallel source and target text files from `--data_dir`:

```text
train.src  # one source sequence per line
train.tgt  # one target sequence per line
```

If `--src_file` or `--tgt_file` is omitted, the native defaults are `train.src` and `train.tgt`. The files must have aligned line counts. With `--tokenized_input`, each line is whitespace-tokenized and passed through a whitespace tokenizer instead of the BERT tokenizer.

Legacy decoding reads one source line per example from `--input_file`; with `--tokenized_input`, each source line must already be tokenized for the matching BERT/UniLM vocab.

## Legacy special tokens

Common BERT special tokens:

```text
[UNK]
[SEP]
[X_SEP]
[PAD]
[CLS]
[MASK]
```

UniLM seq2seq variants may also require:

```text
[S2S_CLS]
[S2S_SEP]
[S2S_SOS]
```

Use `scripts/inspect_legacy_tokenizers.py` on a local vocab file before enabling `--s2s_special_token`, `--pos_shift`, or a checkpoint known to rely on these tokens.

## Prediction outputs

`s2s-ft/decode_seq2seq.py` writes one generated text line per input example. If `--output_file` is omitted, the native decoder derives an output path from the checkpoint path and split. If `--need_score_traces` is enabled, a pickle trace file may also be written next to the prediction output.

UniLMv1 decoding similarly writes predictions as `MODEL_RECOVER_PATH.SPLIT` unless `--output_file` is provided. The legacy trace post-processor expects a `.trace.pickle` file generated from a decode run with beam search and score traces.

## Evaluation files

ROUGE-style evaluation scripts expect:

- prediction file: one generated summary/headline per line;
- gold file: one reference per line;
- matching line counts after any truncation or filtering;
- task-appropriate postprocessing such as CNN/DM truncation length or Gigaword digit normalization.

Before running ROUGE, perform simple validation:

```bash
wc -l predictions.txt references.target
head -n 3 predictions.txt
head -n 3 references.target
```

A line-count mismatch is usually a data split, subset, or decode-output-path error, not a ROUGE problem.
