# AdalFlow Package Overview

## When to read

Read this when you need a fast map of AdalFlow's public modules, optional extras, and cross-sub-skill ownership before choosing a detailed workflow.

## Package role

AdalFlow is a Python framework for building and optimizing LLM applications with PyTorch-like components. Its common building blocks are:

- `Component` and `DataComponent` for reusable pipeline nodes.
- `Prompt`, `DataClass`, parser objects, and `DataClassParser` for prompt and structured I/O.
- `ModelClient`, `Generator`, and `Embedder` for provider-agnostic generation and embeddings.
- `Document`, `LocalDB`, `TextSplitter`, retrievers, and context formatters for RAG.
- `FunctionTool`, `ToolManager`, `Agent`, `Runner`, and `ReActAgent` for tool-using agents.
- `AnswerMatchAcc`, `RetrieverEvaluator`, `Parameter`, `AdalComponent`, optimizers, and `Trainer` for evaluation and prompt optimization.
- logging/tracing utilities for local debugging, callbacks, spans, and optional MLflow.

## Install surface

Minimum practical install for AdalFlow 1.1.1 top-level imports:

```bash
python -m pip install "adalflow[openai]"
```

The OpenAI SDK is needed by the current `Generator` module's response-event imports even if the user will later use another provider. Additional extras are workflow-specific:

| Extra or package family | Use when | Owning sub-skill |
|---|---|---|
| `openai`, `groq`, `anthropic`, `google-generativeai`, `cohere`, `ollama`, `together`, `mistralai`, `fireworks-ai`, `azure`, `bedrock` | Live model or embedding calls for that provider. | `model-client-and-generator-workflows` |
| `faiss-cpu` | Local FAISS vector retrieval. | `retrieval-rag-and-data-pipelines` |
| `lancedb`, `sqlalchemy`, `pgvector`, Qdrant client/group | Optional vector-store or database-backed retrieval. | `retrieval-rag-and-data-pipelines` |
| `mcp` | MCP tool discovery and execution. | `agents-tools-and-streaming` |
| `datasets` | Built-in dataset loaders or benchmark workflows. | `evaluation-and-optimization` |
| `torch`, `transformers` | Local model clients, rerankers, or torch-backed workflows. | `model-client-and-generator-workflows` |
| `mlflow` | MLflow-backed tracing. | `tracing-observability-and-configuration` |

## Public module map

| Module family | Main APIs | Primary route |
|---|---|---|
| `adalflow.core` | `Component`, `Sequential`, `DataClass`, `Prompt`, `Generator`, `ModelClient`, `Embedder`, `Retriever`, `Document`, parser types. | Core, model-client, retrieval routes depending on task. |
| `adalflow.components.model_client` | Provider clients and response-format utilities. | `model-client-and-generator-workflows` |
| `adalflow.components.data_process` | `TextSplitter`, `ToEmbeddings`, retrieval-output processors. | `retrieval-rag-and-data-pipelines` |
| `adalflow.components.retriever` | BM25, FAISS, LanceDB, Postgres, Qdrant, LLM/reranker retrievers. | `retrieval-rag-and-data-pipelines` |
| `adalflow.components.agent` | `Agent`, `Runner`, `ReActAgent`, prompts and run logic. | `agents-tools-and-streaming` |
| `adalflow.eval` | answer matching, retriever recall/precision, LLM-as-judge utilities. | `evaluation-and-optimization` |
| `adalflow.optim` | parameters, gradients, losses, optimizers, trainer, optimize-anything. | `evaluation-and-optimization` |
| `adalflow.tracing` | tracing providers, spans, loggers, decorators, MLflow integration. | `tracing-observability-and-configuration` |
| `adalflow.utils` | env setup, logging, config, serialization, lazy imports. | Root troubleshooting or tracing/config route. |

## Safe validation strategy

Use service-free checks first:

1. `scripts/check_adalflow_environment.py` for root import and optional dependency status.
2. Core structured I/O and component smoke scripts for parser and pipeline basics.
3. Fake model-client/generator and fake planner/runner scripts for no-credential LLM and agent tests.
4. Text splitter/LocalDB and metric smoke scripts for RAG/evaluation foundations.
5. Live provider, vector-store, MCP, training, dataset, or MLflow checks only after their extras, services, credentials, data, and budget are explicitly available.
