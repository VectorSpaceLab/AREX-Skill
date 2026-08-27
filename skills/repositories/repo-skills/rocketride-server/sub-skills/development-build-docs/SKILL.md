---
name: development-build-docs
description: "Guide RocketRide contributors through builder tasks, workspace
  setup, docs generation, contract freezes, tests, linting, and related
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Development, Build, and Docs

Use this sub-skill when a task is about RocketRide contributor workflows: choosing
safe builder tasks, setting up the pnpm workspace, updating co-located docs after
public contract changes, regenerating generated references, freezing/checking API
contracts, selecting focused tests or lint checks, and troubleshooting build/doc
infrastructure failures.

## Use this for

- `./builder` task discovery, module action selection, global `build`/`test`,
  and focused module `:build`, `:test`, `:clean`, `:docs-*`, or contract tasks
- pnpm workspace setup, Node/pnpm version mismatches, and Corepack/pnpm-missing
  failures
- Co-located documentation ownership for nodes, SDKs, MCP, engine protocol,
  `.pipe` schema, VS Code extension, and docs spine pages
- Generated docs/reference workflows: `nodes:docs-generate`,
  `client-typescript:docs-generate`, and `docs:build`
- TypeScript SDK API contract floors: `client-typescript:freeze`, `:check`,
  and `:regen`
- Focused test/lint/format command planning for PRs without doing unrelated
  repository refactors
- Maintenance checks such as third-party interface contract checks and model
  profile sync workflows

## Do not use for

- End-user runtime startup, Docker/Helm, Cloud/self-hosted deployment, or port
  `5565` protocol operations -> `../runtime-deployment/SKILL.md`
- Python or TypeScript SDK method usage and client code examples ->
  `../sdk-clients/SKILL.md`
- `.pipe` workflow authoring, lane wiring, or pipeline recipes ->
  `../pipeline-authoring/SKILL.md`
- Node service schema field semantics and provider catalog details ->
  `../nodes-catalog/SKILL.md`
- MCP server, n8n, assistant-tool, or webhook integration behavior ->
  `../mcp-and-integrations/SKILL.md`
- VS Code extension UX and app descriptor behavior -> `../ide-and-apps/`

## Route first

- Read [builder and tasks](references/builder-and-tasks.md) for the builder
  action model, workspace setup, global commands, focused module commands, and
  task-authoring rules.
- Read [docs, contracts, and tests](references/docs-contracts-and-tests.md) for
  the co-located docs rule, generated docs commands, API contract freeze/check
  rules, tests, linting, model sync, and check-externals workflows.
- Read [troubleshooting](references/troubleshooting.md) when pnpm/Corepack is
  missing, builder discovery fails, docs generation skips or drifts, contract
  floors fail, tests start unexpected services, or model sync/check-externals
  reports confusing output.

## Operating guardrails

- Treat documentation as part of a public contract change, not a follow-up. If a
  public input, output, config schema, SDK signature, protocol surface, `.pipe`
  schema, or extension surface changes, update the owning co-located docs in the
  same change.
- Never hand-edit generated regions such as the node README block between
  `ROCKETRIDE:GENERATED:PARAMS` markers or generated TypeScript pipeline
  reference output. Change the source contract and run the generator.
- Prefer focused tasks over `./builder build` or `./builder test` when the user
  only changed one area. Many builder tests assemble the engine or start a
  temporary test server.
- Do not start long-running dev servers (`docs:dev`, `docs:serve`, `server:run`,
  `server:dev`) unless the user explicitly asks for an interactive service.
- Do not run provider/network model sync, Docker/Kubernetes, engine source
  builds, or credential checks as a passive troubleshooting step.

## Good output for contributor tasks

- Names the changed public surface and its required co-located docs owner
- Lists the generated artifacts that must not be edited by hand
- Gives the smallest adequate builder/test/lint command set and expected signal
- Calls out heavy commands, service-starting commands, and credential/network
  requirements before suggesting them
- Separates documentation generation, API contract freezing, and runtime
  deployment concerns instead of mixing them into one task
