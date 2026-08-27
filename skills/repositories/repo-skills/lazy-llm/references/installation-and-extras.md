# Installation and Optional Extras

## When to read

Read this when a LazyLLM task starts with installation, import errors, optional dependency questions, or backend selection. The key rule is: install the smallest extra that covers the selected workflow; do not default to `full` for routine inspection.

## Python and base package

LazyLLM 0.7.5 declares Python `>=3.10,<3.14`. The package exposes the distribution name `lazyllm` and the import package `lazyllm`.

Typical install choices:

```bash
python -m pip install lazyllm
python -m pip install -e .        # only when working in a LazyLLM source checkout
```

Base install supports the core package, CLI dispatcher, config, common modules, flow primitives, and many public class definitions. It does **not** guarantee document/RAG, vector stores, multimodal, local serving, fine-tuning, tracing, MCP, or provider SDK dependencies.

## CLI install helper

The repo CLI includes an install dispatcher:

```bash
lazyllm install <extra1> <extra2> <pkg1> ...
```

Use it to install named optional groups or explicit packages into the active Python environment. Confirm the active interpreter first when using Conda, venv, uv, or notebook kernels.

## Practical extra matrix

| Extra or package group | Use when | Notes |
| --- | --- | --- |
| base package only | Config, CLI routing, simple modules, flow composition, no optional imports | Safe first choice for inspection and pure flow tests. |
| `rag` | Importing `lazyllm.tools.rag`, `Document`, `DocNode`, BM25, readers, SQL-backed doc service metadata, local RAG tests | Installs pandas/numpy/fsspec, pypdf/docx/pptx/ebook/html readers, tiktoken, spaCy, bm25s, Stemmer, NLTK, jieba, sentencepiece, SQLAlchemy, psycopg2, json repair. |
| `agent-advanced` | MCP or advanced agent integrations need `mcp` or `ctranslate2` | Do not run external MCP servers unless the task provides approval and command details. |
| `rag-advanced` | Vector databases, embedding model stacks, OpenSearch/Elasticsearch, Redis/RedisVL, Milvus, offline embeddings, OCR/audio ingestion | Can install heavy model/vector packages; treat as optional unless the task names those backends. |
| `standard` | Broad app stack for common demos and tests, including gradio, vector stores, model packages, and some local inference/training dependencies | May install large ML packages. Use when the user wants broad LazyLLM examples, not for a single config/flow question. |
| `full` | All optional stacks, advanced local model backends, multimodal, provider SDKs, tracing, and many external systems | Expensive and broad; use only with explicit need and budget. |
| `multimodal`, `online-advanced`, `deploy-all`, `finetune-all`, `vllm`, `lmdeploy`, `lightllm`, `llama-factory`, `tracing`, `dev` | Focused backend, provider, development, or observability work | Check the model-deployment or core-runtime sub-skill before selecting these. |

## Safe validation commands

Use bundled scripts for no-network checks:

```bash
python scripts/check_lazyllm_env.py --require-rag --require-agent --require-writer
python scripts/inspect_lazyllm_surface.py --json
```

A focused pytest smoke set for a source checkout can use CPU-only tests such as config, model type mapping, online chat history sanitization, search content contracts, and BM25 RAG. Treat provider, GPU, vector database, external parser service, Kubernetes/Slurm/SCO, and MCP process tests as optional unless selected by the task.

## Common dependency signals

- `ImportError: Missing package(s): [...] You can install them by: lazyllm install rag` means a lazy dependency group check fired. Install the named extra for the selected environment.
- `ModuleNotFoundError` for provider SDKs such as online multimodal packages usually belongs to model-deployment optional backends.
- Missing `mcp`, `npx`, or MCP server startup errors belong to agents-tools and are not proof that basic agents are broken.
- Missing CUDA, vLLM, LMDeploy, LLaMA-Factory, or model weights belongs to model-deployment and should not block base import, flow, RAG text-only, or writer artifact work.

## Environment hygiene

- Keep credentials out of shell history and config files shown to users.
- If using a source checkout, distinguish package installation failures from missing optional extras. An editable build can succeed while optional RAG imports still fail until `lazyllm install rag` runs.
- For GPU/model work, verify hardware, model path/cache, server port, and extra group before running expensive examples.
- For CLI diagnostics, use concrete subcommands. The dispatcher prints usage and exits non-zero for unknown commands or bare `--help`.
