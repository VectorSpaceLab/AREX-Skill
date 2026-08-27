# Cross-Cutting Troubleshooting

## When to Read

Read this when a SuperAGI task fails before you know which sub-skill owns the
problem, or when a failure spans services, configuration, credentials, and
agent/tool behavior.

## Quick Triage

1. Identify the layer: Docker/runtime, FastAPI/API, agent workflow, toolkit,
   model provider, resource/vector storage, or GUI proxy.
2. Check whether the failing operation is safe and authorized. Do not run
   service startup, downloads, migrations, provider-key validation, or external
   API calls unless the downstream user expects those side effects.
3. Validate config shape first with `scripts/check_superagi_config.py`.
4. If a checkout is available, statically summarize it with
   `scripts/summarize_superagi_checkout.py` and compare it with the provenance
   snapshot.
5. Route to the nearest sub-skill for layer-specific recovery.

## Common Symptoms

| Symptom | Likely cause | Next action |
|---|---|---|
| `config.yaml` not found | The template was not copied, or the process runs from the wrong working directory. | Create a config from the checkout's template, then run the config checker before service startup. |
| FastAPI starts but DB errors appear | `DB_URL`, `DB_HOST`, credentials, or container hostnames do not match the target deployment. | Read deployment configuration; ensure Docker uses `super__postgres` while host-local runs usually need `localhost` or an explicit URL. |
| Celery tasks do not run | Redis URL mismatch, worker not running, broker inaccessible, or import failure in `superagi.worker`. | Confirm `REDIS_URL`, worker logs, and that backend/worker use the same config source. |
| GUI loads but API calls fail | nginx/proxy mismatch, backend not healthy, wrong frontend API base, or CORS/proxy path issue. | Inspect compose/proxy topology and API prefixes. |
| `/v1/agent/...` returns 401/404 | Missing/invalid `X-API-Key`, org/project mismatch, or wrong endpoint prefix. | Read `api-service` auth/API reference and verify API-key records. |
| Agent run loops or retries | LLM output parser could not parse tool JSON, unknown tool name, missing tool config, or tool validation error. | Read agents-workflows parser guidance and toolkits-integrations troubleshooting. |
| Provider-key validation fails | Wrong provider name, placeholder key, network failure, local LLM base URL issue, or upstream service error. | Read models-resources-vector provider guidance; never invent credentials. |
| Vector/resource failures | Missing vector DB credentials/service, wrong index dimensions, missing document parser dependency, or FILE/S3 mismatch. | Read models-resources-vector vector/resource references. |
| GPU/local LLM path fails | Docker GPU runtime not available, CUDA image/wheel mismatch, `llama-cpp-python` CUDA build failure, or local LLM endpoint not ready. | Treat as optional unless explicitly required; read deployment GPU notes before retrying. |

## Stop Conditions

Stop and ask the downstream user before:

- starting long-running Docker services or Celery workers;
- running migrations against a non-temporary database;
- downloading marketplace/external tools;
- installing apt packages or arbitrary tool requirements;
- validating real provider/API credentials;
- changing storage from FILE to S3 or connecting to live vector DBs;
- running GPU builds or CUDA package reinstallations.

## Evidence Hints

- Endpoint prefixes are assembled in `main.py`; use the bundled route inspector
  instead of importing the application when static analysis is enough.
- Workflow seeds define default agent workflow names such as Goal Based
  Workflow, Dynamic Task Workflow, Fixed Task Workflow, Sales Engagement
  Workflow, Recruitment Workflow, and SuperCoder.
- Tool names are normalized by lowercasing and removing spaces during execution;
  an apparently similar name can still fail if the toolkit registration did not
  create the expected `Tool` record.
- `config_template.yaml` includes many placeholders; a placeholder-looking value
  is not proof that a capability is configured.
