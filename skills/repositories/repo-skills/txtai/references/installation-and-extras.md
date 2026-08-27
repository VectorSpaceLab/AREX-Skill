# Installation and Optional Extras

Use this reference when selecting txtai dependencies for a user task. Install the smallest group that supports the requested workflow.

## Baseline

```bash
pip install txtai
python - <<'PY'
import importlib.metadata
from txtai import Embeddings, Application, Workflow
print(importlib.metadata.version("txtai"))
print(Embeddings, Application, Workflow)
PY
```

txtai requires Python 3.10 or newer. The standard package includes core dependencies such as NumPy, PyYAML, msgpack, Hugging Face Hub, safetensors, PyTorch, Transformers, and FAISS CPU. Some package indexes may install CPU-only or CUDA-enabled PyTorch wheels depending on index configuration; choose a CPU-specific PyTorch index when the target does not need GPU acceleration.

## Extras Map

| Extra | Use when | Typical surfaces |
| --- | --- | --- |
| `agent` | Building `Agent` objects, tool calling, agent teams, skill.md/agents.md integration | `smolagents`, MCP adaptation, Jinja templates |
| `api` | Running FastAPI/Uvicorn, OpenAI-compatible routes, MCP endpoint, auth, uploads | `txtai.api`, `CONFIG=app.yml uvicorn "txtai.api:app"` |
| `ann` | Choosing non-default ANN/vector stores | Annoy, HNSW, pgvector, sqlite-vec, sklearn/scipy, SQLAlchemy |
| `cloud` | Loading/saving indexes through cloud storage | Apache Libcloud, locks |
| `console` | Interactive console formatting | Rich |
| `database` | DuckDB or SQLAlchemy-backed content databases and object encoders | DuckDB, SQLAlchemy, Pillow |
| `graph` | Graph indexes, graph queries, topic/network analysis | grand-cypher, grand-graph, NetworkX, SQLAlchemy |
| `model` | ONNX model export or runtime tasks | ONNX, ONNX Runtime |
| `pipeline-audio` | Text-to-speech, audio streams, transcription, speech workflows | sounddevice, soundfile, scipy, ONNX runtime, tokenizer/VAD packages |
| `pipeline-data` | Document parsing, HTML/Markdown conversion, chunking, tabular inputs | BeautifulSoup, Chonkie, Docling, LiteParse, NLTK, pandas, Tika |
| `pipeline-image` | Captioning, image hashing, object detection | Pillow, timm, imagehash |
| `pipeline-llm` | LLM/RAG backends beyond core Transformers | LiteLLM, llama.cpp, LiteRT LM API, HTTPX |
| `pipeline-text` | Text classification/entity/sparse-vector extras | GLiNER, SentencePiece, staticvectors |
| `pipeline-train` | Training, ONNX export, PEFT/quantization workflows | accelerate, bitsandbytes, ONNX tooling, PEFT, scikit ONNX |
| `pipeline` | Broad pipeline coverage | All `pipeline-*` groups; heavier than most focused tasks need |
| `scoring` | Sparse scoring with SQLAlchemy-related storage | SQLAlchemy |
| `vectors` | Alternate vectorizers/backends | sentence-transformers, tokenizers, llama.cpp, LiteLLM, model2vec, skops, staticvectors |
| `workflow` | Workflow scheduling and file/data task extras | croniter, pandas, openpyxl, requests, XML tools, cloud storage |
| `similarity` | Backward-compatible combined ANN/vector group | `ann` plus `vectors` |
| `all` | Full-feature local environment where size is acceptable | Most optional groups; avoid for narrow tasks |

## Task-Based Selection

- Embeddings-only search: start with `txtai`; add `graph`, `database`, `ann`, `vectors`, or `scoring` only when the config uses those features.
- Document extraction/chunking before indexing: add `pipeline-data`; then route workflow details to `sub-skills/pipelines-and-workflows/`.
- RAG with hosted LLMs: add `pipeline-llm` and configure credentials outside source files.
- Agents and agent tools: add `agent`; if an agent calls hosted LLMs, also add the backend-specific LLM dependencies.
- FastAPI service deployment: add `api`; add workflow/pipeline/agent extras only for route families enabled in the config.
- Docker/cloud deployment: choose extras inside the container image, mount model/index caches, and avoid downloading models on every cold start.

## CPU, GPU, and Offline Notes

- Use CPU-only PyTorch wheels when GPU acceleration is not needed or CUDA downloads are too large for the environment.
- GPU acceleration requires matching the PyTorch wheel, driver, CUDA capability, and optional backend packages. Do not claim GPU support without a tiny backend check.
- Hugging Face model paths may trigger downloads. In restricted networks, use local model paths, pre-populated caches, or explicit offline-mode guidance.
- Audio/image/document parsing extras can require system libraries. If an import fails even after installing the Python extra, inspect the native library error and route to the nearest sub-skill troubleshooting reference.

## Verification

Run the shared helper first:

```bash
python scripts/check_txtai_environment.py --json
```

Then run the sub-skill helper that matches the workflow. Keep smoke tests no-download unless the user explicitly authorizes model, network, GPU, or service work.
