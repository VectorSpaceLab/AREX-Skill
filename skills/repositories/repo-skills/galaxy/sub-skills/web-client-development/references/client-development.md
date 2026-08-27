# Client Development

Galaxy's web client is a Vue 2.7 and TypeScript application under `client/`, with pnpm workspace packages under `client/packages/`. The main workspace consumes `@galaxyproject/galaxy-api-client` via `workspace:*`, and Vite serves package source directly during development so edits to package source participate in HMR.

## Choosing Commands

Use the bundled planner first when deciding what to run:

```bash
python scripts/client_command_planner.py --task test-file --path src/components/Example/Example.test.ts
python scripts/client_command_planner.py --task dev-server --galaxy-url http://localhost:8000 --vite-port 8083
python scripts/client_command_planner.py --task api-client-build
```

The planner does not run pnpm. It prints commands to run from the Galaxy root or from `client/`, plus prerequisites and risk notes.

## Common Client Commands

Run repository-level make targets from the Galaxy root:

| Goal | Command | Notes |
| --- | --- | --- |
| Development client build | `make client` | Stages dependencies, styles, scripts, and bundles for local development. |
| Production client build | `make client-production` | Production-optimized build for deployment-like checks. |
| Production with sourcemaps | `make client-production-maps` | Useful for inspecting built production JavaScript. |
| Dev server | `make client-dev-server` | Starts Vite dev server, normally on port `5173`. |
| Backend without client build | `make skip-client` | Useful when running a separate Vite dev server. |
| Client tests | `make client-test` | Repository-level entry for full client unit tests. |
| Lint | `make client-lint` | Uses the client lint command wired by Galaxy. |
| Format | `make client-format` | Uses the client formatting command wired by Galaxy. |

Run package scripts from `client/`:

| Goal | Command | Notes |
| --- | --- | --- |
| Vite dev server | `pnpm run develop` | Honors `GALAXY_URL`, `CHANGE_ORIGIN`, and `VITE_PORT`. |
| Development build | `pnpm run build` | Runs build preprocessing, Vite build, and stages output. |
| Production build | `pnpm run build-production` | Equivalent package-level production build. |
| Full Vitest run | `pnpm test` | Same broad suite invoked by `make client-test`. |
| Watch Vitest | `pnpm test:watch` | Interactive watch mode. Add a pattern for focused reruns. |
| Coverage | `pnpm test:coverage` | Potentially slower; use when coverage is requested. |
| Type check | `pnpm run type-check` | Runs `vue-tsc --noEmit`. |
| ESLint | `pnpm run eslint` | Lints JS, Vue, and TS under `src`. |
| Format check | `pnpm run format-check` | Non-writing Prettier check. |
| Format write | `pnpm run format` | Writes formatting changes. |

## Dependency and Artifact Expectations

- Galaxy expects Node.js and pnpm. A Galaxy virtual environment may provide appropriate versions after activation; otherwise the user must provide compatible host tools.
- `client/package.json` records the pnpm package manager version as `pnpm@10.26.1`; mismatches can cause lockfile or install behavior changes.
- `client/` is a single pnpm workspace declared with `packages/*` members.
- `pnpm install` from `client/` installs the whole workspace and runs a postinstall build for the API-client package so `dist/` is available to `vue-tsc` and production builds.
- Built client bundles are staged under Galaxy static output during builds, but generated script artifacts are not source-controlled and should not be committed.

## Dev Server Proxy

For iterative UI work, run Galaxy without rebuilding the client and run Vite separately:

```bash
make skip-client
cd client
pnpm run develop
```

The Vite dev server defaults to port `5173` and proxies non-Vite routes to the Galaxy backend. Use these environment variables when the default is wrong:

- `GALAXY_URL=http://localhost:8000` changes the backend proxy target.
- `CHANGE_ORIGIN=true` is appropriate when developing against a remote Galaxy server that expects host/origin rewriting.
- `VITE_PORT=8083` changes the Vite bind port.
- `GALAXY_SKIP_CLIENT_BUILD=1 ./run.sh` starts Galaxy without a client build when using the normal server startup path.

When debugging dev-server issues, distinguish three URLs: the browser URL for Vite, the proxied Galaxy backend URL, and any remote server origin/cookie policy.

## API Client Package

`client/packages/api-client` is the workspace package `@galaxyproject/galaxy-api-client`. It provides OpenAPI-derived types, a typed fetch client backed by `openapi-fetch`, error utilities, and a backward-compatible `GalaxyApi` export.

Common package-scoped commands from `client/`:

```bash
pnpm --filter @galaxyproject/galaxy-api-client test
pnpm --filter @galaxyproject/galaxy-api-client run build
pnpm --filter @galaxyproject/galaxy-api-client run dev
```

The main client aliases `@galaxyproject/galaxy-api-client` to package source during `vite serve`; production builds use package `dist/`. If `vue-tsc` or production build cannot resolve package declarations, build the package or run workspace install/postinstall.

## OpenAPI Schema Updates

Use backend/OpenAPI guidance from `../api-automation/SKILL.md` to understand endpoint semantics. For client type updates, the normal repository command is:

```bash
make update-client-api-schema
```

This target builds Galaxy and Tool Shed OpenAPI schema files, runs `openapi-typescript` for the client API schema package, formats the generated schema, and removes temporary schema files. Treat it as a generated-code update; review diffs carefully and do not hand-edit generated schema output unless fixing the generator input.

## API Query Style

When adding UI API calls:

1. Prefer an existing composable if it already models the resource.
2. Prefer a Pinia store when the data is reactive, cached, or shared across views.
3. Use `GalaxyApi` directly for narrow uncached reads/writes.
4. Put reusable request wrappers under an API resource module when several components need the same call.
5. Use OpenAPI schema types instead of duplicating TypeScript models.
6. Handle `{ data, error }` explicitly and return early on error so code does not use undefined data.

Avoid new Axios calls for OpenAPI-covered endpoints unless there is a clear compatibility reason and the surrounding code already uses that layer.
