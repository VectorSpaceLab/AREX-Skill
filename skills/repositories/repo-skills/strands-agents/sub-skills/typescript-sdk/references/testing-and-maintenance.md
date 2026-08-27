# Testing and Maintenance

## Workspace scripts

The package metadata exposes two script layers:

- The root workspace scripts coordinate the monorepo (`dev`, `build`, `test`, `test:coverage`, `test:all`, `test:all:coverage`, `test:integ`, `test:integ:all`, `test:integ:selective`, `test:browser:install`, `test:package`, `lint`, `format`, `format:check`, `type-check`, `check`, `check:browser-bundle`, `complexity`, `complexity:setup`, `test:pr-metrics`).
- The `strands-ts` workspace adds the TypeScript SDK-specific scripts (`build`, `check`, `test`, `test:coverage`, `test:types`, `test:integ`, `test:browser`, `test:package`, `lint`, `format`, `format:check`, `type-check`, `check:browser-bundle`, `lock:refresh`).

Prefer the helper scripts when you need a standard validation path.

## Fast checks

| Command | What it does |
| --- | --- |
| `scripts/ts-core-check.sh check` | Lint, format-check, type-check, and browser bundle check |
| `scripts/ts-core-check.sh test` | Workspace unit tests |
| `scripts/ts-core-check.sh build` | Build the TypeScript workspace |
| `scripts/ts-core-check.sh package` | Package verification and tarball-content guard |
| `scripts/ts-core-check.sh browser-note` | Show the browser-install reminder without mutating anything |
| `scripts/workspace-cli.sh ci` | Workspace-level CI-style flow |
| `scripts/workspace-cli.sh example <name>` | Run an isolated example project |

## Test layout and naming

- Unit tests live next to the source in `src/**/__tests__/`.
- Integration tests live in `test/integ/`.
- `*.test.ts` runs in Node and browser.
- `*.test.node.ts` runs in Node only.
- `*.test.browser.ts` runs in browser only.
- Keep Node-only tests out of browser projects.
- Use the fixtures in `src/__fixtures__/` instead of hand-rolling setup when a fixture already exists.

## Test style

- Use nested `describe` blocks.
- Batch related assertions when the setup is expensive.
- Prefer object-wide assertions over piecemeal property checks.
- Write direct tests for implementations, not interfaces.
- Add `*.test-d.ts` only when type-level compatibility is worth pinning.

## Native candidate map for this sub-skill

| Native artifact | Why it matters | Safety class | Backend requirement | Typical command | Expected signal |
| --- | --- | --- | --- | --- | --- |
| `src/__tests__/index.test.ts` | Public export surface, value exports, and barrel omissions | safe-runnable | cpu | `npm test -w strands-ts -- --run src/__tests__/index.test.ts` | selected tests pass |
| `src/tools/__tests__/tool.test.ts` | Tool factory, streaming, error wrapping, direct invocation | safe-runnable | cpu | `npm test -w strands-ts -- --run src/tools/__tests__/tool.test.ts` | selected tests pass |
| `src/models/__tests__/bedrock.test.ts` | Provider contract and mock streaming mapping | safe-runnable | cpu | `npm test -w strands-ts -- --run src/models/__tests__/bedrock.test.ts` | selected tests pass |
| `strands-ts/examples/first-agent` | Basic agent usage and invoke/stream patterns | help-only / optional | any | no default run; use as a standalone example when needed | documented or manual pass |
| `strands-ts/examples/graph` | Multi-agent orchestration example | help-only / optional | any | no default run; use as a standalone example when needed | documented or manual pass |
| `strands-ts/examples/mcp` | MCP integration example | help-only / optional | any | no default run; use as a standalone example when needed | documented or manual pass |
| `strands-ts/examples/browser-agent` | Browser-only demo with unsafe DOM editing | skip-unsafe | browser | no default run; require explicit browser approval | documented skip |
| `strands-ts/examples/telemetry` | Tracing and metrics example with Docker | conditional | node + docker | no default run; requires explicit environment setup | documented skip or manual pass |

## Maintenance rules

### Dependency changes

- If a dependency crosses the API boundary, it belongs in `peerDependencies`.
- Optional peer dependencies should also be mirrored in `devDependencies` for local development.
- After changing dependencies, refresh the lockfile with `npm run lock:refresh -w strands-ts`.
- Do not manually edit the lockfile.

### Package and export hygiene

- Keep root and subpath exports aligned with the public barrel.
- If a symbol must exist at runtime, export it as a value, not a type-only export.
- If a file is moved or renamed, update any export paths and tests that prove the surface.
- Keep the packed tarball free of test artifacts and fixtures.

### Node/browser discipline

- Keep Node-only setup behind the Node entry point or Node-only subpaths.
- Keep browser-safe code free of Node builtins unless the path is explicitly Node-only.
- Re-run the browser bundle check after touching entry points or provider imports.

### What to verify before you call something done

- Public export surface still imports cleanly
- Tool and model behavior still round-trips through tests
- Browser bundle still builds when the change touches the top-level barrel
- Packaging still excludes tests and fixtures
- Example projects still behave as isolated consumers
