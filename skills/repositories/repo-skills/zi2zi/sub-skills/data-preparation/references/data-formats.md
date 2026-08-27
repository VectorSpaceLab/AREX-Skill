# zi2zi data formats

## Charset inputs

`font2img.py` supports four symbolic charsets loaded from the repository's CJK
JSON data:

| Name | Intended characters |
| --- | --- |
| `CN` | Simplified Chinese GBK-style set |
| `CN_T` | Traditional Chinese GB2312-style set |
| `JP` | Japanese set |
| `KR` | Korean set |

A custom charset can be supplied as a text file path. The original script reads
the first line, decodes it as UTF-8 in Python 2, and uses the characters in that
line. Keep the file one line and avoid trailing explanatory text.

## Rendered paired image schema

The renderer creates one RGB JPG per character and style label:

```text
<label>_<zero-padded-index>.jpg
```

Example: `3_0042.jpg` means embedding/style label `3`, sample index `42`.

Each image is a horizontal concatenation of two square canvases:

```text
+--------------------+--------------------+
| target-style glyph | source-style glyph |
+--------------------+--------------------+
```

With the default `--canvas_size=256`, each output image is `512x256` pixels.
The model later splits the image at the midpoint, treats the left half as the
target glyph (`real_B`), and the right half as the source glyph (`real_A`).

Important rendering flags:

- `--char_size`: font point size used for both source and target glyphs.
- `--canvas_size`: square side length for each half of the pair.
- `--x_offset`, `--y_offset`: text draw offsets on the canvas.
- `--filter`: when true, sample the target font and skip recurring blank or
  missing-glyph hashes.
- `--shuffle`: randomize charset order before taking `--sample_count` glyphs.

## Pickled object schema

`package.py` scans a single directory of `*.jpg` files, sorts the filenames, and
writes two binary files:

```text
<save_dir>/train.obj
<save_dir>/val.obj
```

Each file is a stream of Python pickle records, not a single list. Each record
has the shape:

```python
(label, image_bytes)
```

- `label` is an integer parsed from the JPG basename before `_`.
- `image_bytes` is the raw JPG byte string.
- The record goes to validation if `random.random() < split_ratio`; otherwise
  it goes to training.

Because the original packager uses Python 2 `cPickle`, Python 3 readers should
load with byte-compatible handling. The bundled
[inspect_zi2zi_obj.py](../scripts/inspect_zi2zi_obj.py) handles this safely.

## Label and embedding consistency

Training uses `--embedding_num` to size the style embedding matrix. The largest
label in the data must be less than `embedding_num`. If labels are `0, 1, 2`,
then `--embedding_num=3` is the minimum. Use a larger value only if you reserve
future labels or match a checkpoint trained with more embeddings.

Do not change label meanings between preprocessing, training, and inference.
If label `4` represented a brush font during training, then `--embedding_ids=4`
at inference asks for that learned style.
