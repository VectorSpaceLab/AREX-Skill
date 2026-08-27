# Docs, Contracts, and Tests

Use this reference to map a contributor change to required docs, generated
artifacts, API contract tasks, tests, and lint/format checks. It encodes the
repository's co-located docs rule so a public contract change does not ship with
stale documentation.

## Co-located docs rule

When a change alters a public contract, update the corresponding co-located doc
in the same change. Prose-only edits and internal refactors that do not change a
public contract do not require extra generated docs work.

| Changed public surface | Update the co-located docs owner | Generated/verification command |
|---|---|---|
| Node inputs, outputs, or config schema | Node prose in `nodes/src/nodes/<node>/README.md` | `./builder nodes:docs-generate` and usually `./builder docs:build` |
| Node service definition behavior or optional dependency | Node README prose plus tests near the node | `./builder nodes:test-contracts` or a focused `./builder nodes:test --pytest="-k <pattern>"` |
| Public TypeScript SDK signature | `packages/client-typescript/docs/` | `./builder client-typescript:freeze` for the current package minor, then `./builder client-typescript:check` |
| `.pipe` schema in the TypeScript types | `packages/client-typescript/src/client/types/pipeline.ts` plus explanatory docs | `./builder client-typescript:docs-generate` and `./builder docs:build` |
| Public Python SDK signature | `packages/client-python/docs/` | `./builder client-python:test` or focused Python tests; full docs build gathers the docs |
| MCP protocol surface | `packages/client-mcp/docs/` | `./builder client-mcp:test` or focused MCP tests; full docs build gathers the docs |
| WebSocket / engine protocol surface | `packages/server/docs/` | Engine/runtime tests as appropriate; full docs build gathers the docs |
| VS Code extension surface | `apps/vscode/docs/` | `./builder vscode:build` or extension-focused checks as appropriate |
| Spine/landing pages, Quickstart, Concepts, Cloud, Troubleshooting, Glossary, Cursor/Windsurf stubs | `packages/docs/content-static/` | `./builder docs:test` and `./builder docs:build` |

Do not create a separate docs repository or a new top-level docs site folder.
The docs site is assembled from co-located package/app/node docs.

## Node README generated block

Node READMEs contain hand-authored prose plus an optional generated block between
these exact markers:

```md
<!-- ROCKETRIDE:GENERATED:PARAMS START -->
...
<!-- ROCKETRIDE:GENERATED:PARAMS END -->
```

Rules:

- Never hand-edit content inside that block.
- Update the node's `services*.json`, requirements file, and hand-authored
  README prose outside the block.
- Run `./builder nodes:docs-generate` to regenerate the block from service JSON
  and requirements data.
- `nodes:build` also runs node docs generation after syncing nodes.
- The generator only updates READMEs that carry the markers. Nodes without a
  marked README are skipped rather than modified blindly.
- In the current generator, comments are stripped before JSON parsing, but the
  post-strip content must still parse as JSON. Treat trailing commas or malformed
  strings as generator-breaking syntax.
- The generator can skip on non-release-track feature branches because generated
  source links include the branch name. Do not fix that by editing the block by
  hand; run the generator in an allowed branch context or document the required
  release-branch regeneration step.

## Docs build pipeline

`./builder docs:build` performs this high-level pipeline:

1. Run lightweight reference generators in parallel:
   - `nodes:docs-generate`
   - `client-typescript:docs-generate`
2. Gather co-located docs from modules into the docs content build tree.
3. Build the LLM/docs index.
4. Run Docusaurus build and emit the static site to `dist/docs`.

Related tasks:

| Command | Use |
|---|---|
| `./builder docs:build` | Build the static docs site after docs or generated-reference changes. |
| `./builder docs:test` | Run pure docs helper tests. |
| `./builder docs:clean` | Remove generated docs outputs and cached docs state. |
| `./builder docs:dev` | Start an interactive docs dev server; do not run unless requested. |
| `./builder docs:serve` | Serve `dist/docs`; requires a prior docs build and starts a long-running process. |

## TypeScript SDK API contract floors

The TypeScript SDK has a structural public API floor managed by
`client-typescript:freeze`.

What the freeze does:

- Bundles the public SDK surface from `src/client/index.ts` into a self-contained
  declaration floor for the current package `MAJOR.MINOR`.
- Stores the floor under the package contract versions area.
- Regenerates derived contract barrels and the conformance check file.
- Treats older floors as immutable. Re-freezing is only appropriate for the
  current in-progress minor.
- Enforces removals/narrowings through TypeScript compilation against all frozen
  floors; additive current-minor work is allowed.

Commands:

| Command | Meaning |
|---|---|
| `./builder client-typescript:freeze` | Mint or replace the floor for the current package minor and regenerate derived artifacts. Use after intentional public TypeScript SDK signature changes. |
| `./builder client-typescript:check` | CI/publish mode. Verifies floors, verifies a floor exists for the current package version, and writes nothing. |
| `./builder client-typescript:regen` | Regenerate derived artifacts from immutable floors and verify. On a clean tree this should be a no-op; pair with `git diff --exit-code` in CI-like checks. |
| `./builder client-typescript:build` | Builds the package and runs a floors-only gate before packaging, then regenerates the pipeline reference. |

Do not edit older frozen floors to make a breaking API change pass. Either keep
backward compatibility, intentionally version the change, or ask for maintainer
direction.

## `.pipe` schema and generated pipeline reference

The `.pipe` JSON schema is owned by the TypeScript pipeline type definitions.
When that schema changes:

1. Update the schema/type definitions and any explanatory prose in the
   TypeScript client docs.
2. Run `./builder client-typescript:docs-generate` to regenerate the pipeline
   reference page.
3. Run `./builder docs:build` before treating docs verification as complete.
4. Do not hand-edit the generated pipeline reference as a shortcut.

Route schema semantics and sample `.pipe` repair to the pipeline-authoring
sub-skill; this sub-skill only owns the contributor docs/build workflow.

## Python, MCP, server, and app docs

Python SDK, MCP, WebSocket/server, VS Code, and spine docs are gathered into the
docs site from co-located docs directories. In the inspected task files, the
explicit generated-reference actions are node docs and TypeScript pipeline
reference generation; full docs verification still uses `./builder docs:build`.

Suggested focused checks:

| Surface | Focused checks before full docs build |
|---|---|
| Python SDK docs/API | `./builder client-python:test` or selected Python SDK pytest files if the environment is already prepared. |
| MCP docs/API | `./builder client-mcp:test` or selected MCP pytest files if the environment is already prepared. |
| Server protocol docs | A targeted engine/protocol check when changing executable behavior; otherwise docs build and review may be enough. |
| VS Code docs | `./builder vscode:build` for extension packaging/build changes. |
| Docs spine/content-only changes | `./builder docs:test` plus `./builder docs:build`. |

## Third-party interface contract checks

The check-externals framework catches upstream Python package interface drift for
third-party imports used by nodes, AI modules, the Python client, and engine-side
Python runtime code. It loads modules and inspects attributes; it does not call
real provider APIs.

Commands:

| Command | Use | Cost |
|---|---|---|
| `./builder check-externals:run` | Full interface scan after relevant Python dependency/API changes. | Heavy: builds server, nodes, AI, and Python client first. |
| `./builder check-externals:run --pattern=<substr>` | Focus on one node/package/component pattern. | Still builds prerequisites. |
| `./builder check-externals:test` | Unit tests for the framework itself. | Lighter; builds only the engine first. |
| `./builder check-externals:run --rebuild-cache --install-all` | Nightly-style fresh constraints and all optional installs. | Very heavy; do not use as a routine local PR check. |

When optional/heavy dependencies are intentionally skipped, use the framework's
markers on the owning import or requirements file with a short reason. Do not
silence a real upstream break by deleting coverage without explaining why.

## Model profile sync

The model sync tool refreshes LLM provider profile lists in node `services.json`
files. It can read provider APIs, OpenRouter data, and LiteLLM data. Without
`--apply`, the direct Python script is dry-run. The builder action runs sync and
then Prettier on target service files, so it may still format files even when the
sync itself is dry-run.

Common commands:

```bash
# Pure dry-run, no writes from the sync tool itself
python tools/sync_models/src/sync_models.py --provider llm_openai

# Builder path: sync then format target services.json files
./builder models:update --models="--provider llm_openai --apply"

# All providers, writing changes; requires careful review and credentials where available
./builder models:update --models="--all --enable-discovery --apply"
```

Rules:

- Default mode enriches existing profiles and does not add new ones.
- `--enable-discovery` allows new profiles to be added.
- Strict discovery adds provider-discovered models only when the provider API key
  is available.
- `--allow-fallback-discovery` permits OpenRouter/LiteLLM discovery for missing
  provider keys and can introduce aliases that do not work with the native SDK;
  use only with explicit reviewer awareness.
- Keep provider API keys in environment variables or `.env`; do not put secrets
  in service JSON.

Offline tool tests:

```bash
pytest tools/sync_models/test/test_sync_logic.py
```

Live sync tests are skipped when provider keys are absent; do not convert them
into mandatory checks for ordinary PRs.

## Lint and format checks

There is no single root npm script that replaces the builder. Use the tool that
matches the changed surface:

| Surface | Typical command |
|---|---|
| Python style | `python -m ruff check <paths>` and optionally `python -m ruff format <paths>` if Ruff is installed. |
| Python tests | `python -m pytest <test-path> -q` for focused direct tests, or the corresponding `./builder <module>:test` when engine/runtime setup is required. |
| TypeScript/JS lint | `pnpm exec eslint <paths>` after workspace install. |
| Prettier format/check | `pnpm exec prettier --check <paths>` or `pnpm exec prettier --write <paths>`. |
| TypeScript compile | Prefer `./builder client-typescript:build`, `./builder vscode:build`, or the owning module build task instead of ad-hoc `tsc`. |
| Docs helpers | `./builder docs:test`. |

The root Python tooling configuration uses Ruff with single-quote formatting for
inline strings, a high line-length ceiling, and pytest defaults such as verbose
output, short tracebacks, strict markers, and a per-test timeout. Package-level
Python projects may add their own optional `dev`/`test` dependencies.

## Suggested PR validation patterns

| Change type | Smallest useful validation set |
|---|---|
| Node `services.json` or node README | `./builder nodes:docs-generate`, `./builder nodes:test-contracts` or focused node tests, then `./builder docs:build` if docs are part of the change. |
| TypeScript SDK public API | `./builder client-typescript:freeze`, `./builder client-typescript:check`, `./builder client-typescript:test`, and docs build if docs changed. |
| `.pipe` schema | `./builder client-typescript:docs-generate`, `./builder client-typescript:build`, docs build, plus pipeline-authoring static checks for examples if applicable. |
| Python SDK public API | Focused Python SDK tests or `./builder client-python:test`, docs update, docs build. |
| MCP protocol/config | Focused MCP tests or `./builder client-mcp:test`, docs update, docs build. |
| Docs-only spine page | `./builder docs:test` and `./builder docs:build`. |
| Dependency import/API drift | `./builder check-externals:run --pattern=<component>` or the full check-externals run when warranted. |
| Model list refresh | Direct dry-run first, then `./builder models:update --models="... --apply"`, review service JSON diffs and provider-source provenance. |
