# WebDataset Format Notes

Read this before choosing a reader or writer workflow. WebDataset stores samples as groups of files inside tar shards.

## Shards

- A shard is a tar archive, often named with a numeric pattern such as `dataset-000000.tar`.
- Multiple shards are usually specified with brace expansion, for example `dataset-{000000..001281}.tar`.
- `SimpleShardList` also accepts `::`-separated URL lists.
- Directory-based shard lists expect a directory path ending in `/`.

## Samples inside a shard

Files with the same basename are grouped into one sample:

```text
abc123.jpg
abc123.json
abc123.cls
```

The reader emits a dictionary like:

```python
{
    "__key__": "abc123",
    "__url__": "... shard url ...",
    "jpg": b"...",
    "json": b"...",
    "cls": b"...",
}
```

After `decode()`, fields become typed values according to their extensions. Projection methods such as `to_tuple("jpg", "json")` or `rename(image="jpg;png", label="cls")` should come after the field names are known.

## Writer-side sample dicts

Writers expect a flat dictionary. The key `__key__` is required and should be stable. Payload field names become tar member extensions:

```python
{
    "__key__": "abc123",
    "txt.gz": "caption text",
    "cls": "7",
    "json": {"split": "train"},
    "npy": array,
    "png": image_array,
}
```

Metadata keys start with `_`; they are skipped unless writer configuration keeps metadata.

## Extension-driven encoding and decoding

Common extension meanings:

| Extension | Writer expectation | Reader result after `decode()` |
| --- | --- | --- |
| `txt`, `text`, `transcript` | string | string |
| `cls`, `class`, `index`, `id` | int-like string/value | integer |
| `json`, `jsn` | JSON-serializable object | parsed object |
| `npy` | NumPy array | NumPy array |
| `npz` | dict of NumPy arrays | dict of arrays |
| `ten`, `tb` | array-like or list of arrays | list of arrays |
| `jpg`, `png`, `ppm`, `tiff` | image array/PIL image | PIL/NumPy/torch image depending on decode spec |
| `pyd`, `pickle`, `pth` | pickle/torch payload | object when secure mode allows it |

Security note: secure mode blocks pickle and torch payload decoding. Use [io-caching-security](../sub-skills/io-caching-security/SKILL.md) when trust boundaries matter.

## Cross-links

- To read existing shards, use [reading-pipelines](../sub-skills/reading-pipelines/SKILL.md).
- To create shards, use [shard-writing](../sub-skills/shard-writing/SKILL.md).
- To configure opening/caching/security, use [io-caching-security](../sub-skills/io-caching-security/SKILL.md).
