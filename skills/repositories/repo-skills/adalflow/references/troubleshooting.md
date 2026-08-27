# Root Troubleshooting

## When to read

Read this for install/import and cross-cutting AdalFlow failures before going to a workflow-specific sub-skill.

## Install/import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'openai'` while importing `adalflow` | In AdalFlow 1.1.1, `adalflow.core.generator` imports OpenAI response event types at module import time. | Install the OpenAI extra even if the target provider is not OpenAI: `python -m pip install "adalflow[openai]"`. Then rerun the root environment check. |
| `ImportError: Please install <provider>` when constructing a provider client | Provider clients are lazy imports with optional SDK extras. | Install only the provider SDK extra needed by the workflow. Then verify import and credentials separately. |
| `MLflow not available. Install with: pip install mlflow` | Optional MLflow integration is not installed. | Ignore for non-MLflow tracing. Install `mlflow` only when using MLflow tracing or experiment tracking. |
| Top-level import works, but live model call fails | Missing API key, wrong endpoint/base URL, unsupported model name, network/provider error, or wrong `model_kwargs`. | Route to `model-client-and-generator-workflows`; first replace the provider with the bundled fake-client smoke to isolate AdalFlow wiring from provider availability. |
| Vector retriever import fails | Optional backend such as FAISS, LanceDB, Qdrant, Postgres, or pgvector is not installed. | Route to `retrieval-rag-and-data-pipelines`; install only the backend needed by the selected retriever and verify service availability separately. |
| MCP imports or tool discovery fails | `mcp` extra is missing, Python version is too old, or no server is running. | Route to `agents-tools-and-streaming`; use MCP reference-only setup until a server process and extra are available. |

## Workflow failures

| Symptom | Route | First action |
|---|---|---|
| Parser returns `GeneratorOutput.error` or structured output is missing fields | `core-components-and-structured-io`, then `model-client-and-generator-workflows` | Validate the schema and parser with a service-free string before calling a provider. |
| RAG returns empty or irrelevant context | `retrieval-rag-and-data-pipelines` | Check document loading, splitter settings, transformed document count, retrieval `top_k`, and index freshness before blaming the generator. |
| Agent exceeds `max_steps` or keeps choosing the wrong tool | `agents-tools-and-streaming` | Verify each tool independently with `FunctionTool`/`ToolManager`, then inspect the agent prompt and final-answer tool contract. |
| Training or optimization is expensive or unstable | `evaluation-and-optimization` | Run metric smokes and `Trainer.diagnose`-style checks before `Trainer.fit`; require explicit data/provider/budget. |
| Trace/log files are missing or contain sensitive data | `tracing-observability-and-configuration` | Use explicit writable artifact directories, redact secrets, and avoid logging raw provider payloads unless needed for debugging. |

## Safe escalation order

1. Run the root environment check.
2. Run the nearest service-free sub-skill smoke script.
3. Inspect workflow-specific troubleshooting.
4. Add optional extras/services/credentials only for the selected workflow.
5. Run native or live checks only after the generated guidance has made expected inputs, outputs, and failure conditions explicit.

Do not use a successful CPU import as evidence for GPU, vector-service, provider, MCP, dataset, or MLflow readiness. Those are separate optional gates.
