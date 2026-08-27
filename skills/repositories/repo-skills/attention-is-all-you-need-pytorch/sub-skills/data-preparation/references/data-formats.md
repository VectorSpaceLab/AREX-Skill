# Data Formats and Contracts

## Purpose

Read this reference when deciding whether a preprocessing artifact can be used
for training or translation. It summarizes the data contracts produced by the
non-BPE Multi30k path and the WIP BPE path, plus the token constants consumed by
training and translation.

## Token constants

The repository defines these token strings and expects them to exist in the
relevant torchtext vocabularies:

| Constant | Token string | Role |
| --- | --- | --- |
| `PAD_WORD` | `<blank>` | Padding token. Training reads its index as `src_pad_idx` and/or `trg_pad_idx`. |
| `UNK_WORD` | `<unk>` | Unknown token. Translation uses the source field's `unk_token` index for missing words. |
| `BOS_WORD` | `<s>` | Target beginning-of-sentence token for beam search translation. |
| `EOS_WORD` | `</s>` | Target end-of-sentence token for beam search translation. |

The preprocessing `Field` objects set `pad_token=<blank>`, `init_token=<s>`, and
`eos_token=</s>`. A pickle is not ready for training or translation if these
strings are absent from the appropriate `Field.vocab.stoi` tables.

## Non-BPE Multi30k pickle

The default non-BPE path writes a dill pickle containing a dictionary with this
shape:

```text
{
  "settings": argparse.Namespace(...),
  "vocab": {
    "src": torchtext.data.Field,
    "trg": torchtext.data.Field
  },
  "train": [torchtext.data.Example, ...],
  "valid": [torchtext.data.Example, ...],
  "test":  [torchtext.data.Example, ...]
}
```

### `settings`

Important fields saved in `settings` include:

| Field | Meaning |
| --- | --- |
| `lang_src`, `lang_trg` | spaCy language aliases used for tokenization. Default documented route is German/English. |
| `save_data` | Output pickle path originally requested by the caller. |
| `max_len` | Maximum source and target length allowed before examples are filtered. |
| `min_word_count` | Minimum frequency for `Field.build_vocab`. |
| `keep_case` | Whether text was lowercased by torchtext fields. |
| `share_vocab` | Whether source and target vocabularies were merged and made identical. |

### `vocab.src` and `vocab.trg`

Each value is a legacy torchtext `Field` with a built `vocab` object. Training
uses:

```text
src_pad_idx = data["vocab"]["src"].vocab.stoi["<blank>"]
trg_pad_idx = data["vocab"]["trg"].vocab.stoi["<blank>"]
src_vocab_size = len(data["vocab"]["src"].vocab)
trg_vocab_size = len(data["vocab"]["trg"].vocab)
```

If source/target embedding sharing is enabled during training, the source and
target `stoi` tables must be identical. The documented preprocessing command
uses `-share_vocab` for this reason.

Translation uses the non-BPE pickle only. It reads:

```text
SRC, TRG = data["vocab"]["src"], data["vocab"]["trg"]
src_pad_idx = SRC.vocab.stoi["<blank>"]
trg_pad_idx = TRG.vocab.stoi["<blank>"]
trg_bos_idx = TRG.vocab.stoi["<s>"]
trg_eos_idx = TRG.vocab.stoi["</s>"]
```

### Split examples

The `train`, `valid`, and `test` lists contain legacy torchtext `Example`
objects. Each example should expose `src` and `trg` token sequences. Training
wraps `train` and `valid` in `torchtext.data.Dataset`; translation wraps `test`
in a `Dataset` and writes one decoded line per test example.

## BPE shared-field pickle

The WIP BPE preprocessing path writes a different pickle shape:

```text
{
  "settings": argparse.Namespace(...),
  "vocab": torchtext.data.Field
}
```

There are no embedded `train`, `valid`, or `test` example lists. Training must
also receive encoded parallel text prefixes via `-train_path` and `-val_path`.
For a prefix `./bpe_deen/deen-train`, torchtext expects these files:

```text
./bpe_deen/deen-train.src
./bpe_deen/deen-train.trg
```

Training uses the shared field this way:

```text
field = data["vocab"]
fields = (field, field)
src_pad_idx = trg_pad_idx = field.vocab.stoi["<blank>"]
src_vocab_size = trg_vocab_size = len(field.vocab)
```

The BPE training loader requires `-embs_share_weight`; it raises if source and
target embeddings are not shared. This matches the shared field contract.

## Encoded BPE text files

BPE encoding is whitespace-token based. For each word, all non-final subword
units receive the separator marker, default `@@`. Example shape:

```text
low@@ er new@@ est
```

The BPE field tokenizes encoded files with `str.split`, lowercases tokens, and
adds the same special tokens (`<blank>`, `<s>`, `</s>`) as the non-BPE fields.

## Schema identification with the bundled inspector

Use the bundled inspector for trusted preprocessing artifacts:

```bash
python sub-skills/data-preparation/scripts/inspect_preprocessed_pickle.py --pickle artifact.pkl --trust-pickle --strict
```

Classification rules used by the helper:

| Classification | Required signs | Ready for |
| --- | --- | --- |
| `non_bpe_multi30k` | `vocab` is a dict with `src` and `trg`; `train`, `valid`, and `test` keys exist. | Non-BPE training and non-BPE translation, subject to special-token and vocab-sharing checks. |
| `bpe_shared_field` | `vocab` is one field-like object; embedded split keys are absent. | BPE training only, with encoded `-train_path` and `-val_path` sidecar files. |
| `unknown` | Missing or mixed keys. | Do not train until the mismatch is explained. |

Do not treat a BPE shared-field pickle as a non-BPE translation pickle. It lacks
`data["vocab"]["src"]`, `data["vocab"]["trg"]`, and `data["test"]`, so the
translation loader will fail before beam search begins.
