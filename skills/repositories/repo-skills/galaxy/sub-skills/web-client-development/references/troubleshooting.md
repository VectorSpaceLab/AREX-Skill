# Troubleshooting

Use this guide to diagnose Galaxy client build, dev-server, API-client, and Vitest problems without immediately running heavyweight installs or full builds.

## Node or pnpm Mismatch

Symptoms:

- `pnpm` refuses the lockfile or rewrites many dependency entries.
- Workspace package scripts fail before TypeScript or Vite starts.
- `node`/`pnpm` versions differ from the versions expected by the checkout.

Checks:

```bash
node --version
pnpm --version
```

Resolution path:

1. Compare the package manager version recorded in the client package metadata.
2. If the Galaxy virtual environment is available, activate it first because Galaxy may provide the expected Node and pnpm tools there.
3. Do not run `pnpm install` just to inspect versions; ask before installing dependencies or changing the lockfile.
4. If install is approved, run it from `client/` so the whole pnpm workspace and API-client postinstall build are handled together.

## Missing Client Artifacts

Symptoms:

- Galaxy starts but static client bundles or CSS are missing.
- Templates refer to built assets that do not exist.
- A clean checkout lacks generated client script artifacts.

Resolution path:

1. Remember built client artifacts are not committed.
2. For a local development build, use `make client` from the Galaxy root.
3. For production-like validation, use `make client-production` or `make client-production-maps` when sourcemaps are needed.
4. For iterative development, run Galaxy with client build skipped and use the Vite dev server.
5. Do not commit staged bundle output unless the repository's contributing rules explicitly require a generated file.

## Stale Generated API Client or Schema

Symptoms:

- `GalaxyApi().GET(...)` rejects a route that exists in the backend.
- TypeScript reports missing response fields after backend API changes.
- MSW typed handlers cannot use a new endpoint.
- The standalone API-client package has stale declaration output.

Resolution path:

1. Confirm whether the backend route is FastAPI/OpenAPI-backed; route semantics belong in `../api-automation/SKILL.md`.
2. If OpenAPI changed, regenerate client schema with `make update-client-api-schema` from the Galaxy root.
3. Rebuild the API-client workspace package from `client/` with `pnpm --filter @galaxyproject/galaxy-api-client run build` when `dist/` or declarations are stale.
4. Run targeted API-client or affected client tests after regeneration.
5. Do not patch generated schema by hand except as a temporary diagnostic; fix the backend schema source or generator path.

## Vite Dev-Server Proxy Target, Origin, or Port

Symptoms:

- Browser on Vite port shows Galaxy login/static shell but API calls fail.
- Requests go to `127.0.0.1:8080` even though the backend runs elsewhere.
- Remote Galaxy development has cookie, CORS, or host-origin failures.
- Port `5173` is unavailable.

Resolution path:

1. Identify the browser URL, Vite bind port, and Galaxy backend URL separately.
2. Set `GALAXY_URL` to the backend target when Galaxy is not on the default local port.
3. Set `CHANGE_ORIGIN=true` when proxying to a remote Galaxy that expects rewritten host/origin headers.
4. Set `VITE_PORT` when the default Vite port is occupied.
5. Start the backend without rebuilding the client when using Vite separately: `make skip-client` or `GALAXY_SKIP_CLIENT_BUILD=1 ./run.sh`.
6. If cookies fail against HTTPS remote targets, check same-site/secure cookie behavior and confirm the server is safe to use for development.

Example plan from `client/`:

```bash
GALAXY_URL=http://localhost:8000 VITE_PORT=8083 pnpm run develop
```

## Async Vitest Assertions

Symptoms:

- Tests fail before API results render.
- Wrapper text is stale after `setProps` or `setValue`.
- Debounced search tests are intermittent.

Resolution path:

1. Use `await flushPromises()` after mounting components that make API calls or after interactions that trigger async work.
2. Use `await nextTick()` for pure Vue reactivity changes.
3. Await `trigger`, `setValue`, and `setProps` calls.
4. For debounced code, use fake timers, advance the exact debounce interval, then flush promises.
5. Avoid arbitrary sleeps except as a last resort; deterministic timer/promise flushing makes tests faster and less flaky.

## `shallowMount` vs `mount` Problems

Symptoms:

- A unit test triggers unexpected child API calls.
- Full component mounting requires a large graph of unrelated mocks.
- A shallow test cannot see slot or child behavior that is the actual feature.

Resolution path:

- Default to `shallowMount` for focused component unit tests.
- Use `mount` only when rendered children, slots, router/plugin behavior, or parent-child interaction is the behavior under test.
- Stub specific children deliberately when they are irrelevant but need props or methods.
- If the test is proving full application UI behavior, route it to server-backed browser testing rather than expanding Vitest into an end-to-end test.

## MSW Typed vs Untyped Responses

Symptoms:

- `http.get("/api/...", ...)` rejects a route or response type.
- A handler compiles only after `as any` casts.
- A test mocks a legacy endpoint that is not in the OpenAPI schema.

Resolution path:

1. Prefer typed OpenAPI handlers for schema-covered endpoints.
2. Use `response(200).json(...)` for typed success responses and status-family helpers for typed errors.
3. Use `http.untyped.*` or `response.untyped(HttpResponse.json(...))` only for routes missing from OpenAPI.
4. If a route should be typed but is missing, regenerate schema or route endpoint semantics to `../api-automation/SKILL.md`.
5. Keep untyped mocks local and documented so they do not mask schema drift.

## Unhandled MSW Request Failures

Symptoms:

- Test error says no request handler was found and shows a suggested `server.use(...)` handler.
- The requested path includes query/path parameters you did not expect.

Resolution path:

1. Add a handler for every API request the unit makes, including child component requests if using `mount`.
2. Prefer `shallowMount` if the unhandled request comes from irrelevant children.
3. Check `GALAXY_URL` or app-root assumptions only if the test is not using the normal test base URL.
4. Keep handlers inside `beforeEach` or individual tests so reset behavior does not leak state between cases.

## TypeScript and Lint Failures After UI Changes

Symptoms:

- `vue-tsc` cannot resolve workspace package declarations.
- Prettier or ESLint reports widespread unrelated changes.
- Imports are out of order or schema types no longer match.

Resolution path:

1. For package declaration failures, build the API-client package first.
2. Use OpenAPI schema types and exported API resource types instead of duplicating interfaces.
3. Run focused format/lint checks for changed files before broad formatting.
4. If broad formatting changes many unrelated files, stop and narrow the command or revert unrelated formatting.
