# Embeddings API reference

This reference is for generating vectors only. For pairwise scores, top-k search, or BM25 retrieval, route to the sibling similarity-search sub-skill.

## SentenceModel / SBert

`SBert` is exported as an alias of `SentenceModel`.

```python
from text2vec import SentenceModel, SBert, EncoderType
```

Constructor:

```python
SentenceModel(
    model_name_or_path: str = "shibing624/text2vec-base-chinese",
    encoder_type: str | EncoderType | None = "MEAN",
    max_seq_length: int = 256,
    device: str | None = None,
)
```

Key arguments:

| Argument | Use |
|---|---|
| `model_name_or_path` | Hugging Face / compatible model id, or a local HF-compatible model directory containing tokenizer, config, and model weights. Use a local directory for no-network runs. |
| `encoder_type` | Exact `EncoderType` name or enum value. Supported values are listed below. Default is `MEAN`. |
| `max_seq_length` | Tokenizer truncation length used at construction and by default in `encode`. |
| `device` | PyTorch device string such as `cpu`, `cuda`, `cuda:0`, `mps`, or `npu`. If `None`, text2vec chooses `cuda` when available, then `mps`, then `cpu`. |

Encoder types:

| Value | Pooling behavior |
|---|---|
| `FIRST_LAST_AVG` | Average the first hidden layer and last hidden layer pooled over sequence length. |
| `LAST_AVG` | Average the last hidden layer over sequence length. |
| `CLS` | Use the first-token hidden state. |
| `POOLER` | Use `model_output.pooler_output`. |
| `MEAN` | Attention-mask-weighted mean pooling over the last hidden layer. |

Main methods:

```python
embeddings = model.encode(
    sentences,
    batch_size=32,
    show_progress_bar=False,
    convert_to_numpy=True,
    convert_to_tensor=False,
    device=None,
    normalize_embeddings=False,
    max_seq_length=None,
)
```

- `sentences` may be a single string or a list of strings.
- A single string returns one vector with shape `(dim,)`; a list returns `(n, dim)`.
- `convert_to_tensor=True` overrides `convert_to_numpy=True` and returns a stacked CPU tensor.
- `normalize_embeddings=True` L2-normalizes each row, which is useful before dot-product or cosine-style search.
- `max_seq_length` on `encode` temporarily overrides the constructor value for that call.

```python
dim = model.get_sentence_embedding_dimension()
```

- Returns the pooled hidden dimension when the loaded model exposes it.
- Tiny local smoke evidence for this repo confirmed a local HF-compatible model returned `(2, 16)` for a two-sentence batch, `(16,)` for one string, and `16` from this method.

## SentenceModel multi-process lifecycle

```python
pool = model.start_multi_process_pool(target_devices=None)
try:
    embeddings = model.encode_multi_process(
        sentences,
        pool,
        batch_size=32,
        normalize_embeddings=False,
        chunk_size=None,
    )
finally:
    model.stop_multi_process_pool(pool)
```

- Use this only for large SentenceModel batches; startup overhead is not worth it for tiny inputs.
- `target_devices=None` uses all CUDA devices if CUDA is available. If CUDA is unavailable, text2vec starts four CPU workers.
- You may pass explicit devices such as `['cuda:0', 'cuda:1']` or `['cpu', 'cpu']`.
- `encode_multi_process` preserves input order after worker results are collected.
- Always stop the pool in a `finally` block so child processes and queues are closed.
- Word2Vec does not support this lifecycle.

## Word2Vec

```python
from text2vec.word2vec import Word2Vec, load_stopwords
```

Constructor:

```python
Word2Vec(
    model_name_or_path: str = "w2v-light-tencent-chinese",
    w2v_kwargs: dict | None = None,
    stopwords: list[str] | None = None,
    cache_folder: str = "~/.text2vec/datasets/",
)
```

Key behavior:

| Input | Behavior |
|---|---|
| Existing local file path | Loaded with `gensim.models.KeyedVectors.load_word2vec_format`. Pass `w2v_kwargs={"binary": True}` for local binary word2vec files. |
| `w2v-light-tencent-chinese` | Built-in lightweight Tencent Chinese word vector key. It loads/downloads a 111 MB binary model to the text2vec cache. |
| `w2v-tencent-chinese` | Built-in full Tencent vector key. It is much larger and should be treated as a special large-download path. |
| Other non-file string | text2vec falls back to the lightweight Tencent key and emits a warning. |

```python
vectors = model.encode(sentences, show_progress_bar=False)
```

- `sentences` may be a single string or a list of strings.
- A single string returns `(dim,)`; a list returns `(n, dim)`.
- Encoding averages available token vectors and skips stopwords.
- If `stopwords` is omitted, text2vec loads its packaged stopword list. Pass a custom list or use `load_stopwords(path)` to control filtering.
- `gensim` is required only for Word2Vec usage.

## NGram / KenLM reference only

```python
from text2vec.ngram import NGram
```

- `NGram(model_name_or_path=None, cache_folder="~/.pycorrector/datasets/")` loads a KenLM language model.
- If `model_name_or_path` is missing, text2vec attempts to download a 2.95 GB Chinese language model.
- It requires `kenlm`; without it, construction raises an import error.
- Methods include `ngram_score(sentence)`, `perplexity(sentence)`, and `encode(sentences)`.
- `encode` returns per-character score vectors, not a fixed-size semantic embedding suitable for normal retrieval workflows.

## Batch CLI flags

The package console command is `text2vec`; the bundled helper is `scripts/encode_texts.py`. Prefer the bundled helper when you need JSONL output, duplicate-preserving rows, or predictable boolean flags.

| Flag | Meaning |
|---|---|
| `--input_file` | Required input text file, one sentence per non-empty line. |
| `--output_file` | Output CSV file in the package CLI; CSV or JSONL/NDJSON in the bundled helper. |
| `--model_type` | `sentencemodel` or `word2vec` in the package CLI; the helper also accepts `sbert` as a SentenceModel alias. |
| `--model_name` | HF model id, local HF model directory, local word2vec file, or built-in Word2Vec key. |
| `--encoder_type` | `MEAN`, `CLS`, `POOLER`, `FIRST_LAST_AVG`, or `LAST_AVG`. SentenceModel only. |
| `--batch_size` | Batch size passed to SentenceModel encode or multi-process encode. |
| `--max_seq_length` | Token truncation length for SentenceModel. |
| `--chunk_size` | Save/encode chunk size for batch helpers; also controls multi-process work chunking. |
| `--device` | Device string such as `cpu`, `cuda`, `cuda:0`, or `mps`. SentenceModel only. |
| `--show_progress_bar` | Progress display toggle. Use the bundled helper's boolean flag form to avoid `type=bool` pitfalls. |
| `--normalize_embeddings` | L2-normalize rows before writing or returning. SentenceModel only. |
| `--multi_gpu` | SentenceModel multi-process path. The package CLI explicitly rejects `word2vec` with this flag. |

## Direct Transformers / sentence-transformers fallback

- Use `SentenceModel` when you want text2vec's pooling and device wrapper.
- Use raw `transformers.AutoTokenizer` + `AutoModel` only when you need custom pooling or have an existing Transformers-only stack.
- A local HF-compatible directory can be loaded by text2vec, Transformers, and many sentence-transformers workflows; keep it complete to avoid network downloads.
