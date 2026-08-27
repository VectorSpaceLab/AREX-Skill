---
name: pipelines-integrations
description: "Operate ClawBio's optional MCP stdio server, messaging and web
  adapters, provider bridges, and nf-core Nextflow wrappers with explicit
  safety, credential, network, and preflight boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Pipelines and Integrations

Use this sub-skill for integrations around ClawBio rather than for the
scientific interpretation itself. It covers the optional MCP server, RoboTerri
Telegram/Discord/WhatsApp adapters, Robotary/OpenClaw web routes, the FLock
provider bridge, and the `scrnaseq-pipeline`, `rnaseq-pipeline`, and
`sarek-pipeline` wrappers.

## Route

- MCP discovery, stdio setup, demo-only defaults, or local-file opt-in: read
  [references/integrations.md](references/integrations.md).
- Telegram, Discord, WhatsApp, Robotary, OpenClaw webchat, provider credentials,
  file handling, or structured chat follow-up: read
  [references/integrations.md](references/integrations.md).
- Any nf-core/Nextflow command, profile, reference, resume, `--check`, network,
  container, or large-data question: read
  [references/pipeline-preflight.md](references/pipeline-preflight.md).
- A missing optional dependency, credential, binary, stale resume, rejected
  input, or failed handoff: read
  [references/troubleshooting.md](references/troubleshooting.md).
- For ordinary ClawBio skill execution, output inspection, or reproducibility
  bundles, hand off to [core-runner](../core-runner/SKILL.md).

## Operating procedure

1. Establish the boundary before acting: package importability is not service
   readiness; an installed optional module is not proof that credentials,
   network access, a webhook, a gateway, Nextflow, a container backend, or
   references are usable.
2. Prefer safe, non-starting diagnostics with
   [scripts/check_integrations.py](scripts/check_integrations.py). Run its
   `--help` first when unfamiliar. It only probes imports and executable
   availability, and an optional CLI help probe; it never starts a bot, MCP
   transport, web server, or Nextflow run.
3. For MCP, use `clawbio mcp` over stdio. Keep the default demo-only policy;
   local input/output access requires an explicit operator environment opt-in.
   Do not place secrets or patient paths in a client configuration.
4. For bots and web adapters, collect only the platform/provider settings
   required for the chosen adapter, keep identities and received files scoped
   to the sender/session, and treat platform APIs and external LLMs as network
   boundaries. Never echo or log credentials.
5. For a pipeline, choose one exact wrapper command, a fresh output directory,
   an explicit backend/profile and reference strategy, then run `--check`
   before a real run. Use only flags documented in the wrapper contract or the
   ClawBio registry allowlist; do not invent Nextflow parameters.
6. Preserve the wrapper's preflight decisions. Do not bypass local-first remote
   input checks, config trust checks, output-location checks, version pins,
   or resume incompatibility errors. Long runs and large references need an
   explicit disk/network/container budget.
7. After execution, inspect `result.json`, `report.md`, logs, and any preferred
   artifact before offering a follow-up. Pass confirmed artifacts to the
   relevant core/domain skill; do not infer a handoff from an exit code alone.

## Safety boundary

- Do not run live credentials, network calls, long pipelines, containers, or
  large reference/model/data downloads while drafting or diagnosing this
  sub-skill.
- MCP demo execution is the safe default. `CLAWBIO_MCP_ALLOW_LOCAL_FILES=1`
  is a deliberate exception that can expose local genomic data and outputs.
- Messaging adapters necessarily contact their platform and configured LLM;
  that is distinct from ClawBio's local computation guarantee. WhatsApp
  webhook requests fail closed without a valid app-secret signature, and
  public sender access must be explicit.
- Nextflow configs are trusted Groovy code, not a sandbox. Remote inputs,
  iGenomes, containers, conda environments, Wave, and object-store work dirs
  can require network access and substantial storage.
- Keep ClawBio's research/educational disclaimer and direct medical questions
  within the domain skill's safety contract.

## Handoff contract

A successful integration run returns a structured result or an adapter-visible
bundle. Use `result.json` fields such as `workflow_state`,
`chat_summary_lines`, `preferred_artifacts`, `suggested_actions`, and
`contract_alerts` when present. An action offer is a stored structured request,
not fresh shell text: execute it only through the normal runner path. Pipeline
wrappers commonly expose a confirmed `preferred_h5ad`,
`preferred_counts_tsv`, VCF inventory, or downstream command template. Point
ordinary output interpretation to [core-runner](../core-runner/SKILL.md) and
scientific follow-up to the named domain skill.
