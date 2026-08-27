---
name: models-and-serving
description: "Configure DB-GPT 0.8.1 model providers and local backends,
  validate model TOML, operate model controller/worker/API-server roles, use
  model-management CLI commands, and diagnose serving failures without mistaking
  an import or registry record for a live deployment."
metadata:
  disco-role: operating
license: Apache 2.0
disable-model-invocation: true
---

# Models and serving

Use this route when a DB-GPT task mentions model/provider TOML, `models.llms`,
embeddings or rerankers, OpenAI-compatible endpoints, Ollama, Hugging Face,
vLLM, llama.cpp, MLX, model workers, controller, model API server, model CLI,
model registration, health/heartbeat, GPU memory, quantization, or serving logs.

This route owns model selection and the model-service topology. Route general
installation, profile creation, workspace paths, and generic `start webserver`
setup to `setup-and-cli`; route agents/AWEL to `agents-and-awel`; route public
client CRUD and sandbox calls to `apis-client-and-sandbox`; route document,
embedding-pipeline, vector-store, and knowledge workflows to `data-and-rag`.

## Operating contract

- Work against the public DB-GPT 0.8.1 package interface, not a source checkout.
- Treat a TOML parse, Python import, controller registry row, or `healthy` value
  observed before a real request as configuration evidence only. Deployment is
  successful only after the intended service is reachable and a suitable model
  operation succeeds.
- Keep provider credentials in environment variables. Never print resolved
  secrets, copy them into generated files, or put them in shell history.
- Choose one model role explicitly: `llm`, `text2vec` (embedding), or
  `reranker`. A chat model cannot silently substitute for an embedding model.
- CPU is the verified baseline for this route. CUDA/local-model, vLLM,
  bitsandbytes, llama.cpp acceleration, and MLX are optional backend paths;
  do not claim they work from a CPU import or from host GPU visibility alone.

Read the focused contracts before making changes:

- [model-api-reference.md](references/model-api-reference.md) — configuration
  dataclasses, model/provider fields, worker types, and OpenAI-compatible API
  surface.
- [provider-and-backend-matrix.md](references/provider-and-backend-matrix.md)
  — provider credentials, endpoint conventions, embedding pairing, optional
  dependencies, and backend boundaries.
- [serving-workflows.md](references/serving-workflows.md) — proxy/local TOML,
  unified webserver, split controller/worker/API-server deployment, and CLI
  operations.
- [backends.md](references/backends.md) — local-model, quantization, VRAM, and
  hardware-specific decision rules.
- [troubleshooting.md](references/troubleshooting.md) — symptom-to-check
  diagnosis and recovery boundaries.

## Standard workflow

1. **Identify the topology and model roles.** Decide whether the user needs a
   unified webserver process, a split cluster, a standalone model API server,
   or only a provider configuration. Record the LLM, embedding, and optional
   reranker names separately.
2. **Select the provider/backend.** Prefer a remote proxy for a CPU-first smoke
   test. For a local model, require a real model path or an explicitly allowed
   model download and select `hf`, `vllm`, `llama.cpp`,
   `llama.cpp.server`, or `mlx` deliberately. Check the matrix for the
   provider-specific key and endpoint.
3. **Write a redacted TOML.** Put model entries under `[models]` using repeated
   `[[models.llms]]`, `[[models.embeddings]]`, and `[[models.rerankers]]` tables.
   Use `${env:NAME}` or `${env:NAME:-default}` placeholders. Set
   `default_llm`, `default_embedding`, or `default_reranker` only when multiple
   entries make selection ambiguous. Keep web/database configuration owned by
   the setup route unless the serving topology requires the related model
   service section.
4. **Validate without network or model loading.** Run the bundled checker:

   ```bash
   python scripts/model_config_check.py path/to/config.toml
   ```

   It parses TOML, checks model-table shape, provider/role requirements,
   duplicate names, placeholder syntax, endpoint URLs, and obvious service-port
   collisions. It never resolves secrets, calls a provider, contacts a
   controller, downloads a model, or starts a process. Use `--json` for a
   machine-readable report and `--allow-missing-embeddings` only when the
   configuration is intentionally chat-only; RAG/knowledge workflows must not
   use that exception.
5. **Run a safe package-level check.** Use `dbgpt --version`, the relevant
   static `--help`, and import/config-parser checks. Do not use `dbgpt model
   start --help` or another dynamic model command as an offline gate: model
   command discovery can query a controller and return a timeout/502 when no
   controller is reachable.
6. **Start only the chosen topology.** Use the exact commands in
   [serving-workflows.md](references/serving-workflows.md). Do not start both a
   unified model manager and an independent worker on the same ports. For
   split mode, start and verify the controller before workers, then verify
   workers before the API/web layer.
7. **Verify reachability and model capability.** Check the controller health and
   registry, then issue a minimal request through the intended API or provider.
   `dbgpt model list` is a registry/heartbeat view, not proof that generation or
   embedding works. An unreachable controller, failed heartbeat, missing model,
   authentication failure, or failed embedding request is a deployment failure;
   report it as such with the exact next check.
8. **Diagnose from the right boundary.** Inspect the command's resolved config
   path, service logs, bind address, port, controller address, provider base URL,
   model name, and optional-backend imports in that order. Redact API keys and
   authorization headers in reports.

## CLI routing facts

The DB-GPT CLI registers model commands under `dbgpt model` and service commands
under `dbgpt start` / `dbgpt stop`:

```text
dbgpt model [--address CONTROLLER_URL] list|start|stop|restart|chat
dbgpt start controller --config FILE [--daemon]
dbgpt start worker --config FILE [--daemon]
dbgpt start apiserver --config FILE [--daemon]
dbgpt start webserver [web options]
dbgpt stop controller|worker|apiserver [--port PORT]
```

`CONTROLLER_ADDRESS` can supply the controller address used by model-management
commands when `--address` is omitted. The dynamic `model start` command obtains
supported-model metadata from the controller before constructing some options;
therefore a failed remote request during help or invocation is not a successful
start. For model-service launch commands, the configuration file is the
source of worker/model parameters; do not rely on stale examples that show
model flags which are not present in the installed command tree.

## Validation and boundaries

A valid result for this route includes:

- provider/model/role entries parse with no secret resolution or network call;
- an embedding entry exists and is compatible with the intended RAG path;
- each selected local backend's dependency, path, device, and VRAM assumptions
  are explicit;
- service roles have distinct, reachable addresses and non-conflicting ports;
- controller registry and heartbeat checks are separated from generation,
  completion, embedding, or reranking checks;
- optional CUDA/GPU/provider/service dependencies are labeled unverified when
  they were not executed.

Do not claim that `dbgpt model list` proves deployment, that `--daemon` proves a
healthy child process, that a provider key exists merely because a placeholder
parsed, or that an A100-visible host proves CUDA/torch/vLLM/bitsandbytes support.
Do not add API CRUD, agent orchestration, or RAG chunking instructions here.
