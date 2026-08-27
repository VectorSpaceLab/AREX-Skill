# Data Preparation Workflows

## Purpose

This reference gives future agents copyable data-preparation workflows without
requiring them to reopen the repository source. Use it for Multi30k
preprocessing, BPE preparation planning, pickle inspection, and local BPE
experiments.

## Default non-BPE Multi30k workflow

The repository's default preprocessing entry point uses the non-BPE flow. It is
the path documented for WMT'16 Multimodal Translation / Multi30k German-English.

### Prerequisites

- Python environment compatible with the legacy stack verified for this repo:
  Python 3.8-era source, torch 1.13.1, torchtext 0.6.0, spaCy 2.3.5, and dill
  0.3.3.
- spaCy language models for the requested language pair. For the documented
  German-English example:

```bash
python -m spacy download en
python -m spacy download de
```

With modern spaCy packaging, `en`/`de` may no longer be accepted aliases. If the
short aliases fail, install spaCy-2-compatible model packages or create the
alias links expected by `spacy.load("en")` and `spacy.load("de")`.

### Command

From a checkout that contains the repository preprocessing entry point, run:

```bash
python preprocess.py -lang_src de -lang_trg en -share_vocab -save_data m30k_deen_shr.pkl
```

Important options in the non-BPE flow:

| Option | Default / behavior | Notes |
| --- | --- | --- |
| `-lang_src`, `-lang_trg` | required, spaCy-supported language codes | Without custom files, the code asserts that the pair is exactly German/English in either order. |
| `-save_data` | required output pickle path | The pickle is consumed by training and non-BPE translation. |
| `-max_len` | `100` | Examples with source or target length greater than this value are filtered before vocab building. |
| `-min_word_count` | `3` | Passed to `Field.build_vocab(..., min_freq=MIN_FREQ)` for source and target vocabularies. |
| `-keep_case` | off | By default, source and target `Field` objects lowercase tokens. |
| `-share_vocab` | off | When enabled, target vocabulary is expanded with source vocabulary entries, then source and target share the same `stoi`/`itos` tables. Required when training with source/target embedding sharing. |
| `-data_src`, `-data_trg` | accepted by parser but rejected | The default implementation asserts that custom data input is not supported. |

### What it writes

The non-BPE pickle has the schema described in
[data-formats.md](data-formats.md#non-bpe-multi30k-pickle): `settings`,
`vocab.src`, `vocab.trg`, and embedded `train`/`valid`/`test` example lists.

After preprocessing, inspect the artifact before training or translation:

```bash
python sub-skills/data-preparation/scripts/inspect_preprocessed_pickle.py \
  --pickle m30k_deen_shr.pkl \
  --trust-pickle \
  --strict
```

The helper reports whether the pickle is non-BPE or BPE, checks special tokens,
counts embedded examples when present, and warns about schema mismatches.

## WIP WMT BPE workflow

The repository also contains a WMT-style BPE path, but its README marks BPE as
not fully tested and says the preprocessing entry point must be switched from
the default non-BPE flow to the BPE flow before running it. Treat this as an
experimental preparation route.

### Command shape

After selecting the BPE preprocessing entry point in the repository script, the
README command shape is:

```bash
python preprocess.py \
  -raw_dir /tmp/raw_deen \
  -data_dir ./bpe_deen \
  -save_data bpe_vocab.pkl \
  -codes codes.txt \
  -prefix deen
```

Additional BPE options:

| Option | Default / behavior | Notes |
| --- | --- | --- |
| `-raw_dir` | required | Target directory for extracted raw corpora. The code downloads WMT train/dev/test archives if expected files are missing. |
| `-data_dir` | required | Directory for BPE codes, encoded split files, and saved field pickle. |
| `-codes` | required filename | Saved under `data_dir`; learned from combined training source and target files if missing. |
| `-save_data` | required filename | Saved under `data_dir`; contains only `settings` and one shared `Field`. |
| `-prefix` | required | Produces encoded prefixes such as `<prefix>-train.src` and `<prefix>-train.trg`. |
| `-max_len` | `100` | Used while building the shared field vocabulary from encoded training data. |
| `--symbols` / `-s` | `32000` | Number of BPE merge operations to learn. |
| `--min-frequency` | `6` | Stop learning merges when no pair reaches this count. |
| `--separator` | `@@` | Marker appended to non-final subword units during encoding. |
| `--dict-input` | off | Interpret BPE learning input lines as `word count` pairs. |
| `--total-symbols` / `-t` | off | Adjust merge count by the number of initial symbols. |

### Produced files and training inputs

The BPE path writes:

- `data_dir/codes.txt` or the chosen code filename.
- Encoded parallel text prefixes such as `data_dir/deen-train.src`,
  `data_dir/deen-train.trg`, `data_dir/deen-val.src`, and `data_dir/deen-val.trg`.
- `data_dir/bpe_vocab.pkl` containing `settings` and a single shared torchtext
  `Field` under `vocab`.

Training consumes the BPE outputs with both the shared-field pickle and encoded
parallel prefixes:

```bash
python train.py \
  -data_pkl ./bpe_deen/bpe_vocab.pkl \
  -train_path ./bpe_deen/deen-train \
  -val_path ./bpe_deen/deen-val \
  -embs_share_weight \
  -proj_share_weight \
  -label_smoothing \
  -output_dir output
```

Do not route BPE translation as ready. The translation path contains TODOs for
loading BPE vocabulary and decoding generated subwords.

### Caveats

- This path downloads external WMT archives by default; it is unsuitable for
  offline or no-network workflows unless the expected raw files are already
  staged exactly as the code searches for them.
- Existing encoded files may be overwritten: the encoder prints a skip message
  if both output files exist, but the implementation still proceeds to encode.
  Keep BPE experiments in a scratch directory.
- The BPE pickle is not a drop-in replacement for the non-BPE translation
  pickle because it does not embed `train`/`valid`/`test` example lists or a
  source/target `vocab` dictionary.

## Tiny local BPE demonstration

For a no-network demonstration of the BPE learning and application behavior,
use the bundled helper:

```bash
python sub-skills/data-preparation/scripts/bpe_tiny_demo.py
python sub-skills/data-preparation/scripts/bpe_tiny_demo.py --symbols 8 --min-frequency 2 --json
```

To learn codes from local text files and optionally write `codes.txt` and
`encoded.txt` to a scratch output directory:

```bash
python sub-skills/data-preparation/scripts/bpe_tiny_demo.py \
  --corpus tiny.de tiny.en \
  --encode "low lower lowest" "newer widest" \
  --symbols 20 \
  --write-dir /tmp/tiny-bpe-demo
```

This helper intentionally does not download WMT data, create torchtext fields,
or write training pickles. Use it to understand and debug BPE merge behavior
before attempting the repository's WIP BPE pipeline.

## Pickle inspection workflow

Pickle loading can execute arbitrary code. The bundled inspector therefore
refuses to unpickle unless the caller passes `--trust-pickle`.

```bash
python sub-skills/data-preparation/scripts/inspect_preprocessed_pickle.py --pickle artifact.pkl
# exits with an explanation and a file digest, without unpickling

python sub-skills/data-preparation/scripts/inspect_preprocessed_pickle.py --pickle artifact.pkl --trust-pickle --strict
```

For BPE artifacts, also provide encoded-data prefixes so the inspector can check
that the sidecar text files expected by training are present:

```bash
python sub-skills/data-preparation/scripts/inspect_preprocessed_pickle.py \
  --pickle ./bpe_deen/bpe_vocab.pkl \
  --trust-pickle \
  --train-path ./bpe_deen/deen-train \
  --val-path ./bpe_deen/deen-val \
  --strict
```
