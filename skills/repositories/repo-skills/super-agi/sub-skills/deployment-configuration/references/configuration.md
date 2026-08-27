# SuperAGI Configuration Reference

## When to Read

Read this before creating or modifying `config.yaml`, debugging service host
names, or deciding which credentials are required for a capability.

## Configuration Loading Behavior

SuperAGI loads a YAML file named `config.yaml` from the repository root and then
merges environment variables over the YAML values. Environment variables can
therefore override template values at runtime. If `config.yaml` is absent,
`superagi.config.config.Config.load_config` creates an empty file and logs a
prompt-like message; service startup will then fail later if required values are
missing.

## Required Cross-Cutting Keys

| Key | Purpose | Notes |
|---|---|---|
| `DB_NAME`, `DB_HOST`, `DB_USERNAME`, `DB_PASSWORD`, `DB_URL` | PostgreSQL connection. | If `DB_URL` is set, source code parses it and uses its scheme/netloc/path. Docker defaults use `super__postgres`. Host-local runs often need a different host. |
| `REDIS_URL` | Celery broker/result backend and task queue storage. | Docker default is `super__redis:6379`; host-local is usually `localhost:6379`. |
| `STORAGE_TYPE` | Resource storage backend. | `FILE` and `S3` are the main code paths. S3 requires bucket and AWS credentials. |
| `TOOLS_DIR` | Local tool directory. | Default evidence uses `superagi/tools`. |
| `MODEL_NAME`, `RESOURCES_SUMMARY_MODEL_NAME` | Default model selections. | Provider-specific setup is in `models-resources-vector`. |
| `MAX_TOOL_TOKEN_LIMIT`, `MAX_MODEL_TOKEN_LIMIT` | Tool/model token budgets. | Used by prompt/tool helpers and model settings. |
| `JWT_SECRET_KEY`, `JWT_EXPIRY` | JWT auth. | The template uses weak placeholder-style values; replace for real deployments. |
| `ENCRYPTION_KEY` | Toolkit secret encryption/decryption. | Required for stored toolkit credentials. |

## Provider and Tool Credentials

The template contains placeholders for OpenAI, Google Palm, Replicate, Hugging
Face, Pinecone, Google Search/Serp, email, GitHub, Jira, Slack, Twitter,
Instagram/S3, and image generation keys. Do not validate or use these providers
until the downstream user supplies real credentials and authorizes network
calls.

## Local LLM Configuration

`OPENAI_API_BASE` defaults to OpenAI-compatible hosted API. For local text
generation web UI, the template comments show an internal Docker endpoint using
`super__tgwui:5001/v1`. Switching to local LLM also requires matching model
name, token limits, the local LLM service, and possibly GPU compose support.

## Vector and Resource Configuration

`RESOURCE_VECTOR_STORE` can select vector storage for resource summaries. The
source enum recognizes Redis, Pinecone, Chroma, Weaviate, Qdrant, and LanceDB,
while factory implementations primarily cover Redis/Pinecone/Weaviate/Qdrant in
this checkout. Read the vector sub-skill before claiming a backend is ready.

## Validation

Use the root `scripts/check_superagi_config.py` helper for shape and placeholder
checks. The helper intentionally does not contact providers, start databases, or
validate tokens. A config can pass shape checks and still fail if credentials,
network, Docker services, or vector DB instances are unavailable.
