# Interoperability and serving workflows

This note summarizes the safe, local-first workflows covered by this sub-skill.
All examples are synthetic and should stay inside a trusted runtime.

## 1) Choose the surface

| Need | Prefer | Why |
| --- | --- | --- |
| One local command with a result that can exit | CLI | No daemon, easy shell use, stable JSON envelopes when requested |
| Repeated HTTP calls or browser clients | REST | Shared warm pool, auth, health checks, async jobs, and CORS controls |
| Typed RPC or server-streamed de-identification | gRPC | Schema-first contracts with the same service runtime as REST |
| Agent or IDE tool access | MCP | Tool registry, prompts, and resources with standard transport negotiation |
| In-process Python integration | `OpenMedClient` or `create_app()` | Typed local wrapper and importable app factory |
| Framework tool rendering | Registry adapters | One canonical tool spec rendered for multiple agent ecosystems |

### Rule of thumb

- If the task can finish in one call and the output can live in stdout or a file,
  use the CLI.
- If the task needs a daemon, shared state, or browser-facing access, use REST.
- If the caller needs streaming RPC or typed protobuf contracts, use gRPC.
- If an agent or editor needs tools, use MCP or a rendered adapter view.
- Do not expand this skill to model-cache or backend-selection work.

## 2) Service surfaces

### REST

The REST service is the HTTP surface for local or networked callers. Its safe
uses include health checks, loaded-model inspection, single-request analysis,
PII extraction and de-identification, privacy-gateway handoff, async jobs, and
OMOP/cohort operations.

Useful client entry points:

- `openmed.service.app.create_app()` for an importable FastAPI app
- `openmed.service.client.OpenMedClient` for a typed sync client
- `openmed.service.client.OpenMedAPIError` for non-2xx responses

The client methods mirror the service paths:

- `analyze`
- `extract_pii`
- `extract_pii_stream`
- `deidentify`
- `privacy_gateway`
- `loaded_models`
- `unload_model`
- `unload_all_models`

`OpenMedAPIError` carries the HTTP status, stable `code`, human `message`,
optional `details`, and the `request_id` when the service returns one.

### gRPC

The gRPC service uses the same runtime as REST. It is a good fit when a caller
wants typed protobuf contracts or server-streamed redaction.

Core RPCs:

- `Analyze`
- `Extract`
- `Deidentify`
- `StreamDeidentify`

The gRPC and REST surfaces should be kept in sync when a request schema changes.

### MCP

The MCP server exposes the same canonical tool set to agents and IDE clients.
Use it when the consumer wants tool calls instead of HTTP endpoints.

- Local stdio is the default transport.
- Streamable HTTP is for loopback or authenticated network use.
- Tool and workflow metadata come from `openmed.mcp.tool_registry.TOOL_REGISTRY`.

## 3) Adapter registry and tool rendering

The interop registry is dependency-light and can enumerate built-in adapters
without importing optional third-party packages.

Use it to:

- discover which connector families are registered;
- render framework-specific tool definitions from one canonical registry;
- keep agent integrations in sync with MCP tool shapes.

Core calls:

- `openmed.interop.available_adapters(include_plugins=False)`
- `openmed.interop.adapter_tool_definitions(name)`
- `openmed.interop.to_function_tools()`
- `openmed.interop.to_tool_use_tools()`
- `openmed.interop.get_langchain_tools()`
- `openmed.interop.get_llamaindex_tools()`

Built-in adapter families relevant to this sub-skill include:

- agent and workflow renderers: `function_tools`, `langchain`, `llamaindex`
- document and NLP connectors: `cda`, `hl7v2`, `fhir_server`, `openmrs`
- tabular and distributed connectors: `duckdb`, `pandas`, `polars`, `spark`, `ray`, `beam`, `prefect`
- pipeline and component wrappers: `haystack`, `search_pipeline`, `spacy`
- clinical exchange and mapping helpers: `omop`, `cdm_etl`
- additional optional interop families: `presidio`, `pydeid`, `scrubadub`, `philter`, `quickumls`, `scispacy_linker`, `gliner_biomed`, `indic`, `zh`

## 4) Interop handoff patterns

### FHIR

Use local shaping, validation, and bundle assembly. Keep OperationOutcome-style
messages PHI-free and path-based. When a task needs round-trip conformance,
record what was preserved and what was intentionally lossy.

### OMOP

Treat vocabulary snapshots as caller-supplied inputs. Keep unknown mappings at
`concept_id = 0` with an explicit reason instead of guessing.

### HL7 v2

Redact structured fields before rendering narrative text. Preserve segment order,
field numbers, and offsets. The rendered text should still be useful for local
review or downstream NLP.

### C-CDA

Keep the XML parseable. Redact structured header PHI and section narrative,
but do not disturb the CDA markup.

### OpenMRS

Pull on the facility-controlled side, de-identify locally, review transformed
paths, then export or dry-run write-back. Prefer a dry run before any real
handoff.

### DHIS2

Generalize org units, remove precise geometry, suppress small cells, and emit
local aggregate/tracker/manifest JSON for review before upload.

### OpenHIM

Register and heartbeat inside a trusted HIE boundary. Keep mediator management
credentials out of payloads and send only de-identified traffic through the
mediator channel.

## 5) Synthetic quickstart patterns

These are the distilled, synthetic workflows that belong in this sub-skill:

- privacy gateway: redact locally, forward only redacted text to a caller-owned
  function, then restore the response locally when authorized;
- agent tools: render function-calling, tool-use, LangChain, and LlamaIndex
  views from one registry;
- OpenMRS handoff: pull Patient/Encounter/Observation resources, export NDJSON,
  and only then consider a dry-run write-back;
- DHIS2 export: combine aggregate and tracker snapshots with org-unit data,
  de-identify in memory, and write the local review artifacts.

## 6) Output and safety reminders

- Keep examples synthetic and PHI-free.
- Use paths and hashes instead of raw identifiers in diagnostics.
- Treat service and adapter outputs as local operational artifacts, not clinical
  decisions.
- If a task needs privacy semantics rather than transport wiring, route it to
  the privacy sub-skill instead of extending this one.
