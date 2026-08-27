# CLI and Script Reference

## Downloader

```bash
python -m gensim.downloader -i [data_name]
python -m gensim.downloader -d data_name
```

`-i` prints information; `-d` downloads. Inspect before downloading.

## GloVe to word2vec

Bundled wrapper:

```bash
python scripts/convert_glove_to_word2vec.py --input tiny.glove --output tiny.word2vec --verify-load
```

The input is a GloVe-style text file with one token and vector values per line.
The output is word2vec text format with a header line.

## word2vec to TensorBoard TSV

Bundled wrapper:

```bash
python scripts/word2vec_to_tensor_tsv.py --input tiny.word2vec --output-prefix tiny --verify
```

This creates `tiny_tensor.tsv` and `tiny_metadata.tsv`. Keep the two files
together; rows must remain aligned.

## word2vec standalone training

The package module `python -m gensim.scripts.word2vec_standalone` mirrors older
word2vec CLI flags such as `-train`, `-output`, `-size`, `-window`, `-iter`,
`-min_count`, `-cbow`, and `-binary`. Use it only with explicit tiny fixtures or
planned training jobs; embedding training through Python APIs is usually clearer.

## Package diagnostics

Use root `scripts/check_gensim_environment.py` rather than copying raw
`package_info` output into reports, because raw package-info style output can
include local install locations.

## Wikipedia helpers

- `segment_wiki`: extract article sections from compressed MediaWiki XML to
  JSONL.
- `make_wikicorpus`: convert a full dump into word ids, BoW Matrix Market, and
  TF-IDF artifacts.
- `make_wiki_online`/`make_wiki_online_nodebug`: online/hash dictionary variants.

Full Wikipedia workflows are large jobs. Test with `scripts/segment_wiki_tiny.py`
or a tiny XML fixture before scheduling a full dump conversion.
