# Frontend Integration Troubleshooting

## Wrong API Prefix

Symptoms:

- Browser request returns 404/405 even though an endpoint constant exists.
- Vite dev proxy sends the request to the wrong backend target.
- A route works through public SDK/curl but fails in the web UI.

Checks:

1. Confirm whether the backend route is a newer RESTful `/api/v1` route or legacy `/v1` route.
2. Inspect the endpoint constant for `restAPIv1` versus `webAPI` usage.
3. Run `python scripts/check_web_api_keys.py --root <ragflow-checkout>` from this skill directory to summarize prefix use and suspicious literals.
4. If the route changed backend families, update every service/hook call that relies on the old endpoint key.
5. In dev, check `API_PROXY_SCHEME`; Python, hybrid, and Go proxy schemes route some prefixes to different targets.

Fix pattern: choose the correct prefix in the endpoint constant, keep the service key name stable when possible, update focused tests or static scan output, and cross-check backend route ownership with `backend-api-services`.

## Stale React Query Data

Symptoms:

- A create/update/delete succeeds but the list or detail page still shows old values.
- Switching filters/pages shows inconsistent data.
- Detail views fail to refresh after a mutation.

Checks:

1. Compare the hook's `queryKey` with the mutation's `invalidateQueries` call.
2. For parameterized list keys, use `exact: false` when all pages/filter variants must refresh.
3. Invalidate both list and detail keys when a mutation changes both views.
4. Ensure route IDs are included in detail query keys and mutation invalidations where needed.
5. Look for `gcTime: 0`, `enabled`, `placeholderData`, and `refetchOnWindowFocus` overrides that change expected cache behavior.

Fix pattern: invalidate the exact action enum/key family used by the query hook, include affected entity IDs when detail keys are ID-specific, and avoid broad global refetches unless the flow truly needs them.

## Service Method Mismatch

Symptoms:

- Request body is nested under the wrong key.
- Params are sent in `data` or data is sent as query params.
- A dynamic URL function receives the wrong config shape.
- Upload progress or blob download stops working after a service refactor.

Checks:

1. Identify whether the service uses `registerNextServer`, deprecated `registerServer`, or a direct request call.
2. For `registerNextServer`, decide whether the call should pass simple data or native Axios config with the second argument set to `true`.
3. For `FormData`, confirm the request client is not trying to convert keys and that the exact backend field names are appended.
4. For dynamic endpoints, confirm path IDs are supplied in the expected config shape or native `url` override.
5. For downloads/uploads, preserve `responseType`, `signal`, and progress callbacks.

Fix pattern: keep method/URL binding in the service, keep route/page state in hooks/pages, and add a focused hook/service test or static scan when changing endpoint keys.

## Route Enum Mismatch

Symptoms:

- Navigation helper points to a path that renders 404.
- A nested dataset, chat, or agent page does not load under the expected layout.
- Lazy import succeeds but the route is unreachable.

Checks:

1. Confirm the `Routes` enum value, route config path, and component import match.
2. For nested routes, verify parent and child path concatenation does not duplicate or omit a segment.
3. For shared/widget/public pages, verify `layout: false` when the route should bypass the main app layout.
4. For sub-path deployment, check `VITE_BASE_URL`, Vite `base`, and router basename.

Fix pattern: update the enum and route config together, then verify navigation helpers and hard-coded links use the enum instead of raw strings where practical.

## Parser Config Shape Errors

Symptoms:

- Dataset or document settings save, but backend ignores new parser fields.
- RAPTOR clustering fields disappear or appear at the wrong level.
- Child chunking fields are sent as UI names instead of backend shape.
- Backend complains about unexpected `dataset_id`, `kb_id`, `chunk_method`, or parser fields.

Checks:

1. Inspect the parser-config normalization utility used by dataset/document hooks.
2. Known parser fields should remain top-level; unknown parser fields should move into `ext`.
3. RAPTOR extras should move into `raptor.ext`, with `clustering_method` and `tree_builder` normalized there.
4. Child-chunk UI options should become `parent_child` only when children are enabled.
5. Run `npm run test -- src/hooks/tests/parser-config-utils.test.ts --runInBand` from `web/` after changes.

Fix pattern: normalize UI shape in the hook/utility before calling the service. If backend parser semantics changed, coordinate with `dataset-ingestion-retrieval` rather than adding ad hoc page-level conversions.

## Agent DSL Bridge Mismatch

Symptoms:

- Agent canvas saves but reopens with missing nodes or broken edges.
- Import/export round trips change semantic fields.
- Backend executes a different graph than the UI displays.
- Historical `_layout` or components-only payloads behave unexpectedly.

Checks:

1. Preserve the canonical shape: `graph` for React Flow layout and `components` for executable topology.
2. Ensure save/export paths rebuild `components` from current `graph` state.
3. Do not reintroduce `_layout` as a wire contract; strict import reads `graph.nodes`.
4. Treat React Flow internal fields such as selection/measurement as transient, not semantic.
5. Run `npm run test -- src/pages/agent/utils/tests/dsl-bridge.test.ts --runInBand` from `web/`.

Fix pattern: update bridge utilities and tests together, keep import/export/save behavior aligned, and cross-check backend agent route contracts with `backend-api-services` when API payload shape changes.

## Jest, Vite, and Lint Confusion

Symptoms:

- A test works in Vite/browser but fails in Jest.
- Path aliases or static assets fail in tests.
- The dev server starts on an unexpected port.
- Lint passes but type-check fails, or vice versa.

Checks:

1. Jest uses `jsdom`, `esbuild-jest`, `@/` alias mapping, mocks for styles/assets, and `jest-setup.ts`.
2. Vite uses its own alias, plugins, proxy, base path, and build chunking settings.
3. `npm run test` runs Jest with coverage; use file-specific paths for focused tests.
4. `npm run lint` is ESLint only; run `npm run type-check` for TypeScript compiler errors.
5. `npm run dev` uses Vite and defaults to port `9222` unless `PORT` overrides it.

Fix pattern: choose the command that matches the failure mode. Do not debug Jest alias/mocks as if they were Vite runtime proxy problems, and do not treat lint success as type safety.

## Useful Native Candidates

Prefer these safe native checks after frontend integration changes:

- Parser config normalization: `npm run test -- src/hooks/tests/parser-config-utils.test.ts --runInBand`.
- Agent DSL bridge stability: `npm run test -- src/pages/agent/utils/tests/dsl-bridge.test.ts --runInBand`.
- Chat rendering utility behavior: `npm run test -- src/utils/tests/chat.test.ts --runInBand`.
- Static endpoint scan: `python scripts/check_web_api_keys.py --root <ragflow-checkout>` from this skill directory.

## Difficult Synthetic Cases

Use these for deeper usability verification when extending this sub-skill:

- Add a backend RESTful endpoint and wire it through endpoint constants, service, hook, page action, and React Query invalidation while proving the prefix stays `/api/v1` and stale list/detail caches refresh correctly.
- Debug a parser_config form that sends dataset/document IDs or chunk-method fields in the wrong shape, then verify normalization keeps frontend UI names out of the backend payload except through intended compatibility aliases.
