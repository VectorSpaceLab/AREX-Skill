---
name: servers-and-remote
description: "Use for Feast feature servers, offline servers, registry servers,
  transformation servers, MCP, remote stores, TLS, auth/RBAC, and production
  serving topology choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Feast Servers and Remote Stores

Use this sub-skill when the user asks to run or diagnose Feast serving processes, expose online or offline features over HTTP/gRPC/Arrow Flight, configure remote registry/online/offline stores, enable TLS, attach auth tokens, reason about RBAC denials, or choose a production serving topology.

## Route first

- Use this skill for `feast serve`, `feast serve_offline`, `feast serve_registry`, `feast serve_transformations`, server host/port/TLS flags, `registry_ttl_sec`, feature-server routes, registry REST/gRPC, Arrow Flight offline serving, MCP server configuration, remote store YAML, auth headers, and RBAC permissions.
- Route feature repository layout, `feature_store.yaml` discovery, `feast init`, `feast apply`, `feast plan`, and registry file paths to `../feature-repos-and-cli/SKILL.md`.
- Route `Entity`, `FeatureView`, `FeatureService`, `Permission`, policy object definitions, and schema modeling to `../feature-definitions/SKILL.md`.
- Route in-process SDK retrieval semantics, `FeatureStore.get_online_features`, `get_historical_features`, `materialize`, and `push` workflows to `../retrieval-and-materialization/SKILL.md`.
- Route vector document retrieval and RAG-specific online-store choices to `../rag-and-vector-search/SKILL.md`.
- Route optional backend extras, custom stores/providers, and contributor implementation work to `../integrations-and-extensibility/SKILL.md` or `../repo-development/SKILL.md`.

## Fast workflow

1. Identify which process owns the task: online feature server, offline Arrow Flight server, registry server, transformation server, or MCP-enabled feature server.
2. Confirm the feature repo is already applied and the server process can read its `feature_store.yaml`, registry, credentials, and configured stores.
3. Pick local vs remote clients: direct SDK calls use in-process stores; remote clients set `registry`, `online_store`, or `offline_store` to `type: remote` and point at the relevant server.
4. If TLS is required, always pass both server `--key` and `--cert`, then configure client `cert` or trust-store environment variables.
5. If auth is enabled, decide whether the request needs REST, gRPC, or Arrow token propagation, then verify permissions separately from missing Feast objects.

## References

- `references/server-reference.md` for server command choices, routes, ports, config snippets, MCP, and topology selection.
- `references/auth-and-rbac.md` for `no_auth`, OIDC/Kubernetes auth, token patterns, RBAC actions, and 401/403 diagnosis.
- `references/remote-stores.md` for remote registry, online store, offline store, TLS client config, and production layout examples.
- `references/troubleshooting.md` for install/import, CLI, config, service credentials, network, TLS, auth, and backend failure signals.
- `scripts/server_smoke_check.py` for safe CLI/config checks and optional explicit server command execution.
