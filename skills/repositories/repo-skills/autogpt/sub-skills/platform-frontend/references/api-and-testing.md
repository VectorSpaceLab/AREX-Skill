# Frontend API Generation and Testing

## Command order

For frontend code changes, run:

```bash
pnpm format
pnpm lint
pnpm types
pnpm test:unit
```

Use `pnpm generate:api` after intentional backend route/OpenAPI changes. Full `pnpm test` builds the app and then runs Playwright; do not use it as a casual smoke check.

## API generation

The generation flow is:

1. Backend route/schema changes are implemented and validated in the backend.
2. `src/app/api/openapi.json` is refreshed by the frontend generation script.
3. Orval reads `orval.config.ts`, applies `fix-tags.mjs`, and writes generated endpoints, models, React Query hooks, and MSW handlers under `src/app/api/__generated__`.
4. Generated files are formatted by the Orval hook.

Command:

```bash
pnpm generate:api
# or force refresh when a local cached schema must be ignored:
pnpm generate:api:force
```

Do not hand-edit generated files. If a hook name, model, status handler, or operation is wrong, fix the backend OpenAPI operation or Orval config and regenerate.

## Integration tests: the default

Vitest + React Testing Library + MSW is the primary test strategy. Tests live in a `__tests__/` folder near the page or component being tested. Prefer page-level tests for features and route behavior.

Typical pattern:

```tsx
import { render, screen } from "@/tests/integrations/test-utils";
import { server } from "@/mocks/mock-server";
import { getGetV2ListLibraryAgentsMockHandler200 } from "@/app/api/__generated__/endpoints/library/library.msw";
import LibraryPage from "../page";

test("renders library agents", async () => {
  server.use(getGetV2ListLibraryAgentsMockHandler200());
  render(<LibraryPage />);
  expect(await screen.findByText(/agent/i)).toBeDefined();
});
```

Use `findBy...` queries for async rendering. Prefer generated MSW handlers and response builders over ad hoc API objects. Use direct hook tests only for shared hooks with standalone business logic that cannot be exercised through the UI.

## Unit and component tests

Use co-located unit tests for pure helpers, shared hooks, and isolated components with meaningful logic. Do not test third-party library internals, CSS implementation details, or simple prop plumbing. Storybook is the right place for visual/design-system states.

## Playwright E2E

E2E specs live in `src/playwright/*-happy-path.spec.ts` and import `test`/`expect` from `./coverage-fixture`. The suite covers critical real-browser journeys such as auth, settings/API keys, Builder, Library, Marketplace, Publish, and Copilot.

Common commands:

```bash
pnpm test:e2e:no-build
pnpm test
pnpm test-ui
```

Playwright requires a running backend stack and seeded data. The documented seed flow uses backend test data scripts and creates reusable auth state under `frontend/.auth/states/`. If the DB is reset, delete stale auth state and reseed.

## Storybook

Use Storybook/Chromatic for design-system components and visual state coverage:

```bash
pnpm storybook
pnpm build-storybook
pnpm test-storybook
```

Add or update stories when creating or materially changing atoms, molecules, or organisms.
