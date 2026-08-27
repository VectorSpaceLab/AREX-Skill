# Development

This document describes the standalone `@auto-ml-skills/disco` package. The
runtime source lives in `packages/coding-agent/src`; there is no second wrapper
implementation and no runtime dependency on `@earendil-works/pi-coding-agent`.

## Setup

From the package root, which contains this file's parent `docs/` directory:

```bash
npm ci
npm run typecheck
npm test
npm run test:examples
npm run verify:provenance
npm run build
```

Run the built CLI without installing it globally:

```bash
node dist/cli.js --help
node dist/cli.js
```

The caller's current working directory remains the DisCo project directory.
Use `DISCO_CODING_AGENT_DIR` to point development runs at a temporary config
directory when they must not use your normal `~/.disco/agent` state.

## Source layout

```text
packages/coding-agent/src/   runtime, CLI, SDK, modes, workflows, and TUI glue
packages/coding-agent/test/  upstream-derived and DisCo regression tests
docs/                        documentation shipped in the npm package
examples/                    extension, SDK, and RPC examples shipped in npm
scripts/                     build asset copying and package verification
dist/                        generated build output
```

`packages/coding-agent/upstream-package.json`, `UPSTREAM_SOURCE.md`,
`UPSTREAM_CHANGELOG.md`, and `UPSTREAM_MANIFEST.json` record the Pi v0.83.0
baseline. They are provenance inputs, not package roots and are not published.
The manifest records SHA-256 hashes and a disposition for every upstream file
and every local runtime, test, documentation, and example file.

## Build and package checks

```bash
npm run build
npm run verify:provenance
npm run verify:package
npm pack --dry-run --json
npm publish --dry-run
```

`verify:provenance` checks the local source inventory against the recorded
manifest. `verify:package` audits source, build output, documentation, and the
packed file contract. Release testing also installs the generated tarball into
a temporary npm prefix; it must not use a globally installed Pi package or a
source-tree symlink.

## Running focused tests

Vitest paths are relative to the package root:

```bash
npx vitest --run --config vitest.config.ts packages/coding-agent/test/config.test.ts
npx vitest --run --config vitest.config.ts packages/coding-agent/test/resource-loader.test.ts
```

Tests that need real providers or a local proxy are separate from the default
deterministic suite. Proxy addresses belong in the test process environment or
a temporary settings fixture and must never become package defaults.

## Package assets

Runtime asset paths must be resolved through `src/config.ts`, not by assuming a
Pi monorepo layout. `scripts/copy-assets.mjs` copies bundled skills, themes, and
HTML export assets into `dist/`; npm's package file list includes README, docs,
examples, and notices directly from the package root.

Source-mode, built, packed, and globally installed runs must all resolve the
same DisCo package root and `.disco` configuration semantics.

## Debug log

The hidden `/debug` command writes `~/.disco/agent/disco-debug.log`. It can
contain rendered terminal output and recent model messages; inspect and share
it as potentially sensitive data.

## Upstream synchronization

When importing a later Pi coding-agent version:

1. Record the exact tag and commit in `packages/coding-agent/UPSTREAM_SOURCE.md`.
2. Regenerate `UPSTREAM_MANIFEST.json` with
   `node scripts/upstream-provenance.mjs --write --upstream-root /path/to/pi`
   and review every disposition change across source, tests, docs, examples,
   package assets, and the narrow OAuth exception.
3. Reapply DisCo ownership boundaries for `.disco`, `DISCO_*`, self-update,
   package discovery, Creator/Researcher filtering, SDK exports, and branding.
4. Run the complete deterministic, packed-install, coexistence, proxy, splash,
   and real-model regression gates before release.

Do not copy upstream `node_modules`, `dist`, install locks, monorepo links, or
the Pi executable into the DisCo package.
