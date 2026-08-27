# OpenNMT-py data formats and preparation reference

## Purpose

Read this when creating or repairing an OpenNMT-py corpus YAML, building vocabularies, choosing transforms/tokenizers, or handling source features. This reference is self-contained: it distills the public quickstart and FAQ intent, the data/vocab option validation rules, the vocabulary builder behavior, corpus YAML fixtures, and transform tests into operational guidance.

## Minimum parallel corpus YAML

A standard machine-translation or summarization config uses parallel source and target text files, one tokenized example per line on each side.

```yaml
save_data: run/example
src_vocab: run/example.vocab.src
tgt_vocab: run/example.vocab.tgt
overwrite: false

data:
  corpus_1:
    path_src: data/src-train.txt
    path_tgt: data/tgt-train.txt
    weight: 1
  valid:
    path_src: data/src-val.txt
    path_tgt: data/tgt-val.txt
```

Preparation command:

```bash
onmt_build_vocab -config CONFIG.yaml -n_sample 5000
```

Training later uses the same `src_vocab` and `tgt_vocab` paths after `onmt_build_vocab` has created them.

## Corpus mapping rules

- Top-level `data` must be a mapping. Each key is a corpus id; `valid` is the conventional validation corpus id.
- Every corpus entry must be a mapping with either `path_src` or `path_txt`.
- Parallel seq2seq corpora need both `path_src` and `path_tgt`.
- Source-only language-model style corpora omit `path_tgt`; OpenNMT-py treats target text as the source text for that corpus. Do not mix source-only and parallel corpora unless you have a clear model-task reason.
- `path_txt` is an alternate blockwise text input. It should not be mixed with `path_src` in the same corpus entry.
- `path_align` points to Pharaoh-style source-target alignments for alignment-aware training. Use it only with compatible transforms and alignment training options.
- `weight` controls how many examples are drawn sequentially from each training corpus before moving to the next corpus. If omitted on a non-`valid` corpus, OpenNMT-py defaults to `1` and logs a warning.
- Relative file paths are validated relative to the process working directory used to run the CLI. Run the CLI from the intended data root or use paths that are valid from that working directory.

## Vocabulary fields

`onmt_build_vocab` counts transformed corpus samples and writes plain-text vocabulary files. Each vocab line is either a token alone or a token followed by a tab and a count. The builder writes counts as:

```text
token_0	123
token_1	98
```

Important fields:

| Field | Build-vocab use | Training use |
| --- | --- | --- |
| `save_data` | Required output prefix for vocab-related and sample artifacts. | Required when dumping transformed samples or transforms. |
| `src_vocab` | Required output file for source or shared vocabulary. | Required existing input file. |
| `tgt_vocab` | Required unless `share_vocab: true`. | Required existing input file unless `share_vocab: true`. |
| `share_vocab` | Merges source and target counters and writes the shared vocab to `src_vocab`. | Reuses source vocab for target side; `tgt_vocab` is not required. |
| `overwrite` | Allows existing vocab/sample output files to be replaced. | Controls overwrites for dumped preparation artifacts. |
| `n_sample` | Must be `-1` for full corpus or greater than `1` for `onmt_build_vocab`; common quickstart value is `5000` or larger. | `0` means do not stop to dump samples; nonzero requires `save_data` and stops after writing samples. |

When `n_src_feats` is greater than zero, the vocabulary builder also writes feature vocab files named like `SRC_VOCAB_feat0`, `SRC_VOCAB_feat1`, and so on.

## Transforms

Transforms are applied on the fly when reading corpus examples. They can be set globally with top-level `transforms` or per corpus with `data.<corpus>.transforms`; a per-corpus list overrides the global default for that corpus.

Known built-in transform names in this OpenNMT-py generation:

- General filtering and augmentation: `filtertoolong`, `prefix`, `suffix`, `uppercase`, `normalize`, `clean`, `docify`, `fuzzymatch`, `inlinetags`, `terminology`.
- Tokenization and subwording: `onmt_tokenize`, `sentencepiece`, `bpe`.
- Noise and sampling: `bart`, `switchout`, `tokendrop`, `tokenmask`, `insert_mask_before_placeholder`.
- Source-feature propagation: `inferfeats`.

Common transform options:

- `filtertoolong`: set `src_seq_length` and `tgt_seq_length`; target filtering accounts for BOS/EOS overhead.
- `prefix`: set `src_prefix` and/or `tgt_prefix` inside each corpus using the transform.
- `suffix`: set `src_suffix` and/or `tgt_suffix` inside each corpus using the transform.
- `clean` and `normalize`: set language/script/ratio options when the default heuristics are too aggressive.
- `bart` and `switchout` require existing vocabularies for full warm-up; during vocabulary building, transforms that need vocabularies can be skipped or disabled.
- `tokendrop`, `tokenmask`, and similar stochastic transforms should be intentional in build-vocab mode because the counted samples may not match deterministic training text.

## Tokenizer and subword settings

There are three tokenizer-related transform families:

- `onmt_tokenize`: pyonmttok-based tokenization. Use `src_subword_type` and `tgt_subword_type` with values `none`, `sentencepiece`, or `bpe`; pass tokenizer options through `src_onmttok_kwargs` and `tgt_onmttok_kwargs` as dictionary strings.
- `sentencepiece`: loads `src_subword_model` and `tgt_subword_model` as SentencePiece models; `src_subword_nbest` and `tgt_subword_nbest` greater than `1` enable sampling during training.
- `bpe`: loads `src_subword_model` and `tgt_subword_model` as BPE code files; `src_subword_alpha` and `tgt_subword_alpha` act as dropout probabilities during training.

Shared tokenizer fields:

| Field | Meaning |
| --- | --- |
| `src_subword_model` | Source-side model path, or shared model path when sharing is intended. |
| `tgt_subword_model` | Target-side model path when not sharing the source-side model. |
| `src_subword_vocab`, `tgt_subword_vocab` | Optional vocabulary restriction files in `token<TAB>count` format. |
| `src_vocab_threshold`, `tgt_vocab_threshold` | Minimum count threshold for subword vocabulary restrictions. |
| `src_subword_nbest`, `tgt_subword_nbest` | SentencePiece sampling candidates. Use `1` for deterministic tokenization. |
| `src_subword_alpha`, `tgt_subword_alpha` | SentencePiece sampling smoothing or BPE dropout probability; expected range is `0` to `1`. |

If `learn_subwords: true` is used during vocabulary building, set the intended source subword type and output location carefully. The builder learns the subword model before counting vocab samples, then counts with transforms restored.

## Source features

Source features are encoded inline on the source side with the full-width separator `￨`:

```text
This￨A is￨B a￨B test￨A
```

Operational rules:

- Set `n_src_feats` to the number of feature channels.
- Set `src_feats_defaults` to one default value per feature channel, separated by `￨`, when some source tokens may omit features. Example for two channels: `src_feats_defaults: "0￨UNK"`.
- Every corpus must include `inferfeats` in its `transforms` when `n_src_feats` is greater than zero.
- Do not mix annotated and unannotated tokens on the same line unless defaults are configured and the line remains consistent after parsing.
- With subword tokenization, `inferfeats` propagates word-level features to generated subwords. Use `reversible_tokenization: joiner` for joiner-marked tokenization or `reversible_tokenization: spacer` for spacer-marked tokenization.

Minimal feature-aware YAML:

```yaml
src_vocab: run/feat.vocab.src
tgt_vocab: run/feat.vocab.tgt
save_data: run/feat
n_src_feats: 1
src_feats_defaults: "0"

data:
  corpus_1:
    path_src: data/src-train-with-feats.txt
    path_tgt: data/tgt-train.txt
    transforms: [inferfeats]
  corpus_2:
    path_src: data/src-train.txt
    path_tgt: data/tgt-train.txt
    transforms: [inferfeats]
  valid:
    path_src: data/src-val-with-feats.txt
    path_tgt: data/tgt-val.txt
    transforms: [inferfeats]
```

## Alignment-aware data

Alignment files are per-corpus `path_align` files in Pharaoh source-target index format, such as `0-0 1-1 2-2`. When `lambda_align` is greater than zero, OpenNMT-py requires alignment files for the corpora involved in training.

Alignment constraints to remember:

- Alignment learning is not compatible with on-the-fly tokenization transforms (`sentencepiece`, `bpe`, `onmt_tokenize`) because tokenization changes positions.
- Alignment learning is not compatible with token-deleting or token-adding transforms such as `tokendrop`, `prefix`, and `bart` in the validated path.
- Keep blank lines out of alignment files.

## Bundled validation workflow

Use the validator from this sub-skill when a config is unclear:

```bash
python scripts/validate_data_config.py --config CONFIG.yaml --root . --mode build-vocab
```

What it catches before the OpenNMT-py CLI starts:

- YAML parse failures and a non-mapping top-level `data` field.
- Missing or invalid corpus path fields.
- Missing vocab fields for build-vocab or train modes.
- Relative paths that do not exist under the chosen root.
- Invalid `n_sample`, `share_vocab`, `overwrite`, and feature-default combinations.
- Unknown transforms, tokenizer option ranges, and likely tokenizer model path omissions.
- Source-feature annotation count mismatches in sampled source lines.
- Alignment path and transform compatibility problems.

## Safe command pattern

1. Check the YAML in generic mode while drafting:

   ```bash
   python scripts/validate_data_config.py --config CONFIG.yaml --root . --mode generic
   ```

2. Check for vocabulary building:

   ```bash
   python scripts/validate_data_config.py --config CONFIG.yaml --root . --mode build-vocab --strict
   onmt_build_vocab -config CONFIG.yaml -n_sample 5000
   ```

3. Check for training after vocab files exist:

   ```bash
   python scripts/validate_data_config.py --config CONFIG.yaml --root . --mode train --strict
   onmt_train -config CONFIG.yaml
   ```
