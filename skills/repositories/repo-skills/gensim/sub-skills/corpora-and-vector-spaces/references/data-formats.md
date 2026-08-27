# Corpus Data Formats

## Choosing a format

| Format/class | Best use | Notes |
| --- | --- | --- |
| `MmCorpus` | General sparse matrix persistence for Gensim workflows. | Supports lazy iteration and optional index files; common default for experiments. |
| `SvmLightCorpus` | Interoperability with SVMlight/liblinear-style sparse features. | Labels may appear in source data; confirm if labels matter to the downstream task. |
| `BleiCorpus` | Blei LDA-C compatible topic-model corpora. | Usually paired with a vocabulary file. |
| `LowCorpus` | GibbsLDA++/Low style corpora. | Use only when downstream tooling expects that format. |
| `UciCorpus` | UCI bag-of-words datasets. | Common for benchmark corpora. |
| `MalletCorpus` | Mallet-compatible input/output. | Use for Mallet interop rather than native Gensim-only workflows. |
| `TextCorpus`/`TextDirectoryCorpus` | Plain text files or directory trees. | Converts text to BoW using a dictionary and preprocessing pipeline. |
| `WikiCorpus` | Compressed MediaWiki XML dumps. | Full dumps are expensive; test on tiny samples first. |

## Sparse vector shape

Gensim sparse vectors are lists of `(feature_id, value)` tuples. Missing ids imply
zero. Feature ids come from the dictionary, so corpus/model/index artifacts must
be kept with their dictionary or an exact saved copy.

## Compression and sidecar files

- Many corpus loaders can read `.gz` or `.bz2` through Gensim/smart_open helpers,
  but compression affects indexing and random access.
- Matrix Market serialization may create an index sidecar. Keep it with the data
  when random access matters.
- Do not rename corpus files without moving the sidecar index and vocabulary files
  needed by that format.

## Metadata

Some corpus classes can carry metadata such as document ids or titles. If a task
requires mapping similarity results back to documents, persist a separate
id/title table or use a corpus class/serialization mode that preserves metadata.
Never assume a similarity result index is meaningful without a document-id map.

## Tiny fixture pattern

For verification or demos, create small local files instead of using network data:

```python
from pathlib import Path
from gensim import corpora

root = Path("texts")
root.mkdir()
(root / "a.txt").write_text("human computer\n", encoding="utf-8")
(root / "b.txt").write_text("graph trees\n", encoding="utf-8")
```

Then build tokenized documents or use `TextDirectoryCorpus` with the same
preprocessing used in production.
