# RWKV training data formats

## JSONL input

The repository's `make_data` utility expects one JSON object per non-empty line
with a string `text` field. Blank lines are ignored. The source implementation
shuffles the retained lines once per requested repetition and appends an end of
document token (`0`) to every encoded item.

Minimal input:

```jsonl
{"text":"first training example"}
{"text":"second training example"}
```

Use the bundled converter with an explicit output directory:

```bash
python scripts/convert_jsonl_to_rwkv_binidx.py \
  --input corpus.jsonl \
  --output-prefix work/minipile-small \
  --repeat 3 \
  --ctx-len 128
```

The helper accepts `--vocab-file` for a checkout's `rwkv_vocab_v20230424.txt`.
If omitted, it tries the installed `rwkv` package's bundled vocabulary. It does
not download a tokenizer or dataset.

## `.bin` and `.idx` pair

RWKV's mmap dataset uses a prefix rather than a single file:

- `<prefix>.bin` stores flat token ids, normally `uint16` for a 65,536-token
  vocabulary.
- `<prefix>.idx` starts with the `MMIDIDX` header and stores dtype code, item
  sizes, byte pointers, and document indices.
- The training command receives the prefix without `.bin`/`.idx` when using
  `--data_type binidx`.

The `.bin` and `.idx` files must be copied or moved together. A valid index with
an absent or differently sized `.bin` is an immediate data error, not a model
error.

## `magic_prime`

The current training dataset samples positions using a prime that is congruent
to `2 mod 3`. For a token count `N` and context length `T`, search downward
from `floor(N/T) - 1` until finding a prime `p` with `p % 3 == 2`. The source
trainer also expects the candidate to be close to the number of available
context slots; it rejects a value that is too large or not prime.

Run:

```bash
python scripts/compute_magic_prime.py \
  --data-prefix work/minipile-small \
  --ctx-len 128
```

Use the printed `--my_exit_tokens`/`--magic_prime` pair in the same training
command. Recompute when the corpus, repetition count, or context length changes.

## Vocabulary and end-of-document behavior

The v20230424 tokenizer is a byte-level trie vocabulary. The repository's data
utility checks that `decode(encode(text)) == text` before writing a document and
uses token `0` as the end-of-document marker. Do not silently replace it with a
BOS/EOS id from a different tokenizer. If a tokenizer round-trip fails, inspect
encoding, invalid Unicode, and the vocabulary file before creating the dataset.

## Dataset checks before training

- Confirm the prefix is readable from the intended working directory.
- Confirm `.bin` size is divisible by the dtype width in `.idx`.
- Read both the first and last indexed items; each should have at least two
  tokens for next-token training.
- Confirm `token_count // ctx_len - 1` is large enough to yield a valid prime.
- Set `vocab_size` to the tokenizer/model family: the v20230424 vocabulary is
  normally 65,536, while older Pile checkpoints may use 50,277 or 50,304.
- Keep data preparation and model output directories separate so a stage-2
  checkpoint search cannot mistake dataset artifacts for weights.
