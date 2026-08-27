# Website troubleshooting

Use this guide to triage website failures while keeping ownership boundaries clear. If diagnosis shows backend task semantics or inference internals are the root cause, hand off to the owning sub-skill with the website-side symptom, request, and response details.

## Node, npm, and dependency installation

Symptoms:

- `npm ci` fails with engine or lockfile errors.
- Native packages fail to build.
- Lint/typecheck cannot resolve `src/...` aliases.
- Jest or Cypress command not found.

Checks and fixes:

1. Use Node 16 for the website workspace. If using nvm, select Node 16 before `npm ci`.
2. Run `npm ci` from the website workspace, not from the repository root.
3. Do not replace `npm ci` with a broad package update unless the task is specifically dependency maintenance.
4. If lockfile/package mismatch appears, inspect the intended dependency change; do not regenerate the lockfile as a blind fix.
5. If `src/...` imports fail in Jest, check that tests are executing from the website workspace and that Jest is using the Next Jest config.
6. If browser tooling fails after a partial install, remove the website workspace's `node_modules` and rerun `npm ci`.

## Docker profile and service dependency confusion

Symptoms:

- Website starts but task pages return errors.
- Mail login works but task fetch fails.
- Prisma cannot connect to the web database.
- Cypress e2e cannot authenticate.
- Chat page appears but generation/streaming fails.

Profile map:

| Need | Profile |
|---|---|
| Website task development with backend, Redis, website DB, Maildev | `frontend-dev` |
| CI-like full stack with built web service | `ci` |
| Chat UI against local inference | `frontend-dev` plus `inference` |
| Backend-only API work | route to `backend` sub-skill |
| Inference worker/server work | route to `inference` sub-skill |

Checks and fixes:

1. Start the dependency stack from the repository root.
2. Use `--attach-dependencies` while debugging so service health failures are visible.
3. Confirm `webdb` is healthy before running Prisma commands.
4. Confirm the FastAPI backend is reachable before debugging frontend task state.
5. Do not expect the `frontend-dev` profile alone to run model inference; add the inference profile for chat generation.
6. On Apple Silicon, set `DB_PLATFORM=linux/x86_64` if the Postgres image architecture fails.
7. If ports 3000, 5432, 5433, 6379, 8080, 1080, or 1025 are already in use, stop the conflicting process or adjust local configuration consistently.

## Maildev, magic email, and debug login

Symptoms:

- Email sign-in does not deliver a link.
- Cypress `signInWithEmail` hangs or cannot find email HTML.
- Debug credentials are not shown on the sign-in page.
- Captcha blocks local sign-in.

Checks and fixes:

1. Maildev must be running and exposed on its web/API port for email sign-in flows.
2. Email provider env must point at the Maildev SMTP host/port in local development.
3. The Cypress email helper expects the Maildev API environment values to match the local service.
4. Debug credentials are available automatically in dev mode. For non-dev builds, set `DEBUG_LOGIN=true`.
5. If email sign-in captcha is enabled locally, Cypress uses a dummy token; disable captcha for local e2e unless the task is captcha integration.
6. After login, tests force backend frontend-user creation and TOS acceptance. If that fails, inspect the backend API connection before assuming an auth bug.
7. Role-specific admin/moderator failures depend on `ADMIN_USERS` and `MODERATOR_USERS` entries in `provider:id` form.

## Prisma, `DATABASE_URL`, and local website DB

Symptoms:

- `npx prisma db push` cannot connect.
- NextAuth login throws Prisma errors.
- Website container waits for Postgres indefinitely.
- Local task registration fails after backend task fetch succeeds.

Checks and fixes:

1. Verify `DATABASE_URL` points to the website DB, not the backend task DB. The website DB stores NextAuth and local task-cache tables.
2. For local host-based dev, the website DB is commonly exposed on a localhost port distinct from the backend Postgres port.
3. For Docker service context, the database host is the service name, not localhost.
4. Run `npx prisma validate` to catch schema issues before DB connectivity debugging.
5. Run `npx prisma db push` after starting a fresh local stack or modifying the schema.
6. `db push` is for local synchronization; do not describe it as a production migration plan.
7. If task registration fails, distinguish local Prisma write failure from backend task fetch failure by checking which route returns the error.

## Cypress base URL, mock backend, and contract tests

Symptoms:

- E2E tests fail at `cy.visit` or cannot reach `/auth/signin`.
- Auth helper cannot read Maildev.
- Random task e2e reports no tasks available.
- Contract test cannot connect to localhost backend.
- Contract test throws `OasstError` with unexpected fields.

Checks and fixes:

1. E2E tests use `http://localhost:3000` as the base URL; start the Next dev server before running e2e.
2. Authenticated e2e needs Maildev, website DB, backend, and backend dependencies from the frontend-dev profile.
3. The random task loop needs backend seed/debug data to supply tasks. If no tasks are available, route task availability semantics to `backend` after verifying the website request path.
4. Contract tests do not use a page base URL. They call the OASST API client against the expected backend/mock port.
5. A contract connection refusal means the mock or backend is absent; a structured error mismatch means the API contract or client parser changed.
6. Use `data-cy` selectors and accessibility hooks. Avoid selectors based on Chakra class names, DOM depth, text that is likely to be translated, or visual layout.
7. If a Cypress component visual comparison fails, inspect the diff and update baselines only for approved visual changes.

## Robust `data-cy` selector coverage

Critical selectors:

| UI surface | Selector |
|---|---|
| Task container | `data-cy="task"` |
| Task type discriminator | `data-task-type` on the task container |
| Task id display | `data-cy="task-id"` |
| Create reply editor | `data-cy="reply"` |
| Review button | `data-cy="review"` |
| Submit button | `data-cy="submit"` |
| Edit button | `data-cy="edit"` |
| Label yes/no question row | `data-cy="label-question"` |
| Label yes/no choices | `data-cy="yes"`, `data-cy="no"` |
| Likert row | `data-cy="label-options"` |
| Likert option | `data-cy="radio-option"` |
| Evaluate sorter | accessibility role description `sortable` |

If a UI change removes or renames one of these hooks, update tests and migration notes together. For task pages, keep the route, `TaskInfos`, component selector, and e2e flow synchronized.

## Jest and jsdom failures

Symptoms:

- Stream tests complain about missing `ReadableStream`, `TextEncoder`, or `TextDecoderStream`.
- Tests fail because `console.warn` or `console.error` was called.
- Components using translations fail unexpectedly.
- Next router-dependent tests fail.

Checks and fixes:

1. Ensure Jest uses the website Jest setup. The setup provides stream/text polyfills for SSE tests.
2. Console warn/error are intentionally fatal in tests. If warning output is expected, spy on the console method, assert it, and restore it.
3. The i18n hook mock returns translation keys. Tests should not assume real translated strings unless they load i18n explicitly.
4. Use a mock Next router provider for components that call router methods or expect route fields.
5. For one-shot CI-style runs, disable watch mode with CI/CLI flags or the bundled frontend check wrapper.

## Chat enablement and inference host/config signals

Symptoms:

- Chat pages or chat API routes return 404.
- Model list or plugin list never loads.
- Sending a prompt creates a user message but no assistant response.
- Assistant response remains pending forever.
- Retry/draft selection is blocked.

Checks and fixes:

1. Server-side chat routes require `ENABLE_CHAT` to be truthy.
2. The browser config also exposes `ENABLE_CHAT`, `ENABLE_DRAFTS_WITH_PLUGINS`, and `NUM_GENERATED_DRAFTS`; stale config can make UI state disagree with server behavior.
3. Next API chat routes proxy to `INFERENCE_SERVER_HOST` and use a trusted-client token built from `INFERENCE_SERVER_API_KEY` and the user session.
4. If model/plugin fetch fails, confirm the inference server is reachable before changing chat UI state.
5. If chat creation returns 404 for a new user, the inference client tries trusted login once and retries chat creation. Persistent 404s likely belong to inference auth/user setup.
6. If multi-draft selection is pending, the form intentionally blocks new submissions until a draft is selected.
7. If plugins are enabled and drafts-with-plugins is disabled, retry behavior chooses single assistant generation rather than multi-draft generation.

## SSE chunks, CRLF, and streamed response bugs

Symptoms:

- Tokens appear concatenated incorrectly.
- JSON parse errors appear only for streamed responses.
- Works locally but fails behind a proxy or different browser.
- Final token is missing when stream ends without newline.

Checks and fixes:

1. The SSE iterator line-buffers chunks; never parse each raw `Uint8Array` independently.
2. Preserve support for both `\n` and `\r\n` line endings.
3. Multiple SSE lines can arrive in one decoded chunk and must yield separately.
4. Partial final lines without a newline are intentionally ignored by the current iterator; if changing this, update tests and confirm inference stream framing.
5. `event: error` and JSON `event_type: error` are different surfaces; the handler supports both patterns.
6. Malformed JSON currently logs a parse error and continues. If changing to hard-fail, update UX and tests.
7. Add regression tests for split `data:` prefixes, CRLF, commas/backslashes/backticks in JSON strings, multiple lines per chunk, and unfinished final lines.

## Feature flag cleanup

Symptoms:

- Feature visible locally but hidden in CI/prod.
- Dead flag leaves unreachable code.
- Tests pass only when a dev-only flag is active.

Checks and fixes:

1. Default new flags to inactive before final handoff unless the feature is deliberately released.
2. Test hidden and enabled states for UI that remains behind a flag.
3. Remove flag wrappers and flag entries when the feature becomes permanent.
4. Avoid using flags to hide broken backend/inference dependencies without documenting the boundary.

## Inlang and locale failures

Symptoms:

- UI renders key names instead of translated text.
- Locale audit reports missing namespace files or missing nested keys.
- `inlang:lint` reports reference-language mismatch.
- A target language has values identical to English.

Checks and fixes:

1. Add English reference keys first.
2. Keep namespace names aligned with the component's `useTranslation` call.
3. Add target language namespace files when English gains a new namespace and a locale already has other content.
4. Treat identical-to-English values as review candidates, not automatic errors. Technical strings, names, and URLs may legitimately match.
5. Use the bundled read-only locale audit before and after editing translations.
6. Avoid `inlang:machine-translate` unless the user explicitly authorizes translation writes.

## Boundary handoff checklist

When routing out, include:

- User-visible route or component affected.
- Website API route and HTTP status/body if available.
- Relevant environment signals without secrets.
- Whether local Prisma, Maildev, Next dev server, and Docker services were healthy.
- For chat, whether the failure happened before message create, during assistant create, during SSE fetch, or while parsing streamed chunks.
- For tasks, whether failure happened during new task fetch, local registration, ack, local interaction write, backend interaction, or next-task refresh.
