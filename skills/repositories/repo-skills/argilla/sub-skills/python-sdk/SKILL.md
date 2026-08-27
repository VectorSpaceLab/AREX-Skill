---
name: python-sdk
description: "Operate the Argilla 2.x Python SDK for datasets, records, search,
  import/export, users, workspaces, webhooks, and SDK troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Argilla Python SDK

Use this sub-skill when a task asks you to use Argilla 2.x from Python: connect to an Argilla server, define dataset settings, log records, map incoming data to fields/questions/metadata/vectors, search/filter/export records, manage users/workspaces, or build a webhook listener.

Do not use this sub-skill for server deployment, Docker/Kubernetes, search-engine reindexing, OAuth/SSO service configuration, or legacy v1/Rubrix migration. Route those to the sibling `server-ops` or `legacy-migration` sub-skill.

## First-choice references

- Read [`references/api-reference.md`](references/api-reference.md) when you need verified Argilla 2.8.0dev0 SDK signatures, object relationships, collection accessors, or event names.
- Read [`references/workflows.md`](references/workflows.md) when you need end-to-end recipes for connecting, creating datasets, logging data, searching/filtering, import/export, users/workspaces, or webhooks.
- Read [`references/data-formats.md`](references/data-formats.md) when you must format field/question values, record mappings, flatten/export columns, markdown/media, images, chat data, custom fields, metadata, vectors, or external ids.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when SDK calls fail due to credentials, API URL, default client, schema collisions, record mappings, images/chat/custom fields, vectors/search, Hub tokens, private Spaces, or webhooks.

## Bundled helpers

- Run [`scripts/build_dataset_template.py --help`](scripts/build_dataset_template.py) when you need a safe offline generator that prints or writes a minimal Python dataset/settings/records template; the helper itself never contacts an Argilla server.
- Run [`scripts/webhook_listener_template.py --help`](scripts/webhook_listener_template.py) when you need a safe FastAPI webhook listener skeleton; it does not create, register, delete, or serve live webhooks unless the user explicitly passes live-server arguments.

## Operating rules

1. Treat the Python SDK as service-backed: `rg.Argilla(...)`, `create`, `update`, `delete`, `records.log`, `to_hub`, `from_hub`, and webhooks can contact a server or network service.
2. Prefer explicit clients. Create `client = rg.Argilla(api_url=..., api_key=...)` before constructing SDK resources if environment defaults are not guaranteed, and pass `client=client` to datasets and user/workspace/webhook resources where supported.
3. Keep dataset setting names unique across fields, questions, metadata properties, and vector fields. Use simple stable names, then map arbitrary source columns with `dataset.records.log(..., mapping=...)`.
4. Use `Record(id=...)` or mapping target `id` for the record external id. The SDK serializes this as `external_id` internally, but the public constructor/mapping target is `id`.
5. Use safe templates for webhooks. The `webhook_listener` decorator registers webhooks when it is executed, so do not place it at module import time unless the user intentionally wants registration.
