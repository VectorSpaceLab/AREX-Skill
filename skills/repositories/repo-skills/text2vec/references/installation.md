# Installation and Environment Notes

## Purpose

Read this when installing `text2vec`, checking imports, or deciding which optional dependencies are needed before using the sub-skills.

## Core install pattern

`text2vec` is a Python package named and imported as `text2vec`. The public console entry point is also `text2vec`.

A typical runtime install is:

```bash
python -m pip install torch
python -m pip install -U text2vec
python -c "import text2vec; print(text2vec.__version__)"
text2vec -h
```

For a local checkout or editable development install:

```bash
python -m pip install torch
python -m pip install -r requirements.txt
python -m pip install --no-deps .
python -c "from text2vec import SentenceModel, Similarity, BM25; print('ok')"
```

`setup.py` declares `jieba`, `loguru`, `transformers`, `datasets`, `tqdm`, `scikit-learn`, and `pandas`, but the source imports `torch` in the public model modules. Install a compatible PyTorch build before relying on `SentenceModel`, training, `Similarity`, or the CLI.

## Optional dependency matrix

| Workflow | Extra packages/artifacts | Notes |
|---|---|---|
| SentenceModel embeddings | `torch`, `transformers`, model weights from a local directory or Hugging Face cache | Default model names download unless already cached. Use a local model directory for offline checks. |
| CLI batch embeddings | Core package plus the dependency for the selected `--model_type` | The bundled `sub-skills/embeddings/scripts/encode_texts.py` keeps duplicate input rows; the package CLI de-duplicates non-empty lines. |
| Word2Vec | `gensim` plus a local word2vec file or the built-in Tencent lightweight vector download | The built-in vector is large enough that offline/local fixtures are better for smoke tests. |
| NGram | `kenlm` plus a very large language-model file | Reference-only for most tasks; do not install just for general embeddings. |
| Training/fine-tuning | `torch`, `transformers`, `datasets`; optional GPU/CUDA/bf16 support | Full training commonly downloads base models/datasets and can be long-running. Use validators before training. |
| FastAPI serving | `fastapi`, `uvicorn` | Use the bundled app template; importing it should not start a server. |
| Jina serving | `jina`, `docarray`, network access to JinaHub when using hub executors | Prefer for multi-model/gRPC/cloud-native serving only when the optional stack is acceptable. |
| Gradio demo UI | `gradio` | Interactive/manual demo, not a production default. |
| MTEB/C-MTEB benchmarks | benchmark packages plus model/dataset downloads | Treat as explicit benchmark work, not a default smoke test. |

## Backend guidance

- CPU is sufficient for import checks, BM25, data validators, tiny local-model smoke tests, and many small examples.
- GPU/CUDA is optional acceleration for large embedding batches, multi-GPU encoding, and realistic training. Do not claim CUDA coverage unless a CUDA PyTorch build passes a device allocation check.
- `device=None` in `SentenceModel` selects CUDA if available, then MPS if available, otherwise CPU. Use explicit `device='cpu'` for deterministic offline smoke checks.
- `bf16` and multi-card training require hardware/framework support and should be treated as training-scale checks.

## Safe environment check

Run the bundled root helper without triggering default model downloads:

```bash
python scripts/check_text2vec_env.py
```

Useful variants:

```bash
python scripts/check_text2vec_env.py --expect-cuda
python scripts/check_text2vec_env.py --local-model /path/to/local/hf-compatible-model
```

The helper checks imports, optional dependencies, torch backend status, BM25, `cos_sim`, and `semantic_search`. The `--local-model` option performs a no-network `SentenceModel` encode smoke against an existing local model directory.
