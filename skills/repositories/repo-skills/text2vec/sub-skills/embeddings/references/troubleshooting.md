# Embeddings troubleshooting

## Quick matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'text2vec'` | The active Python environment cannot import the installed package. | Install `text2vec` into the environment that runs the helper or application. The bundled scripts do not add source checkout paths automatically. |
| `ModuleNotFoundError: No module named 'torch'` when using `SentenceModel` | text2vec package metadata does not install PyTorch, but SentenceModel imports and uses it. | Install a PyTorch wheel that matches the machine: CPU-only for CPU, CUDA wheel for NVIDIA GPUs, or an MPS-capable build on macOS. For Word2Vec-only work, use the Word2Vec path and install `gensim`. |
| `ModuleNotFoundError: No module named 'gensim'` when using `Word2Vec` | Word2Vec loads vectors through `gensim.models.KeyedVectors`, which is optional. | Install `gensim`, then use a local word2vec-format file or the built-in `w2v-light-tencent-chinese` key. |
| SentenceModel construction tries to download or fails with model host errors | `model_name_or_path` is a remote model id, or a local directory is incomplete. | For no-network tasks, pass a complete local HF-compatible directory containing tokenizer, config, and model weights. Otherwise pre-download/cache the model and ensure the cache is writable. |
| Word2Vec construction downloads unexpectedly | `model_name_or_path` was not an existing local file or a recognized built-in key. Unknown names fall back to the lightweight Tencent key. | Use an existing local file path, or explicitly use `w2v-light-tencent-chinese`. If a local path was intended, fix the path before running. |
| Tencent Word2Vec download or cache failure | The built-in lightweight vector file is not cached, the remote mirror is unavailable, or the cache contains a partial/corrupt file. | Prefer a local word2vec-format file for deterministic runs. If using the built-in key, ensure network access and a writable text2vec dataset cache, or clear the corrupt cached file and retry. |
| Local binary Word2Vec file fails to load | `KeyedVectors.load_word2vec_format` defaults to text mode unless `binary=True` is supplied. | In direct API code use `w2v_kwargs={"binary": True}`. With `scripts/encode_texts.py`, use a `.bin` suffix or pass `--word2vec-binary`. |
| `ValueError` from invalid `encoder_type` | `EncoderType.from_string` accepts exact enum names only. | Use one of `FIRST_LAST_AVG`, `LAST_AVG`, `CLS`, `POOLER`, `MEAN`; keep uppercase spelling or pass the enum value. |
| CUDA device error or CPU wheel mismatch | `--device cuda` was requested with a CPU-only PyTorch build, or the CUDA runtime is incompatible. | Test `torch.cuda.is_available()`. Use `--device cpu` for CPU wheels, install a matching CUDA PyTorch wheel for GPU, or use `--device mps` only when PyTorch MPS is available. |
| MPS is requested but errors on an operation | Some PyTorch/transformer combinations may not support all ops on MPS. | Retry with `--device cpu`; use MPS only after a small smoke batch works. |
| Built-in `text2vec` CLI output row count is smaller than input | The package CLI reads input lines into a `set`, which removes duplicates and does not preserve original order. | Use `scripts/encode_texts.py` when duplicate-preserving output or row-count validation is required. Blank lines are still skipped by the helper. |
| Built-in `text2vec` CLI boolean flags behave unexpectedly | The package CLI defines boolean arguments with `type=bool`; non-empty strings such as `False` can evaluate truthy in Python. | Use the bundled helper's flag form, such as `--normalize-embeddings` only when true. If using the package CLI, be cautious and inspect parsed behavior. |
| `--multi_gpu True --model_type word2vec` fails | The package CLI explicitly rejects multi-GPU Word2Vec; Word2Vec is not a SentenceModel multi-process path. | Drop `--multi_gpu` for Word2Vec, or switch to `--model_type sentencemodel` and use SentenceModel multi-process encoding. |
| Large batch or chunk crashes with OOM | Batch size, sequence length, or multi-process chunk size is too large for memory. | Lower `--batch-size`, `--max-seq-length`, and `--chunk-size`. For multi-process, use smaller chunks and one worker per GPU. For CSV/JSONL output, write in chunks rather than holding all records downstream. |
| `NGram` import or construction fails | `kenlm` is missing, or the large language model is not available. | Treat NGram as optional/reference-only. Install `kenlm` and pass a local language-model path only when the task explicitly needs n-gram/perplexity features. |
| NGram begins a huge download | No local KenLM model path was provided. | Stop the run unless the user approved a roughly 2.95 GB language model download; otherwise use SentenceModel or Word2Vec. |

## Decision tips

- If the user asks for semantic sentence vectors, start with SentenceModel / SBert.
- If the user asks for cold-start Chinese literal matching or a no-GPU baseline, consider Word2Vec.
- If the user asks for similarity scores, top-k search, or BM25, do not extend this sub-skill; route to similarity-search.
- If the user asks for model quality comparisons or benchmark reproduction, route to evaluation-benchmarks.
