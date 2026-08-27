---
name: interoperability-serving
description: "Router for OpenMed CLI, REST, gRPC, MCP, adapter registry, and
  interoperability handoffs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Interoperability and serving

Use this sub-skill for:
- one-shot CLI validation and transport-safe probes;
- REST, gRPC, or MCP service use;
- `OpenMedClient`, `create_app()`, and `TOOL_REGISTRY` wiring;
- adapter discovery and framework tool rendering;
- FHIR, OMOP, HL7 v2, C-CDA, OpenMRS, DHIS2, and OpenHIM handoffs;
- LangChain, Haystack, LlamaIndex, spaCy, SQL, and distributed connector wrappers.

## Route elsewhere when the task is about

- Model cache planning, backend selection, or runtime export → `model-runtimes-mobile`
- PHI redaction policy, reversible de-identification, or date shifting → `deidentification-privacy`
- Clinical entity interpretation, grounding, or note-level extraction → `clinical-extraction-grounding`

## Core surfaces

- CLI: `openmed`, `openmed.cli`, `openmed-mcp`
- REST/gRPC: `openmed.service.app.create_app`, `openmed.service.client.OpenMedClient`, `openmed.service.grpc_server`
- MCP: `openmed.mcp.server`, `openmed.mcp.tool_registry.TOOL_REGISTRY`
- Interop registry: `openmed.interop.available_adapters`, `adapter_tool_definitions`, `to_function_tools`, `to_tool_use_tools`
- Connector families: `openmed.interop.hl7v2`, `openmed.interop.cda`, `openmed.interop.fhir_operations`, `openmed.interop.fhir_server`, `openmed.interop.openmrs`, `openmed.interop.omop`, `openmed.interop.cdm_etl`, `openmed.interop.duckdb_udf`, `openmed.interop.langchain`, `openmed.interop.haystack`, `openmed.interop.llamaindex`, `openmed.interop.spacy_component`, `openmed.interop.search_pipeline`, `openmed.interop.spark_udf`, `openmed.interop.pandas_accessor`, `openmed.interop.polars_accessor`, `openmed.interop.beam_transform`, `openmed.interop.ray_data`, `openmed.interop.prefect_tasks`

## Default operating rules

- Prefer one-shot CLI for finite local tasks that can complete and exit.
- Prefer REST or gRPC when you need a shared warm pool, repeated calls, async jobs, streaming, or browser clients.
- Prefer MCP when an agent or IDE needs stable tool definitions and transport negotiation.
- Keep credentials, org-unit trees, FHIR profiles, OMOP vocab snapshots, and external EHR endpoints caller-supplied.
- Keep all examples synthetic and PHI-free.

## Bundled references

- `references/interop-serving-workflows.md`
- `references/cli-reference.md`
- `references/troubleshooting.md`
- `scripts/openmed_cli_probe.py`
