# Word2Vec and NGram notes

This page covers the non-transformer embedding/scoring paths. Use SentenceModel / SBert for general semantic embeddings.

## Word2Vec dependency boundary

Word2Vec is optional at runtime. It imports `gensim.models.KeyedVectors` during `Word2Vec(...)` construction, so install `gensim` before using it. SentenceModel inference does not need `gensim`; Word2Vec does not need CUDA.

## Word2Vec loading behavior

`Word2Vec(model_name_or_path=...)` has two main modes:

1. **Existing local word2vec-format file**
   - If the path exists, text2vec loads it directly with `KeyedVectors.load_word2vec_format`.
   - Text files normally need no extra kwargs.
   - Binary files need `w2v_kwargs={"binary": True}` in direct API code.
   - The bundled `encode_texts.py` helper sets binary mode automatically for `.bin` paths, or explicitly with `--word2vec-binary`.

2. **Built-in model key**
   - `w2v-light-tencent-chinese`: practical default, lightweight Tencent Chinese word vectors, binary, about 111 MB.
   - `w2v-tencent-chinese`: full Tencent vector key, much larger and often impractical for normal skill verification.
   - If the requested key is missing from the local cache, text2vec attempts a remote download into the text2vec dataset cache.
   - Unknown non-file strings fall back to the lightweight key and emit a warning.

Use a local file path when the user needs deterministic no-network behavior.

## Encoding semantics

```python
from text2vec.word2vec import Word2Vec

model = Word2Vec("/path/to/local_vectors.txt")
vectors = model.encode(["银行卡", "花呗更改绑定银行卡"], show_progress_bar=False)
```

- Return type is `numpy.ndarray`.
- A single string returns one vector; a list of strings returns a 2-D matrix.
- The implementation averages available vectors and skips stopwords.
- If a longer token is out of vocabulary, the implementation can try Jieba tokenization to recover sub-token vectors.
- When no vectors are found, the output row is a zero vector of the model's vector size.

## Stopwords

Default behavior:

```python
model = Word2Vec("/path/to/local_vectors.txt")
```

- If `stopwords` is omitted, text2vec loads its packaged stopword list.

Custom list:

```python
model = Word2Vec(
    "/path/to/local_vectors.txt",
    stopwords=["我", "去", "到", "了", "。"],
)
```

Custom file:

```python
from text2vec.word2vec import load_stopwords

stopwords = load_stopwords("stopwords.txt")
model = Word2Vec("/path/to/local_vectors.txt", stopwords=list(stopwords))
```

Use custom stopwords when function words or punctuation are dominating short Chinese strings.

## Tiny local fixture

Use the bundled generator to create a small deterministic file for parser and offline smoke tests:

```bash
python scripts/make_tiny_word2vec_fixture.py --output-file tiny_word2vec.txt
```

Binary fixture:

```bash
python scripts/make_tiny_word2vec_fixture.py --output-file tiny_word2vec.bin --binary
```

The fixture is intentionally tiny and should not be used to judge model quality. It only proves that the local-file loading path and output serialization work.

## NGram / KenLM is reference-only

`NGram` is not a normal sentence embedding model in this repo skill.

```python
from text2vec.ngram import NGram

ngram = NGram(model_name_or_path="/path/to/zh_giga.no_cna_cmn.prune01244.klm")
score = ngram.ngram_score("兄弟们冲呀")
ppl = ngram.perplexity("兄弟们冲呀")
features = ngram.encode(["银行卡", "花呗更改绑定银行卡"])
```

Only use it when a task explicitly asks for KenLM-style language-model scores or per-character n-gram features.

Caveats:

- Requires `kenlm`; construction raises an import error if it is missing.
- If no local model path is supplied, text2vec attempts to download a Chinese language model of about 2.95 GB.
- `encode` returns variable-length score vectors tied to sentence length, not fixed-size semantic embeddings.
- Do not include NGram in the minimum embedding workflow, no-network smoke path, or generic vector-search path.
