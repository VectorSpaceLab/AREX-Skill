# ZenML Agent and Deployment Workflows

Use this reference to adapt ZenML examples into production-ready deployment or agent workflows without depending on the original example directories at runtime.

## Choose the Serving Pattern

### Pipeline Deployment

Use a pipeline deployment when the user needs a persistent HTTP service that wraps a ZenML pipeline. This is the preferred path for new real-time inference, document analysis, interactive agents, and custom business workflows.

Core shape:

```python
from typing import Annotated

from zenml import ArtifactConfig, pipeline, step
from zenml.config import CORSConfig, DeploymentSettings, DockerSettings

@step
def analyze_text(content: str) -> dict[str, object]:
    return {
        "summary": content[:120],
        "word_count": len(content.split()),
        "method": "deterministic",
    }

@pipeline(
    enable_cache=False,
    settings={
        "docker": DockerSettings(requirements="requirements.txt"),
        "deployment": DeploymentSettings(
            app_title="Document Analysis Service",
            dashboard_files_path="ui",
            cors=CORSConfig(allow_origins=["*"]),
        ),
    },
)
def document_service(
    content: str = "ZenML deployment smoke test",
) -> Annotated[dict[str, object], ArtifactConfig(name="analysis")]:
    return analyze_text(content=content)
```

Checklist:

- Give every pipeline input a default value and a JSON-serializable type.
- Keep invocation parameters aligned with step parameters by name.
- Return simple JSON-compatible objects for online APIs, or clear artifact references for larger outputs.
- Disable caching for request/response services unless repeated identical requests should deliberately reuse artifacts.
- Use pipeline `on_init`/`on_cleanup` hooks or a custom deployment service when models, retrieval indexes, prompts, or agent clients should stay warm across requests.
- Keep UI files under the project source root and point `dashboard_files_path` at the relative directory that contains `index.html`.

### Model Deployment via Pipeline

For classical ML serving, prefer deploying an inference pipeline that loads a trained model artifact and exposes preprocessing, prediction, and response formatting as one service. The example-backed pattern is:

1. Train offline and tag or name the production artifact/model version.
2. In the inference pipeline, load the model once during deployment initialization.
3. Accept a JSON payload such as `customer_features: dict[str, float]`.
4. Return a dictionary with prediction, probability, model version, and status.
5. Add deployment settings for app metadata, CORS, health/docs paths, and optional dashboard files.
6. Add resource settings only when the selected deployer honors them.

This pattern is more flexible than a model server template because preprocessing, validation, business rules, guardrails, and reporting all remain in the pipeline.

### Agent Deployment

For LLM or agent workflows, use the same pipeline deployment pattern, but add explicit credential and fallback behavior.

A robust agent pipeline should:

- Accept user inputs as JSON parameters, such as `query`, `content`, `url`, `filename`, or `document_type`.
- Validate or sanitize text and URL inputs before calling tools or providers.
- Detect optional provider credentials through environment variables without printing values.
- Return structured outputs with a `status`, `method`, `latency_ms`, `error` or `skip_reason`, and domain-specific payload.
- Include deterministic fallback branches for demos and smoke checks when the provider key is missing.
- Keep external calls isolated in one step or helper so credential-free tests can monkeypatch, stub, or skip them.

Example adaptation pattern:

```python
import os

from zenml import pipeline, step
from zenml.config import DockerSettings

@step
def run_agent(query: str) -> dict[str, str]:
    if not os.getenv("OPENAI_API_KEY"):
        return {
            "status": "skipped",
            "method": "fallback",
            "response": f"No provider key; deterministic response for: {query}",
        }
    return {
        "status": "ready_for_provider",
        "method": "llm",
        "response": "Call the configured provider here.",
    }

@pipeline(
    enable_cache=False,
    settings={
        "docker": DockerSettings(
            requirements="requirements.txt",
            environment={"OPENAI_API_KEY": "${OPENAI_API_KEY}"},
        ),
    },
)
def agent_pipeline(query: str = "Summarize ZenML deployments") -> dict[str, str]:
    return run_agent(query=query)
```

## Invocation and HTTP Contract

A deployed pipeline exposes an invocation endpoint. CLI and HTTP calls carry pipeline parameters, not arbitrary step-local names.

Common shapes:

```bash
zenml deployment invoke my-service --query="Summarize this text"
```

```bash
curl -X POST "$ENDPOINT/invoke" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"query": "Summarize this text"}}'
```

If authentication is enabled by the deployer or deployment settings, include the configured bearer token or auth header without logging it.

## Agent Framework Matrix

Agent framework examples share the same broad architecture:

- A ZenML `@pipeline` accepts a default `query` parameter.
- One step runs the framework agent and catches framework-specific exceptions.
- One step formats the output into a stable string or dictionary artifact.
- `DockerSettings` packages `requirements.txt` and forwards provider environment variables.
- Deployment is possible with `zenml pipeline deploy ... --name <service>` after stack/deployer setup.

Framework-specific differences to preserve when adapting:

| Framework type | Adaptation concern |
| --- | --- |
| Multi-agent systems | Keep role/task setup deterministic and bound tool permissions before serving. |
| Graph/workflow agents | Preserve graph state schema and convert responses into JSON-safe output. |
| RAG frameworks | Separate retrieval index setup from online query serving; skip network downloads unless authorized. |
| Async frameworks | Contain event-loop handling inside a step; avoid introducing async FastAPI routes in ZenML repo code. |
| Provider SDK wrappers | Normalize response extraction because frameworks return strings, messages, objects, or nested dicts. |

## Source Script Decision

The repository-level agent example runner was intentionally not bundled as a runtime script. It creates fresh environments for every agent framework, installs example dependencies, may call provider APIs, and writes log/summary files. Treat it as reference-only evidence for active ZenML checkout maintenance. For runtime skill use, prefer small credential-free validation through this sub-skill's `validate_deployment_settings.py` and targeted synthetic agent pipelines.

## Production Readiness Checklist

Before claiming a deployment is production-ready, verify:

- The active stack has a deployer compatible with the target execution location.
- Remote deployments have non-local artifact storage, container registry, image builder, and credentials when required.
- Pipeline inputs and outputs are JSON-serializable or intentionally represented as artifacts.
- `DeploymentSettings` endpoint paths, CORS, secure headers, dashboard files, and auth posture match the user's environment.
- `DockerSettings` includes the smallest runtime dependency set and forwards only intended environment variables or secret references.
- Provider API keys, service URLs, auth tokens, and registry credentials are never printed, hard-coded, or written into generated examples.
- Failure responses distinguish unavailable credentials/network/services from code or skill gaps.

## Native Candidates and Safe Adaptations

Native evidence supports these future verification ideas, but they are not safe to run by default:

- Classical ML deployment example: good source for an inference pipeline with startup model loading, dashboard files, CORS, and resource settings. Skip full deployment unless ZenML server, deployer, and local/remote service execution are authorized.
- Agent deployment example: good source for document analysis, optional OpenAI, deterministic fallback, and embedded UI. A credential-free synthetic case can adapt the fallback path without API calls.
- Agent comparison example: good source for architecture comparison, custom materializers, LiteLLM, Langfuse, and mock responses. Skip provider calls and observability exports without keys.
- Agent framework integration examples: good source for framework matrix patterns. Skip the full matrix by default because it installs many dependencies and often needs provider credentials or network.
