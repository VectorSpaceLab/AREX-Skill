# Builder and Task Model

This reference explains how RocketRide contributor commands are organized. It is
for selecting or authoring build/test/docs tasks, not for running end-user
pipelines or deploying the engine.

## Workspace prerequisites

The current repository metadata is stricter than some older prose docs:

| Requirement | Contributor guidance |
|---|---|
| Node.js | Use Node `20` or newer for the workspace. |
| pnpm | Use pnpm `10` or newer; the root package manager pin is `pnpm@10.33.0`. |
| Install | Run `pnpm install` locally after enabling pnpm. CI uses `pnpm install --frozen-lockfile`. |
| Package manager | Do not replace the pnpm lock/workspace with npm or Yarn for monorepo work. |

The pnpm workspace is focused on the JavaScript/TypeScript surfaces:
`packages/shell`, `packages/client-typescript`, `packages/docs`, `apps/*`, and
`examples/*`. Python clients, MCP, nodes, tools, C++ engine work, docs gathering,
and packaging are coordinated by the builder rather than by package-level npm
scripts.

The root package script only installs Lefthook on `prepare`; normal build/test
work uses `./builder` tasks.

## How `./builder` works

`./builder` is a thin wrapper around the Node build orchestrator. The action
format is:

```bash
./builder <module>:<action> [more-actions...] [options]
```

Examples:

```bash
./builder client-typescript:build
./builder client-python:test --pytest="-k env_loading"
./builder docs:build
./builder --help
```

Task discovery loads `scripts/tasks.js` files from module directories such as
`packages/*/scripts/tasks.js`, `apps/*/scripts/tasks.js`, `nodes/scripts/tasks.js`,
`tools/**/scripts/tasks.js`, and the root `scripts/tasks.js`. Each module exports
one or more module definitions with a `name`, `description`, and `actions` array.

Important task-model rules:

- Action names use `module:action`, for example `nodes:build` or
  `client-typescript:check`.
- Public actions have a `description`. They appear in `./builder --help` and are
  expanded by global commands such as `./builder build` and `./builder test`.
- Internal actions usually omit `description`; they are still visible through
  `./builder --list-actions` and can be used as implementation steps.
- A compound action uses `steps: [...]`. A leaf action uses `run: async (...) =>`.
  Do not define both `steps` and `run` on the same action; the runner treats the
  action as compound and the `run` callback will not execute.
- `parallel([...], "label")` runs independent steps concurrently with automatic
  deduplication. Use `--sequential` when local resources are tight.
- `bracket({ setup, steps, teardown })` starts and stops temporary resources for
  tests; teardown runs even when tests fail.
- `when()` / `whenNot()` make runtime decisions, such as using a downloaded
  server binary versus compiling.
- Builder state and source fingerprints let incremental builds skip unchanged
  work unless `--force` is passed.

## Discovery and inspection commands

| Need | Command | Notes |
|---|---|---|
| Show public task help | `./builder --help` | Lists public actions only. |
| Show all registered actions | `./builder --list-actions` | Includes internal/generated helper actions. |
| Show modules | `./builder --list-modules` | Useful when a package task is not discovered. |
| Show dependency graph | `./builder <action> --list-deps` | Use before running a heavy action. |
| Verbose execution | `./builder <action> --verbose` | Adds detail to task output. |
| Grouped log file | `./builder <action> --log=builder.log` | Useful for test/build transcripts. |
| Force rebuild | `./builder <action> --force` | Ignores cached source-state decisions. |
| Run sequentially | `./builder build --sequential` | Reduces memory/CPU contention. |

## Common contributor commands

### Setup and build

| Task | Command | Expected use |
|---|---|---|
| Install JS workspace deps | `pnpm install` | First local setup; required before Node/Docusaurus/TypeScript tasks. |
| Full public build graph | `./builder build` | Heavy; expands to public `*:build` actions. Use focused builds for PRs. |
| Focused client builds | `./builder client-typescript:build client-python:build client-mcp:build` | Builds client packages and their required dependencies. |
| Node sync/docs build | `./builder nodes:build` | Builds server dependency first, syncs nodes, and runs node docs generation. |
| Engine/runtime build | `./builder server:build` | Heavy; may download or compile the engine and assemble runtime files. |
| UI remotes | `./builder ui:build` | Builds remote UI apps; shell is handled by server/shell tasks. |
| VS Code extension | `./builder vscode:build` | Builds extension package outputs. |
| Clean all public modules | `./builder clean` | Expands public `*:clean` actions. |

### Tests

| Task | Command | Side effects |
|---|---|---|
| All public tests | `./builder test` | Heavy; expands public `*:test` actions. |
| Engine tests | `./builder server:test` | Heavy engine test lane. |
| Node tests | `./builder nodes:test` | Builds dependencies and starts a temporary test server with mocks. |
| Full node tests | `./builder nodes:test-full` | Broader/slower than default node tests. |
| Node contract tests | `./builder nodes:test-contracts` | Builds server, then runs node contract test file. |
| Python SDK tests | `./builder client-python:test` | Builds dependencies and starts a temporary test server unless an existing URI is supplied. |
| TypeScript SDK tests | `./builder client-typescript:test` | Builds dependencies and starts a temporary test server unless an existing taskserver is supplied. |
| MCP tests | `./builder client-mcp:test` | Builds dependencies and starts a temporary test server. |
| Docs helper tests | `./builder docs:test` | Fast relative to engine tests; uses Node's test runner for docs helpers. |
| External contract framework tests | `./builder check-externals:test` | Framework unit tests; builds only the engine first. |

Forward focused test arguments with builder options:

```bash
./builder nodes:test --pytest="-k my_node -s"
./builder client-typescript:test --jest="path/or/pattern"
./builder check-externals:run --pattern=my_node
```

## Docs actions

`docs:build` is intentionally explicit in the current task definitions. Do not
assume global `./builder build` will build the docs site.

| Task | Command | What happens |
|---|---|---|
| Build static docs | `./builder docs:build` | Runs node docs generation and TypeScript pipeline reference generation, gathers co-located docs, builds the LLM index, and compiles the Docusaurus site to `dist/docs`. |
| Start docs dev server | `./builder docs:dev` | Gathers by symlink and starts an interactive Docusaurus dev server. Starts a long-running process. |
| Serve built docs | `./builder docs:serve` | Serves `dist/docs`; fails if docs were not built first. Starts a long-running process. |
| Test docs helpers | `./builder docs:test` | Runs pure docs helper tests under Node's test runner. |
| Clean docs outputs | `./builder docs:clean` | Removes generated docs content/site outputs. |

## Root builder maintenance actions

The root task module contributes repository-wide `ui:*` and `builder:*` actions.
Use these only when the task is explicitly about the build system or UI remotes:

| Action | Purpose | Caution |
|---|---|---|
| `ui:register` | Regenerate the UI app manifest without bundling remotes. | Writes manifest metadata. |
| `ui:build` | Build registered remote UI apps. | Can be slower than app-specific tasks. |
| `builder:inject --path=<repo>` | Copy this builder's `scripts/` tree into another repo that vendors the builder. | Build-system maintenance only. |
| `builder:update --branch=<branch>` | Replace `scripts/` with the upstream copy. | If targeting this repo, run as the invocation's only action. |

## Adding or revising a builder task

When a contributor task asks for build-system changes:

1. Put the action in the owning module's `scripts/tasks.js` file.
2. Use a public `description` only for stable commands that should appear in
   help and global command expansion.
3. Split compound and leaf behavior: public compound actions should call
   internal leaf actions if real `run` callbacks are needed.
4. Use `bracket()` for tests that start servers so teardown is guaranteed.
5. Use `parallel()` only for independent work; do not share mutable `ctx` keys
   across parallel steps.
6. Export path constants when another module needs to depend on this module's
   generated paths.
7. Verify discovery with `./builder --list-actions` before relying on a new
   action in docs or CI.
