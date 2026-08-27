# Development, Build, and Docs Troubleshooting

Use this when a contributor command fails before the runtime or package code is
clearly at fault. Start with cheap environment and task-selection checks; do not
jump to heavy engine builds, services, Docker/Kubernetes, or provider credential
checks unless the user explicitly asks.

## Fast classification

| Symptom | Likely cause | First response |
|---|---|---|
| `pnpm: command not found` | pnpm not installed or Corepack disabled | Enable Corepack or install pnpm, then verify `pnpm --version`. |
| `ERR_PNPM_UNSUPPORTED_ENGINE` or package-manager mismatch | Node/pnpm too old or wrong package manager | Use Node 20+ and pnpm 10+, matching the root package-manager pin. |
| `Cannot find module 'glob'`, `listr2`, `dotenv`, or similar while running builder | Workspace dependencies missing | Run `pnpm install`; then retry `./builder --help`. |
| `./builder: Permission denied` | Wrapper is not executable | Run `chmod +x ./builder` or use `node scripts/build.js <action>`. |
| Builder command not found | Wrong module/action name or action is internal | Run `./builder --list-actions` and `./builder --help`. |
| Global `./builder build` is too slow or starts too much work | Global expansion selected many public `*:build` actions | Use focused `module:build` tasks and inspect `--list-deps`. |
| Docs build cannot find Docusaurus or TypeScript | JS workspace deps missing | Run `pnpm install`; retry `./builder docs:build`. |
| `docs:serve` says no built docs | `dist/docs` absent | Run `./builder docs:build` first. |
| `nodes:docs-generate` changes nothing | Branch guard, missing markers, or no service fields | Do not edit generated block; inspect generator output and README markers. |
| Node generated block has stale schema rows | Source `services*.json` changed without regeneration | Run `./builder nodes:docs-generate` in an allowed branch context. |
| TypeScript SDK contract check fails | Public API removed/narrowed, missing current floor, or derived artifacts stale | Decide whether to preserve compatibility, freeze current minor, or regen derived artifacts. |
| check-externals reports missing package/symbol | Upstream interface drift, optional dependency not installed, or auto-extraction false positive | Update code/manifest/requirements marker with a reason; do not blindly delete checks. |
| `models:update` skips discovery | Provider API key absent or strict discovery mode | Keep dry-run output, set the correct env key, or intentionally use fallback discovery. |
| Test task starts an unexpected server | Builder test action uses a `bracket()` setup | Use a focused direct test only when it does not require engine setup, or pass existing server options where supported. |

## pnpm and Corepack recovery

The workspace expects pnpm. Prefer Corepack when available:

```bash
node --version
corepack enable
corepack prepare pnpm@10.33.0 --activate
pnpm --version
pnpm install
```

If Corepack is unavailable or blocked, install pnpm through the user's approved
package-management route, then verify the version:

```bash
npm install -g pnpm@10.33.0
pnpm --version
pnpm install
```

CI-like installs use:

```bash
pnpm install --frozen-lockfile
```

Do not fix pnpm errors by deleting the lockfile, switching to npm/yarn, or
removing workspace security overrides. The workspace file intentionally limits
lifecycle scripts to known native/binary packages.

## Builder startup failures

### Wrapper cannot run

```bash
chmod +x ./builder
./builder --help
```

If shell execution is unavailable, call the orchestrator directly:

```bash
node scripts/build.js --help
node scripts/build.js docs:build
```

### Builder cannot discover or load tasks

Run:

```bash
./builder --list-actions
./builder --list-modules
```

If discovery fails before listing:

1. Confirm `pnpm install` completed.
2. Confirm Node is 20+.
3. Look for the first missing module in the stack trace.
4. Avoid editing task files until the dependency/bootstrap failure is ruled out.

If a new action does not appear, check the owning `scripts/tasks.js` shape:

- It must export a module object or array with `name` and `actions`.
- Each action must be in the top-level `actions` array.
- The action name must include the module prefix, such as `docs:test`.
- Public actions require an action-object `description`; otherwise they are
  internal and omitted from `--help` and global commands.

### A task completed but did not run its callback

A builder action with both `steps` and `run` is treated as compound; the `run`
callback is not executed. Split it into:

- an internal leaf action with `run`, and
- a public compound action with `steps` that calls the leaf.

This pattern is used by maintenance tools that need public build prerequisites
plus one actual CLI invocation.

## Docs generation failures

### `docs:build` is not part of the task you ran

Run docs explicitly:

```bash
./builder docs:build
```

The current docs build action is intentionally explicit. Do not assume a generic
`./builder build` command has produced `dist/docs`.

### `docs:serve` cannot find output

`docs:serve` serves the static site output; it does not build it.

```bash
./builder docs:build
./builder docs:serve
```

Do not start `docs:serve` or `docs:dev` in a non-interactive task unless the user
asked for a long-running docs server.

### Node README generated params did not update

Check these conditions:

1. The README must contain both `ROCKETRIDE:GENERATED:PARAMS START` and
   `ROCKETRIDE:GENERATED:PARAMS END` markers.
2. The node must have parseable `services*.json` files after comments are
   stripped.
3. The generator may skip outside `main`, `stage`, or `develop` to avoid source
   link churn.
4. Some nodes intentionally have no generated block; do not add one unless the
   node docs migration policy requires it.

Correct response:

```bash
./builder nodes:docs-generate
```

If it skips due to branch policy, do not hand-edit the generated block. Preserve
source/schema/prose changes and note that release-track regeneration is required.

### Generated docs drift after branch changes

Node generated blocks include source links derived from Git branch/remotes. If a
feature branch regenerates source links unexpectedly, do not review the entire
block as hand-written content. Either regenerate in the intended release-track
context or revert generated-only source-link churn if policy says not to carry it.

### Generated pipeline reference is stale

The `.pipe` reference is generated from TypeScript pipeline schema types.

```bash
./builder client-typescript:docs-generate
./builder docs:build
```

Do not patch the generated reference page directly; update the schema/types and
run the generator.

## TypeScript SDK contract failures

### `client-typescript:check` reports no current floor

A public TypeScript SDK surface exists for the package version but the current
`MAJOR.MINOR` floor was not minted. If this is an intentional current-minor API
state, run:

```bash
./builder client-typescript:freeze
./builder client-typescript:check
```

Review the generated floor diff carefully before committing.

### A floor check fails after an API edit

Classify the edit:

| Edit | Meaning | Fix |
|---|---|---|
| Added new export/member | Usually additive | Freeze current minor if needed; verify check passes. |
| Removed export/member | Breaking for older floors | Restore compatibility or coordinate a versioned breaking change. |
| Narrowed parameter/return type | Often breaking | Widen or add overload/backward-compatible shape. |
| Renamed enum member or changed wire value | Breaking | Preserve old value/member or version the change. |
| Changed only generated contract artifacts | Derived drift | Run `./builder client-typescript:regen` and verify diff is expected/no-op. |

Never edit older frozen floors to hide a breaking change. The contract exists to
catch that exact failure mode.

### `client-typescript:regen` changes files on a clean tree

Treat this as derived artifact drift or hand-edited generated output. Re-run the
regen command, inspect the diff, and pair it with `git diff --exit-code` in a
CI-like check if the task is to prove generated artifacts are current.

## check-externals failures

`check-externals:run` is a contract-check CLI, not a normal pytest lane. It can
build prerequisites and inspect many dependency surfaces.

Common interpretations:

| Output | Meaning | Response |
|---|---|---|
| `[FAIL] package.symbol missing` | Upstream package changed or code imports the wrong path | Update consuming code, add version-gated manifest, or pin/update requirements. |
| `[SKIP] package not installed` | Optional dependency absent in the engine env | If optional, this may be acceptable; if required, install path/requirements need fixing. |
| `[install-failed]` | A requirements file failed to install during the check | Fix dependency constraints or use a documented skip/disable marker only for intentional cases. |
| Auto-extracted heavy class skipped | The framework guessed an unsafe constructor | Add a manifest with safe dummy construction only if chain coverage is important. |

Focused command:

```bash
./builder check-externals:run --pattern=<component-or-package>
```

Nightly-style command, not routine:

```bash
./builder check-externals:run --rebuild-cache --install-all
```

Use inline markers with reasons only for optional/false-positive imports or known
heavy/incompatible requirements. Avoid broad ignores.

## Model sync failures and surprising diffs

### Provider skipped or discovery disabled

Model sync distinguishes enrichment from discovery:

- Default: enrich existing profiles only; no new profiles.
- `--enable-discovery`: allow new profiles.
- Strict discovery: provider API key must exist for provider-discovered new
  profiles.
- `--allow-fallback-discovery`: allows OpenRouter/LiteLLM fallback discovery;
  review aliases before merging.

If a provider is skipped, first check the required `ROCKETRIDE_<PROVIDER>_KEY`
environment variable. Do not test real provider credentials unless the user
explicitly provides them for this task.

### Builder model sync formats files during a dry-run

The direct script is dry-run without `--apply`, but the builder action runs sync
and then Prettier for targeted services files. For a no-write inspection, prefer:

```bash
python tools/sync_models/src/sync_models.py --provider llm_openai
```

For an intentional write:

```bash
./builder models:update --models="--provider llm_openai --enable-discovery --apply"
```

### New model works in fallback source but not native SDK

Fallback discovery can add provider aliases from OpenRouter/LiteLLM. Verify new
IDs against the native provider API before merging if the node routes through the
native provider SDK.

## Test task surprises

Many builder tests assemble the engine or start a temporary server. Before
running a broad task, inspect dependencies:

```bash
./builder nodes:test --list-deps
./builder client-typescript:test --list-deps
```

Use focused tests when available:

```bash
./builder docs:test
./builder nodes:test-contracts
./builder check-externals:test
python -m pytest <specific-test-file> -q
```

For SDK test tasks that support an existing server, use the task's existing URI
or taskserver option only when the user explicitly wants to run against that
server. Do not start services just to answer a docs/build planning question.

## Lint/format troubleshooting

### Ruff is missing

Install the owning package's dev/test extras or use the prepared environment for
Python checks. Then run focused checks:

```bash
python -m ruff check <paths>
python -m ruff format <paths>
```

The root config uses single quotes for inline strings and deliberately relaxes
some docstring and line-length rules. Do not assume a default Ruff config.

### ESLint or Prettier is missing

Install the pnpm workspace first:

```bash
pnpm install
pnpm exec eslint <paths>
pnpm exec prettier --check <paths>
```

Use `pnpm exec prettier --write <paths>` only when formatting writes are intended.

## When to stop and ask

Ask for user/maintainer direction before:

- running a full source engine build when a focused docs/test command would do,
- starting long-running dev/docs/server processes,
- using provider API keys, Cloud tokens, Docker, Kubernetes, or network sync,
- replacing older TypeScript contract floors,
- bypassing check-externals coverage with broad ignores,
- committing fallback-discovered model IDs that have not been reviewed against
  the native provider SDK.
