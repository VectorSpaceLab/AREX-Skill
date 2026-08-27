# Client Testing

Galaxy client unit tests use Vitest, Vue Test Utils for Vue 2 components, Pinia test utilities, `flush-promises`, shared helpers, and MSW/OpenAPI mocks for API traffic. Keep these tests isolated from a running Galaxy server; server-backed browser workflows belong outside this sub-skill.

## Test Placement and Scope

- Place tests next to the implementation with `.test.ts` or `.test.js` suffixes.
- Test the public behavior of the unit: rendered output, emitted events, API wrapper return values, store state, or user-visible state transitions.
- Do not use Vitest for end-to-end UI flows that need a running server, database, browser automation, or Selenium/Playwright.
- Prefer focused tests around one behavior per case; use descriptive expectations instead of broad truthiness.
- Reset mocks, timers, store state, and request handlers between cases.

## Targeted Commands

From `client/`:

```bash
pnpm test:watch ComponentName
pnpm test:watch src/components/Area/Component.test.ts
pnpm test src/components/Area/Component.test.ts
pnpm test
pnpm run type-check
```

Use targeted watch or file patterns while developing, then broaden to `pnpm test` and `pnpm run type-check` when the user asks for stronger validation. Dependency installation and full client test runs can be long-running; do not start them unexpectedly.

## Shared Test Helpers

Use Galaxy's shared Vitest helper module rather than re-creating framework setup:

- `getLocalVue()` configures BootstrapVue, Pinia plugin, localization, common directives, and Vue Rx shortcuts.
- `getLocalVue(true)` instruments localization strings for assertions around `l()` output.
- `injectTestRouter(localVue)` installs a lightweight Vue Router instance for component tests.
- `suppressBootstrapVueWarnings()`, `suppressLucideVue2Deprecation()`, `suppressDebugConsole()`, and `suppressExpectedErrorMessages()` keep expected noise from failing console-sensitive tests.
- Test-data factories belong in shared test data modules or local `test-utils` files when the fixture is domain-specific.

## Mounting Components

Prefer `shallowMount` for Galaxy component unit tests because it stubs child components, avoids cascading API calls, and keeps tests focused. Use full `mount` when the behavior under test requires rendered child components, slots, router interactions, plugin behavior, or a real parent-child integration point.

A typical setup combines `getLocalVue`, Pinia, a wrapper factory, and an async flush:

```ts
const localVue = getLocalVue(true);

async function mountSubject(options = {}) {
    const pinia = createTestingPinia({ createSpy: vi.fn, stubActions: false });
    setActivePinia(pinia);
    const wrapper = shallowMount(Subject as object, { localVue, pinia, ...options });
    await flushPromises();
    return wrapper;
}
```

Use stable selectors such as `data-description`, IDs already present for tests, accessible labels, or text that represents user-visible behavior. Avoid relying on implementation-only `wrapper.vm` state unless testing a legacy component with no better observable surface.

## Pinia and Stores

- For component tests, use `createTestingPinia({ createSpy: vi.fn })` when actions can be stubbed.
- Set `stubActions: false` when the real action logic is part of the behavior under test.
- Use `createPinia()` plus `setActivePinia()` for isolated store tests or when you need real store behavior and direct state setup.
- Populate stores before mounting so the initial render observes the expected state.
- Spy on store actions that perform network or worker work and resolve them deterministically.

## Async Updates

Galaxy client tests often need both Promise and Vue reactivity flushing:

- Use `await flushPromises()` after mounting components that fetch data, after triggering methods that return promises, and after MSW-handled requests.
- Use `await nextTick()` after prop changes, `setValue`, direct reactive mutation, or DOM updates that do not involve pending promises.
- When code uses debounced search or timers, use `vi.useFakeTimers()`, advance the timer explicitly, then flush promises.
- Await Vue Test Utils operations like `setValue`, `trigger`, and `setProps` before asserting.

## MSW and OpenAPI Mocks

Use the shared server mock for API calls covered by Galaxy's OpenAPI schema:

```ts
import { useServerMock } from "@/api/client/__mocks__";

const { server, http } = useServerMock();

server.use(
    http.get("/api/histories/{history_id}", ({ params, query, response }) => {
        if (query.get("view") === "detailed") {
            return response(200).json(detailedHistory);
        }
        if (params.history_id === "missing") {
            return response("4XX").json({ err_code: 404, err_msg: "History not found" }, { status: 404 });
        }
        return response(200).json(summaryHistory);
    }),
);
```

Important behaviors:

- The mock server throws on unhandled requests so missing handlers fail loudly.
- Handlers reset after each test, so install per-case overrides inside the test or `beforeEach`.
- Typed `http.get`, `http.post`, `http.put`, and similar helpers infer route params and response shapes from the OpenAPI schema.
- For endpoints not yet in OpenAPI, use `http.untyped.*` or `response.untyped(HttpResponse.json(...))` and leave a clear reason.
- To simulate errors, return the appropriate status family such as `response("4XX").json(...)` or `response("5XX").json(...)` with a concrete status.

Prefer MSW/OpenAPI mocks over Axios adapters. They exercise the same request layer as `GalaxyApi` and catch route/schema drift earlier.

## Mocking Modules and Composables

Declare module mocks before the module under test resolves imports. Common Galaxy patterns include:

- `vi.mock("@/composables/config")` plus a provided `setMockConfig(...)` helper.
- `vi.mock("@/api/resource")` for a small wrapper function when the component should not care about API transport details.
- `vi.mock("vue-router/composables")` for Composition API route params.
- Shared breadcrumb, popover, and config helpers when a legacy component expects global UI services.

Mock at the narrowest useful boundary. If the task is to test an API wrapper, use MSW. If the task is to test a component that consumes a wrapper, mocking the wrapper can be clearer.

## API-Client Package Tests

The standalone API-client package has its own Vitest tests. From `client/`:

```bash
pnpm --filter @galaxyproject/galaxy-api-client test
pnpm --filter @galaxyproject/galaxy-api-client run build
```

When testing package client creation, it is normal to mock `openapi-fetch` and assert `baseUrl`, headers, API-key behavior, trailing-slash normalization, exported methods, and error/data handling. Keep package tests independent from the main app's `@/` aliases unless intentionally testing workspace integration.

## Choosing `shallowMount` vs `mount`

Choose `shallowMount` when:

- The behavior is local to one component.
- Child components are expensive or perform their own API calls.
- You only need props, emitted events, simple slots, or rendered local markup.

Choose `mount` when:

- Slot rendering, child output, router integration, plugin behavior, or lifecycle interaction is the feature under test.
- The test is still a focused unit/integration test and does not require a real Galaxy server.

If `mount` forces extensive child mocks, reconsider whether `shallowMount` plus explicit stubs would test the behavior more directly.
