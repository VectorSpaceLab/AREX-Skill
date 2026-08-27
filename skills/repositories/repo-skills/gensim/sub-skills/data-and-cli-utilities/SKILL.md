---
name: data-and-cli-utilities
description: "Guides Gensim downloader, cache, vector conversion, package
  diagnostics, and Wikipedia utility scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 2.1
---

# Data and CLI Utilities

Use this sub-skill when the task is about Gensim's downloader/cache API,
package-provided conversion scripts, vector export formats, package diagnostics,
or Wikipedia dump helpers.

## Read when

- A user asks to list, inspect, or download resources from `gensim.downloader` or
  gensim-data.
- The task mentions `GENSIM_DATA_DIR`, cache planning, `return_path=True`, or
  avoiding large downloads.
- A vector file must be converted between GloVe, word2vec, and TensorBoard TSV
  formats.
- A task needs `segment_wiki`, `make_wikicorpus`, `make_wiki_online`, or package
  info style diagnostics.

## Quick workflow

1. Use `gensim.downloader.info()` before downloading anything.
2. Set `GENSIM_DATA_DIR` deliberately for large resources or shared caches.
3. Use `api.load(name, return_path=True)` when a file path is enough.
4. Use bundled conversion helpers for tiny/local vector files before scaling up.
5. Treat full Wikipedia dump conversion and benchmarking scripts as expensive
   planned jobs, not smoke tests.

Read [`references/downloader-and-data.md`](references/downloader-and-data.md),
[`references/cli-reference.md`](references/cli-reference.md), and
[`references/wiki-workflows.md`](references/wiki-workflows.md) for concrete
commands and safety notes.

## API and CLI anchors

- `gensim.downloader.info(name=None, show_only_latest=True, name_only=False)`.
- `gensim.downloader.load(name, return_path=False)`.
- CLI: `python -m gensim.downloader -i [data_name]` and
  `python -m gensim.downloader -d data_name`.
- `glove2word2vec(glove_input_file, word2vec_output_file)`.
- `word2vec2tensor(word2vec_model_path, tensor_filename, binary=False)`.
- `segment_all_articles(file_path, min_article_character=200, workers=None,
  include_interlinks=False)`.

## Bundled helpers

- [`scripts/convert_glove_to_word2vec.py`](scripts/convert_glove_to_word2vec.py): safe wrapper around GloVe-to-word2vec text conversion.
- [`scripts/word2vec_to_tensor_tsv.py`](scripts/word2vec_to_tensor_tsv.py): safe wrapper for TensorBoard Projector TSV export.
- [`scripts/segment_wiki_tiny.py`](scripts/segment_wiki_tiny.py): tiny fixture/dry helper for Wikipedia segmentation workflows.

## Boundaries and routing

- Route training Word2Vec/FastText/Doc2Vec models to
  [`../embeddings-and-phrases/SKILL.md`](../embeddings-and-phrases/SKILL.md).
- Route `WikiCorpus` iteration and corpus persistence to
  [`../corpora-and-vector-spaces/SKILL.md`](../corpora-and-vector-spaces/SKILL.md).
- Route model transformations to
  [`../topic-modeling-and-transformations/SKILL.md`](../topic-modeling-and-transformations/SKILL.md).
- Route retrieval/indexing to
  [`../similarity-and-search/SKILL.md`](../similarity-and-search/SKILL.md).

## Common decisions

- Do not call `api.load` on a large pretrained model until `api.info` confirms
  size, storage path, and network approval.
- Use `return_path=True` to download/cache and return a path without loading a
  large model into memory.
- Use text conversion helpers only with vector text files whose dimensions are
  known or verified.
- Use `segment_wiki` for extracting plain-text article sections; use
  `make_wikicorpus` planning when the desired output is BoW/TF-IDF Matrix Market
  artifacts from a full dump.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for network
and cache failures, accidental large downloads, vector format mismatches,
TensorBoard TSV output issues, full Wikipedia dump constraints, and optional
lemmatization/dependency questions.
