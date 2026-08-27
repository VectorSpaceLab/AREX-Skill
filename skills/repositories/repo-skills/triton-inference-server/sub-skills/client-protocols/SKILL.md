---
name: client-protocols
description: "Build and troubleshoot Triton KServe HTTP/gRPC request payloads
  and client-side protocol usage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Client Protocols

Use this sub-skill when the user needs Triton HTTP/gRPC request shapes, health/metadata queries, binary input encoding, shared-memory guidance, or client-library request recipes.

## Route Within This Sub-skill

- **KServe v2 HTTP/gRPC payload structure, health, metadata, repository-control, binary data, and status mapping**: read [`references/kserve-http-grpc.md`](references/kserve-http-grpc.md).
- **Client-library recipes, curl vs Python client, streaming, timeouts, and shared-memory usage**: read [`references/client-library-recipes.md`](references/client-library-recipes.md).
- **Transport mismatches, tensor name/shape/datatype mistakes, invalid argument responses, and binary/body encoding problems**: read [`references/troubleshooting.md`](references/troubleshooting.md).
- **Helper to build request descriptors without contacting a live server**: run [`scripts/build_kserve_request.py`](scripts/build_kserve_request.py).

If the user needs to author the model repository or config, route to [`../model-repository-and-config/SKILL.md`](../model-repository-and-config/SKILL.md). If the user is launching Triton or checking metrics/ports, route to [`../server-runtime-and-deployment/SKILL.md`](../server-runtime-and-deployment/SKILL.md).

## Safe Default Workflow

1. Confirm the target endpoint family: HTTP/REST or gRPC.
2. Identify the model name, version, tensor names, shapes, and datatypes from repository/config or metadata.
3. Build a request descriptor or curl/client example with the bundled helper before sending anything live.
4. Distinguish KServe `/v2/*` payloads from Triton's OpenAI-compatible `/v1/*` payloads.
5. Use live metadata or a ready endpoint only when the user explicitly allows contacting a server.
