# Data formats for DALL-E training

## Image-text folder

The package data helper recursively matches image and text files by file stem. Supported image extensions are:

- `.png`
- `.jpg`
- `.jpeg`
- `.bmp`

For each matched stem, the `.txt` file may contain multiple non-empty captions separated by newlines. One caption is sampled during batch creation.

Example:

```text
image-and-text-data/
  cat.png
  cat.txt
  nested/
    dog.jpg
    dog.txt
```

`cat.txt`:

```text
A black and white cat curled up next to the fireplace
A cat sleeping next to a warm fireplace
```

Validation:

```bash
python scripts/validate_image_text_folder.py /path/to/image-and-text-data --strict
```

Common issues:

- `cat.png` and `cat_caption.txt` do not pair because stems differ.
- empty `.txt` files produce skip/retry behavior and can hide data quality problems;
- duplicate stems in different directories can collapse into one key in the source helper because it maps by `Path.stem`, not relative path;
- unsupported image extensions are ignored.

## WebDataset

The training helper accepts `--wds <image_key>,<caption_key>`. The same `--image_text_folder` argument then points to one of:

- a single `.tar` or `.tar.gz` file;
- a directory containing tar/shard files;
- an HTTP/HTTPS brace pattern or URL, streamed through `curl`;
- a `gs://` path, streamed through `gsutil`.

Examples:

```bash
python train_dalle.py --wds img,cap --image_text_folder /data/shards
python train_dalle.py --wds jpg,json --image_text_folder 'https://host/dataset-{000000..000554}.tar'
```

The source helper filters out samples missing either selected key. Remote streams are network side effects; ask before running.

## Tokenized text shape

Text tensors passed to `DALLE` must have shape `(batch, text_seq_len)`. Tokenizers pad with `0`; the model later remaps padding to unique position tokens internally.

If a caption exceeds `text_seq_len`:

- without truncation, tokenizers raise a runtime error;
- with `--truncate_captions`, captions are truncated to context length.

## Image tensor shape

Raw images passed to `DALLE.forward` must match the VAE:

```text
(batch, channels, vae.image_size, vae.image_size)
```

The default image-text data helper converts to RGB or RGBA, applies random resized crop to `vae.image_size`, and converts to tensor.
