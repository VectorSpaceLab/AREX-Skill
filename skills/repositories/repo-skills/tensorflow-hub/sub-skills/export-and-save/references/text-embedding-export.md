# Text embedding SavedModel export

This workflow creates a TF2 `SavedModel` text embedder from a whitespace-delimited token/vector file. It is distilled from the current TensorFlow Hub TF2 text embedding exporter behavior and is bundled here as a self-contained helper at [../scripts/export_text_embeddings_v2.py](../scripts/export_text_embeddings_v2.py).

The result is a plain TF2 `SavedModel` that can be validated with `tensorflow_hub.load(export_path)` and usually wrapped as `tensorflow_hub.KerasLayer(export_path, input_shape=[], dtype=tf.string, output_shape=[embedding_dim])`.

## Input file format

Each usable line contains one token followed by one or more numeric vector components:

```text
cat 1.11 2.56 3.45
dog 1.0 2.0 3.0
mouse 0.5 0.1 0.6
```

Rules:

- Splitting is whitespace-based; tokens themselves cannot contain whitespace.
- All vector rows must have the same embedding dimension.
- Vector values are parsed as floats and exported as `tf.float32`.
- Blank usable lines are invalid; remove them or ignore them with the header-skip flag.
- Header lines such as `400000 300` are not embeddings. Skip them with `--num-lines-to-ignore 1`.
- `--num-lines-to-use N` limits the number of usable rows after skipped lines.

## Bundled CLI

```bash
python scripts/export_text_embeddings_v2.py \
  --embedding-file embeddings.txt \
  --export-path exported_text_embedding \
  --num-oov-buckets 1 \
  --num-lines-to-ignore 0 \
  --verify \
  --sample-text "cat dog" --sample-text "lizard. dog" ""
```

Flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--embedding-file` | required | Token/vector text file to read. |
| `--export-path` | required | New or empty directory where `tf.saved_model.save(...)` writes the `SavedModel`. |
| `--num-oov-buckets` | `1` | Number of out-of-vocabulary buckets appended to the lookup table. |
| `--num-lines-to-ignore` | `0` | Number of initial lines to skip before parsing embeddings. |
| `--num-lines-to-use` | unset | Maximum number of usable embedding rows after skipped lines. |
| `--verify` | off | Reload the exported model with `tensorflow_hub.load(...)` and print sample outputs. |
| `--sample-text` | derived samples | Repeatable; each occurrence accepts one or more sample strings. Quote strings that contain spaces. |

The script refuses to write into a non-empty existing output directory. Choose a fresh path or empty the directory intentionally before rerunning.

## Exported model behavior

The bundled exporter creates a TensorFlow trackable object with:

- a `StaticVocabularyTable` initialized from a saved vocabulary asset;
- an embedding variable containing the input vectors plus zero-valued OOV rows;
- a callable `__call__(sentences)` function with input signature `TensorSpec([None], tf.string)`;
- minimal text preprocessing: punctuation removal, reshape to a flat batch, split on spaces, fill empty rows, reset sparse shape, table lookup, and `tf.nn.safe_embedding_lookup_sparse(..., combiner="sqrtn")`.

Output shape is `[batch_size, embedding_dim]`. For known tokens, the row is the token vector. For multi-token strings, vectors are combined with the `sqrtn` combiner. For all-empty inputs, the output is a zero vector per input row.

## OOV buckets

`--num-oov-buckets` appends zero vectors to the embedding matrix. Unknown tokens hash into those buckets through `StaticVocabularyTable`.

Implications:

- With the default zero OOV vectors, a sentence containing only unknown tokens returns zeros.
- A sentence containing known and unknown tokens combines known vectors with zero OOV rows, so unknown tokens can still affect the `sqrtn` normalization denominator.
- Multiple OOV buckets are mostly useful if the exported variable will later be fine-tuned; initially all OOV rows are zero.
- Setting zero OOV buckets can make unknown-token behavior more brittle. Keep one or more OOV buckets unless there is a reason to reject unknown tokens.

## Header skip and row limit

Use `--num-lines-to-ignore` for metadata headers and `--num-lines-to-use` for smoke-sized exports.

Example with a header and a two-token limit:

```text
3 3
cat 1.11 2.56 3.45
dog 1.0 2.0 3.0
mouse 0.5 0.1 0.6
```

```bash
python scripts/export_text_embeddings_v2.py \
  --embedding-file tiny.txt \
  --export-path tiny_export \
  --num-lines-to-ignore 1 \
  --num-lines-to-use 2 \
  --verify \
  --sample-text cat dog mouse
```

Expected behavior: `cat` and `dog` use stored vectors; `mouse` is treated as OOV because it was beyond the row limit.

## Empty input behavior

The exporter intentionally handles empty strings and all-empty batches:

```python
import tensorflow as tf
import tensorflow_hub as hub

model = hub.load("exported_text_embedding")
print(model(tf.constant(["", "", ""])).numpy())
```

Each empty row should produce an all-zero embedding. Empty leading rows should not shift or drop later non-empty rows.

## Verification expectations

After export, run at least these checks:

1. `tensorflow_hub.load(export_path)` succeeds.
2. Calling the loaded object with `tf.constant([...], dtype=tf.string)` returns a dense rank-2 float tensor.
3. Known single tokens reproduce the original vectors within float tolerance.
4. Multi-token examples combine vectors with `sqrtn`; punctuation such as `"cat? dog"` is removed before splitting.
5. OOV-only and empty inputs return zero vectors with the default zero OOV rows.
6. If `--num-lines-to-ignore` or `--num-lines-to-use` is used, skipped or excluded tokens behave as OOV.

If verification is for Keras integration rather than low-level loading, validate the result with `tensorflow_hub.KerasLayer` and route detailed wrapper issues through the sibling `load-and-wrap` sub-skill via the TensorFlow Hub root router.
