# Website testing reference

Use this reference to choose checks for website changes. Prefer targeted, deterministic checks before broad e2e runs. Use the bundled `scripts/run_frontend_checks.sh` wrapper when you want a repo-root-oriented command that does not depend on original helper scripts.

## Quick check selector

| Change type | Minimum checks | Add when services are available |
|---|---|---|
| Pure TypeScript/lib change | `typecheck`, targeted one-shot Jest | lint |
| React component behavior | lint, typecheck, targeted Jest/RTL or Cypress component | Storybook build if story surface changed |
| Contribution task UI | lint, typecheck, Jest/RTL for reducer/component logic, Cypress component or targeted e2e selectors | random task e2e with frontend-dev stack |
| Frontend API client | typecheck, contract/client tests with mocked fetch, Cypress contract if mock backend/local backend is running | backend integration checks via `backend` sub-skill |
| Chat/SSE parsing | one-shot Jest for stream iterator/handler cases, typecheck | e2e chat smoke only with inference profile |
| Localization | bundled locale audit, `inlang:lint` | page/component render check in target locale |
| Prisma/auth local dev | `npx prisma validate`, `npx prisma db push` against local web DB | magic-link/debug login Cypress smoke |
| Storybook/story changes | build Storybook | Cypress component/visual baseline only when intentional |

## Bundled frontend check wrapper

From any directory:

```bash
<skill-subtree>/scripts/run_frontend_checks.sh --repo-root <repo-root> lint typecheck jest
```

Available checks:

- `install`: `npm ci`
- `lint`: `npm run lint`
- `typecheck`: `npm run typecheck`
- `jest`: one-shot CI-style Jest invocation based on the package's `jest` script
- `cypress-contract`: `npm run cypress:run:contract`
- `cypress-run`: `npm run cypress:run`
- `storybook-build`: `npm run build-storybook`

If no check names are supplied, the wrapper runs `lint typecheck jest`. It prints each command before executing it and runs from the website workspace.

## Jest and React Testing Library

Jest is configured through Next's Jest adapter with jsdom. Important properties:

- `moduleDirectories` include the website root, so imports using the `src/...` alias resolve in tests.
- `setupFilesAfterEnv` installs jest-dom matchers.
- The setup file polyfills `TextEncoder`, `TextDecoder`, `TextDecoderStream`, and `ReadableStream`; this is why stream parser tests can run under Jest.
- The setup file turns `console.warn` and `console.error` into test failures. If a warning/error is intentional, explicitly spy on the console method and assert it.
- The i18n hook is mocked so component tests can render translation keys without loading locale files.

Conventions:

- Non-React unit tests end in `.test.ts`.
- React component/page tests end in `.test.tsx`.
- Keep tests close to the code under test when adding new unit coverage.
- Use React Testing Library queries by role/text/label before implementation details. Use the provided mock router pattern when a component depends on Next router navigation.
- For task UI, assert the review/submit state machine and response content shape rather than only snapshots.

One-shot Jest examples:

```bash
# all Jest tests, non-watch
CI=true npm run jest -- --runInBand --watch=false

# targeted stream parser test
CI=true npm run jest -- --runInBand --watch=false --testPathPattern=chat_stream

# targeted page/component pattern
CI=true npm run jest -- --runInBand --watch=false --testPathPattern=test_pages
```

High-value native Jest candidates:

- SSE iterator tests that split `data:` lines across chunks, handle CRLF, handle multiple lines in one chunk, and ignore unfinished final lines.
- Page render smoke tests for top-level public pages.
- Task container/reducer tests that exercise `EDIT -> DEFAULT_WARN -> REVIEW -> SUBMITTED` and error return-to-edit behavior.

## Cypress component tests

Cypress component tests use the Next framework dev server with webpack. The configured spec pattern is a component-test directory under Cypress support, while many component tests may still be colocated by convention; check current config before adding a spec.

Use component tests when:

- The component needs a browser DOM, Chakra styling, drag/drop, or Cypress visual assertions.
- You can mount the component with fake data and avoid the full backend stack.
- You need stable `data-cy` or accessibility selector coverage.

Component test guidance:

- Mount with explicit fake props/context providers.
- Prefer `data-cy` hooks for task controls and editor interactions; prefer roles for generic controls.
- For dnd-kit sorting, keyboard interaction is often more deterministic than pointer drag in CI.
- Visual baseline updates are not automatic fixes. Only update baselines after confirming the visual change is expected.

Useful command:

```bash
npm run cypress:component
```

## Cypress e2e tests

E2E tests assume the website is reachable at `http://localhost:3000`. The local dependency stack must include Maildev and backend services for authenticated task flows.

Authentication helper behavior:

1. Request NextAuth CSRF token.
2. Post to email sign-in with a dummy captcha token.
3. Poll Maildev for the email, extract the callback link, and visit it.
4. Force backend frontend-user creation through the available-tasks route.
5. Accept terms of service through the TOS route.

Stable selectors and flows:

- Task root: `data-cy="task"`
- Concrete task type: `data-task-type="create-task"`, `evaluate-task`, `label-task`, or `spam-task`
- Markdown reply editor: `data-cy="reply"`
- Task id display: `data-cy="task-id"`
- Review button: `data-cy="review"`
- Submit button: `data-cy="submit"`
- Edit button: `data-cy="edit"`
- Label yes/no rows: `data-cy="label-question"`, with child `data-cy="yes"` and `data-cy="no"`
- Likert rows: `data-cy="label-options"`, with child `data-cy="radio-option"`
- Sortable evaluate items: use the accessibility role description `sortable` and keyboard sequence Enter, Arrow, Enter.

Native e2e candidate:

- Random task loop: sign in, visit `/tasks/random`, inspect `data-task-type`, complete create/evaluate/label tasks through stable selectors, and assert the task id changes after submit. This is valuable because it exercises task fetching, local registration, UI validation, review/submit, backend interaction, and next-task refresh.

Useful commands:

```bash
# interactive e2e/component runner
npm run cypress

# all configured Cypress tests
npm run cypress:run
```

## Cypress contract tests

Contract tests are separate from page e2e tests and use a config with no base URL. They expect a mock or local OASST API server on the port encoded in the test client. The contract suite checks both API-client behavior and basic backend contract shape:

- fetch a task,
- ack a task,
- record a task interaction,
- return `null` for HTTP 204,
- throw `OasstError` when a non-2xx response has structured OASST error JSON,
- throw generic `OasstError` when a non-2xx response has unknown text.

Useful command:

```bash
npm run cypress:run:contract
```

If the contract test cannot connect, first verify whether a mock backend or local backend is actually running on the expected host/port. If the connection succeeds but response shape fails, route backend contract semantics to the `backend` sub-skill.

## Storybook

Storybook uses the Next.js Storybook framework, Chakra addon, public static assets, and decorators for Next router/session context.

Use Storybook when:

- Developing reusable visual components,
- Reproducing UI state without the full service stack,
- Creating stories for task/message/sortable components,
- Checking Chakra theme and layout regressions.

Commands:

```bash
npm run storybook
npm run build-storybook
```

Story guidance:

- Prefer realistic task/message fixtures but keep them small and free of external dependencies.
- Provide the Task context explicitly for task stories.
- Add router/session decorators for components that assume NextAuth or Next router.
- Do not use Storybook stories as substitutes for assertion-backed tests when behavior matters.

## Localization checks

Read-only audit:

```bash
python3 <skill-subtree>/scripts/find_missing_locales.py --repo-root <repo-root>
python3 <skill-subtree>/scripts/find_missing_locales.py --repo-root <repo-root> --lang de
```

Package lint:

```bash
npm run inlang:lint
```

Interpretation:

- Missing file: a target language lacks a namespace file present in English.
- Missing key: a target namespace exists but lacks a key path found in English.
- Potentially untranslated: target value exactly equals English reference value. This can be valid for names, acronyms, URLs, and technical strings; review before changing.

## Prisma/auth checks

Useful checks from the website workspace:

```bash
npx prisma validate
npx prisma db push
```

Run these only against a local development database. `db push` mutates the local schema to match the Prisma schema and should not be treated as a production migration workflow.

## Testing anti-patterns

- Do not select by generated Chakra/CSS class names when a `data-cy` hook or role exists.
- Do not make a Jest test depend on a real backend, Maildev, or inference server.
- Do not run Cypress e2e without the frontend-dev stack and a reachable Next dev server.
- Do not update visual baselines just to make CI green.
- Do not use chat e2e failures to infer model/worker bugs until the website API route status, `ENABLE_CHAT`, and SSE parser behavior have been checked.
- Do not run machine translation as part of routine verification unless the user explicitly asked to modify locale content.
