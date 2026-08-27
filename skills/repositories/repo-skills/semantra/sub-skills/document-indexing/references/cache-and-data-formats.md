# Cache and Data Formats

## Purpose

Read this when a task requires interpreting Semantra cache files, choosing
window strings, understanding PDF-derived artifacts, or validating that a cache
group is complete.

## Cache naming facts

Semantra computes a truncated MD5 hash of each input file and a separate config
hash from the selected model configuration. The package constant for hash
length is `24` hexadecimal characters.

The core filenames use these patterns:

| Artifact | Pattern | Meaning |
| --- | --- | --- |
| Converted PDF text | `<md5>.pdf.txt` | Text extracted from a PDF input. |
| PDF positions | `<md5>.pdf.positions.json` | Per-page character offsets and page sizes for PDF viewer navigation. |
| Token chunks | `<md5>.<config_hash>.tokens.json` | JSON list of text chunks aligned to model tokens. |
| Full config | `<md5>.<config_hash>.config.json` | JSON metadata for the processed file/model/window configuration. |
| Embeddings | `<md5>.<config_hash>.<size>_<offset>_<rewind>.embeddings` | Binary `float32` embedding matrix for one window setting. |
| Annoy index | `<md5>.<config_hash>.<size>_<offset>_<rewind>.<trees>t.annoy` | Approximate nearest-neighbor index for one embedding matrix. |

Use [inspect_semantra_cache.py](../scripts/inspect_semantra_cache.py) to group
these artifacts without importing Semantra.

## Config JSON fields

Semantra's config JSON includes both model settings and run metadata. Important
fields for diagnosis include:

- `filename`, `base_filename`, and `md5` identify the input.
- `model_type`, `model_name`, tokenizer or token pre/post fields identify the
  embedding model.
- `num_dimensions` is the embedding width expected by binary files and Annoy
  indexes.
- `windows` is the list of `(size, offset, rewind)` tuples used for processing.
- `num_tokens`, `num_embeddings`, and `num_embedding_tokens` estimate work and
  validate file sizes.
- `use_annoy` and `num_annoy_trees` explain whether Annoy indexes should exist.
- `semantra_version` records the package version that produced the cache group.
- `encoding` appears only when the selected text encoding differs from UTF-8.

If an embedding file exists but its size is not a multiple of
`num_dimensions * 4`, treat it as incomplete or corrupt and rebuild the group.

## Window tuple behavior

The CLI parser accepts comma-separated specs:

```text
<size>
<size>_<offset>
<size>_<offset>_<rewind>
```

Examples:

| Window string | Parsed tuple | Notes |
| --- | --- | --- |
| `128` | `(128, 0, 0)` | Non-overlapping chunks. |
| `128_0_16` | `(128, 0, 16)` | Default, 16-token overlap. |
| `64_8` | `(64, 8, 0)` | An initial 8-token offset window, then 64-token chunks. |
| `128_0_16,256_0_32` | two tuples | Both are processed; the first is used by query routes in this Semantra version. |

For a document of 10 tokens and window `(4, 0, 1)`, Semantra produces offsets
`[0,4]`, `[3,7]`, and `[6,10]`, embedding 12 token positions because overlap is
counted in the work estimate.

## Text and PDF content objects

For text inputs, Semantra returns a content object with:

- `rawtext`: the decoded text;
- `filename`: the original filename;
- `filetype`: `text`.

For PDF inputs, the PDF content object has:

- `rawtext`: text extracted from pages joined with a page separator;
- `positions`: one record per page containing `char_index`, `page_width`, and
  `page_height`;
- `get_page_image_pil(page_number, scale)`: render a page image;
- `get_page_chars(page_number)`: return text characters and boxes;
- `filetype`: `pdf`.

These PDF methods are used by the web API and UI. If PDF text search succeeds
but page navigation fails, inspect the positions and page-char routes under
[interactive-search](../../interactive-search/SKILL.md).

## Document object fields

After processing, Semantra's `Document` object records:

- original filename and truncated content hash;
- the cache directory and base filename;
- the full config dictionary;
- embeddings filenames and optional Annoy filenames;
- window tuples and offsets;
- token JSON filename;
- embedding dimension count;
- text encoding.

The object's `text_chunks`, `embeddings`, and `embedding_db` properties load
cache artifacts lazily. `embedding_db` is valid only when Annoy is enabled.

## Safe cache inspection rules

- Inspect read-only first; do not delete the entire cache unless the user has
  accepted losing all processed document work.
- Group files by `<md5>.<config_hash>` before diagnosing a document.
- Rebuild with `--force` when artifacts are incomplete or inconsistent.
- Keep separate cache directories for materially different experiments when you
  want easy comparison.
- Do not treat cache artifacts as portable indexes across different Semantra,
  model, tokenizer, or dependency versions unless the config JSON confirms the
  match.
