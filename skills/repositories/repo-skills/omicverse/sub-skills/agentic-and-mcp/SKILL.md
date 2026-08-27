---
name: agentic-and-mcp
description: "OmicVerse CLI, MCP server, registry manifest, JARVIS/gateway,
  smart agent, agent backend, skill seeker, and AI-assisted session workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Agentic and MCP

Use this sub-skill for OmicVerse command-line entry points, the MCP server, registry/manifest inspection, JARVIS and gateway workflows, smart-agent configuration, provider backends, `ov-skill-seeker`, and AI-assisted notebook/session execution.

For package-wide routing and installation strategy, return to [`../../SKILL.md`](../../SKILL.md).

## When to Use

- Inspect command-line routing for `omicverse`, `omicverse claw`, `omicverse jarvis`, `omicverse gateway`, `omicverse web`, `omicverse skill-seeker`, `omicverse-mcp`, or `ov-skill-seeker`.
- Configure an MCP-compatible client to discover OmicVerse registry tools through stdio or local `streamable-http` transport.
- Inspect registry manifests with `omicverse.mcp.build_default_manifest(...)`, `omicverse.mcp.get_manifest(...)`, or bundled `scripts/inspect_registry.py`.
- Use or debug JARVIS/gateway, one-shot `claw -q`, channel credentials, OpenAI/Gemini/Ollama/provider configuration, Codex/Gemini CLI OAuth, or web-launcher behavior.
- Use `omicverse.utils.smart_agent.Agent(...)`, `OmicVerseAgent`, `AgentConfig`, streaming events, approval policy, notebook execution, filesystem context, or harness traces.
- List, validate, package, or create bundled agent skills with `ov-skill-seeker`.

## Route Elsewhere

- Core AnnData IO, QC, preprocessing, plotting, report/provenance, and registry discovery from Python: [`../core-analysis/SKILL.md`](../core-analysis/SKILL.md).
- Single-cell annotation, integration, marker, trajectory, fate, communication, or perturbation analysis: [`../single-cell-workflows/SKILL.md`](../single-cell-workflows/SKILL.md).
- Bulk, enrichment, metabolomics, proteomics, microbiome, and table statistics: [`../multiomics-statistics/SKILL.md`](../multiomics-statistics/SKILL.md).
- Spatial, histology, deconvolution, mapping, and spatial IO workflows: [`../spatial-integration/SKILL.md`](../spatial-integration/SKILL.md).
- Genetics, AIRR, molecular, raw alignment, external binaries, and downloads: [`../specialist-domains/SKILL.md`](../specialist-domains/SKILL.md).

## Safe First Checks

Run help and read-only introspection before starting services or contacting providers:

```bash
python sub-skills/agentic-and-mcp/scripts/check_mcp_runtime.py --profile fast-mock
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --phase P0+P0.5 --limit 20
python sub-skills/agentic-and-mcp/scripts/inspect_registry.py --search pca --phase P0+P0.5 --show-schema
omicverse --help
omicverse-mcp --help
ov-skill-seeker --help
```

Expected signals:

- `check_mcp_runtime.py` prints JSON with package versions, executable availability, MCP public API flags, and CLI help flags.
- `inspect_registry.py` prints JSON with `tool_count`, selected `tools`, execution-class/category counts, and no network listener.
- `omicverse-mcp --help` lists `--phase`, `--transport`, `--session-id`, `--persist-dir`, `--max-adata`, `--max-artifacts`, `--host`, `--port`, and `--http-path`.

## Service-Gated Commands

Do not start long-running services as a default validation step. Start these only when the user explicitly asks for a service or MCP client integration:

```bash
omicverse-mcp --phase P0+P0.5 --transport stdio
python -m omicverse.mcp --phase P0 --transport stdio
python -m omicverse.mcp --phase P0+P0.5 --transport streamable-http --host 127.0.0.1 --port 8765 --http-path /mcp
omicverse claw -q "show code to QC this AnnData object"
omicverse gateway --web-host 127.0.0.1 --web-port 5050 --no-browser
```

Use `stdio` MCP only with clients that keep stdout reserved for JSON-RPC. Use local `streamable-http` only when a network listener is acceptable and the user has approved host/port binding.

## References

- [`references/mcp-and-cli.md`](references/mcp-and-cli.md): console scripts, MCP phases/transports, manifests, meta tools, session/persistence limits, and skill seeker commands.
- [`references/agent-runtime.md`](references/agent-runtime.md): JARVIS/gateway, smart agent factory, `AgentConfig`, provider/auth modes, streaming, notebook/session behavior, and permission policy.
- [`references/troubleshooting.md`](references/troubleshooting.md): missing extras, stdio pollution, startup timeouts, registry hydration, credentials, persistence/quota errors, gateway/web imports, and sandbox policy.
