# Configuration and Secrets

## Configuration layers

Yuxi has three relevant configuration layers:

1. Code defaults.
2. Startup environment variables from `.env` or `.env.prod` through Compose.
3. Administrator system options stored in PostgreSQL and shared to API/worker
   through Redis cache.

Model providers are managed in the web UI, not by editing a static model list.
Startup-only settings such as database URLs, Redis, sandbox, storage paths,
LangGraph checkpointer backend, and Compose service URLs require container
restart after changes. Administrator system options are read at runtime and do
not require restart after saving.

## Environment files

Never print full environment files. When diagnosing, report only variable names
and whether each is missing, blank, or intentionally unmanaged.

### Development `.env`

Important development variables:

| Variable | Purpose | Notes |
| --- | --- | --- |
| `SILICONFLOW_API_KEY` | Default recommended model-provider credential. | Required by the interactive init helper; other providers can be configured later. |
| `JWT_SECRET_KEY` | Signs application tokens. | Generate a strong random value; do not reuse sandbox token. |
| `YUXI_INSTANCE_ID` | Stable identifier for this Yuxi deployment. | Keep stable across restarts for the same deployment. |
| `SANDBOX_PROVISIONER_TOKEN` | Bearer token between API/worker and sandbox-provisioner. | Compose requires it; at least 32 characters. |
| `YUXI_CORS_ORIGINS` | Browser cross-origin allowlist. | Development defaults to local web origins when unset. |
| `WEB_SEARCH_PROVIDER`, `DOUBAO_SEARCH_API_KEY`, `TAVILY_API_KEY` | Optional web search integration. | External network/credential checks are opt-in. |
| OCR provider variables | Optional OCR services and cloud tokens. | See OCR section below. |

The init helper can generate JWT, instance, and sandbox values and can prompt for
model/search keys. Because it writes `.env` and pulls images, do not run it from
an automated troubleshooting script.

### Production `.env.prod`

Production Compose refuses to start when these are missing or empty:

| Variable | Why it is required |
| --- | --- |
| `POSTGRES_PASSWORD` | PostgreSQL service and API/worker connection. |
| `NEO4J_PASSWORD` | Neo4j graph service. |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | Object storage and Milvus object-store backend. |
| `JWT_SECRET_KEY` | Token signing; use a strong persisted random value. |
| `YUXI_INSTANCE_ID` | Stable unique instance identity. |
| `SANDBOX_PROVISIONER_TOKEN` | API/worker authentication to sandbox-provisioner; at least 32 characters. |
| model-provider keys | Needed only for enabled providers/models. |

Use different random values for JWT and sandbox tokens. Persist them securely;
rotating them can invalidate sessions or break service-to-service auth. If an
older deployment used historical default database/object-store credentials,
change the actual service credentials inside existing volumes before relying on
new environment values.

## Administrator system options

Runtime administrator options live in PostgreSQL and are shared through Redis.
Notable fields:

| Option | Default intent |
| --- | --- |
| `default_model`, `fast_model` | Chat model selection in `provider_id:model_id` form. |
| `embed_model` | Default embedding model for knowledge workflows. |
| `reranker` | Default rerank model. |
| `content_guard_llm_model` | Model for optional LLM content guard. |
| `enable_content_guard`, `enable_content_guard_llm` | Optional moderation switches. |
| `default_ocr_engine` | Default OCR engine, usually `rapid_ocr` for CPU/local use. |

Legacy `saves/config/base.toml` values are migrated once into PostgreSQL. After
migration, administrator values in the database are the effective source.

## Model providers

Manage providers under the web UI model-provider page. Provider templates define
provider IDs, base URLs, credential environment variable names, and remote model
discovery. A provider is usable only after credentials are present, the provider
is enabled, and models are added or discovered.

Runtime model identifiers use:

```text
provider_id:model_id
```

`model_id` may itself contain `/`; split on the first `:` only.

Common built-in provider IDs include OpenAI-compatible and vendor-specific
entries such as `openai`, `deepseek`, `alibaba`, `zhipuai`, `zai`, `moonshotai`,
`minimax`, `openrouter`, `modelscope`, `siliconflow-cn`, and `siliconflow`.
Embedding and rerank defaults are commonly provided by DashScope or SiliconFlow
variants, but credentials and availability are deployment-specific.

OpenAI-compatible request extra parameters are restricted to a small top-level
allowlist such as `enable_thinking`, `thinking_budget`, `thinking`, `reasoning`,
and `reasoning_effort`. If a provider needs another field, treat it as a code
change plus tests, not a free-form UI setting.

## CORS and proxy

- Development with `YUXI_ENV=development` and blank `YUXI_CORS_ORIGINS` allows
  local Vite origins.
- Production with `YUXI_ENV=production` and blank `YUXI_CORS_ORIGINS` returns an
  empty cross-origin allowlist. Same-origin Nginx deployment does not need CORS.
- Cross-origin production deployment must set exact origins, for example
  `https://frontend.example.com` or a comma-separated list.
- `YUXI_CORS_ORIGINS=*` is not recommended; credentials are disabled for wildcard
  origins, which breaks login/JWT assumptions.

Production Nginx proxies `/api/` to the API container, disables buffering for
SSE/streaming responses, and increases proxy timeouts for uploads and long runs.
Place TLS in front of Nginx or configure an HTTPS-capable reverse proxy for real
internet exposure.

## MinIO and public files

Development publishes MinIO API and console only on loopback ports. Production
hides MinIO service ports and exposes only read-only public bucket objects
through same-origin `/minio/public/...`.

Rules:

- Do not expose MinIO `9000` or `9001` publicly in production.
- Use `MINIO_PUBLIC_URL` only when a separate static asset domain is configured
  with equivalent read-only restrictions.
- Private knowledge-base buckets are not served by the public proxy.

## Sandbox-provisioner

The sandbox-provisioner supplies isolated execution sandboxes for agent tools.
Key settings:

| Variable | Meaning |
| --- | --- |
| `SANDBOX_PROVIDER` | Usually `provisioner`. |
| `SANDBOX_PROVISIONER_URL` | Internal URL, defaulting to `http://sandbox-provisioner:8002`. |
| `SANDBOX_PROVISIONER_TOKEN` | Required bearer token; at least 32 characters. |
| `SANDBOX_VIRTUAL_PATH_PREFIX` | User-visible virtual sandbox path boundary. |
| `SANDBOX_EXEC_TIMEOUT_SECONDS`, `SANDBOX_MAX_OUTPUT_BYTES` | Execution limits. |
| `SANDBOX_PROVISIONER_BACKEND` | `memory`, `docker`, or `kubernetes`. |
| `SANDBOX_IMAGE`, `SANDBOX_CONTAINER_PORT` | Docker sandbox image and port. |
| `SANDBOX_DOCKER_NETWORK_PREFIX` | Dynamic sandbox network prefix; do not reuse the app network name. |
| Kubernetes variables | Namespace, node host, kubeconfig, and PVC names for k8s backend. |

The Docker backend mounts the Docker socket into the provisioner. Treat it as a
privileged local service and keep it behind the internal Compose network.

## OCR configuration

Yuxi separates OCR engine selection from service credentials. Administrators can
choose a default OCR method; individual uploads can still choose another engine.

| Engine | Requirement | Config source |
| --- | --- | --- |
| `rapid_ocr` | CPU/local; default lightweight choice. | No external service required. |
| `mineru_ocr` | Self-hosted MinerU service, usually GPU. | `MINERU_API_URI` or admin MinerU service URL. |
| `mineru_official` | MinerU cloud API. | `MINERU_API_KEY` or admin secret. |
| `pp_structure_v3_ocr` | Self-hosted PaddleX service, usually GPU. | `PADDLEX_URI` or admin service URL. |
| `deepseek_ocr` | Cloud model-provider route. | Reuses the enabled `siliconflow-cn` provider Base URL and credential. |
| `paddleocr_vl_1_6`, `paddleocr_pp_ocrv6` | Baidu AI Studio cloud OCR. | `PADDLEOCR_API_URL` and `PADDLEOCR_API_TOKEN` or admin config. |

Sensitive OCR fields are returned to the frontend only as masked previews or as
source indicators, not raw environment variable values.

## API keys and external calls

Yuxi user API keys have the `yxkey_` prefix and are stored hashed. The complete
secret is shown only once when created. For production integrations:

- Use HTTPS.
- Store keys in a secret manager or environment variable.
- Create distinct keys per external system.
- Rotate or disable a key immediately if leakage is suspected.
- Remember that an API key acts with the permissions of its bound user.

## Langfuse and other observability credentials

Langfuse is optional. When `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and
`LANGFUSE_BASE_URL` are complete, API/agent execution can emit traces. Missing
or incomplete Langfuse credentials should degrade to no tracing rather than
blocking chat startup. Langfuse dataset upload/evaluation workflows write to an
external service; treat them as explicit side-effectful operations.
