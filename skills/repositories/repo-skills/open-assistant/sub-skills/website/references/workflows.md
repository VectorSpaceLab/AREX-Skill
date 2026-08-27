# Website workflows

This reference summarizes the self-contained operating knowledge for the Open-Assistant website workspace. It is written for future agents working in a checkout of the repository; use repo-root-relative commands and the bundled helper scripts rather than original repository docs or helper scripts.

## Technology boundary

- Framework: Next.js 13 with React 18 and TypeScript.
- UI libraries: Chakra UI, Tailwind CSS, Framer Motion, ByteMD Markdown editor, dnd-kit sortable lists, SWR, React Hook Form, next-i18next.
- Auth and local website data: NextAuth with Prisma and a Postgres database dedicated to website auth/session/task-cache records.
- Backend dependency: the website calls the Open-Assistant FastAPI backend for task, message, user, stats, leaderboard, and admin data. Endpoint semantics belong to the `backend` sub-skill.
- Inference dependency: chat pages call Next API routes that proxy to the inference server. Inference server/worker internals belong to the `inference` sub-skill.

## Local frontend development stack

Use two terminals.

Terminal A, from the repository root, start service dependencies:

```bash
docker compose --profile frontend-dev up --build --attach-dependencies
```

Useful variants:

```bash
# detached stack
docker compose --profile frontend-dev up --build --attach-dependencies -d

# include local inference services so the chat UI can create/stream chats
docker compose --profile frontend-dev --profile inference up --build --attach-dependencies

# CI-like service profile, including the production-built web service
docker compose --profile ci up --build --attach-dependencies

# Apple Silicon compatibility workaround when the Postgres image needs x86_64
DB_PLATFORM=linux/x86_64 docker compose --profile frontend-dev up --build --attach-dependencies
```

What the `frontend-dev` profile provides for website work:

| Service role | Purpose | Typical local port |
|---|---|---:|
| task/backend Postgres | FastAPI backend database | 5432 |
| Redis | backend cache/rate limiting and workers | 6379 |
| website Postgres | NextAuth and local task-cache database | 5433 |
| Adminer | optional DB browser | 8089 |
| Maildev | local SMTP inbox for magic-link login | 1080 / 1025 |
| FastAPI backend | task/message/user/stats API used by the website | 8080 |
| backend workers | task side effects and background jobs | internal |

Terminal B, from the website workspace:

```bash
npm ci
npx prisma db push
npm run dev
```

Then use:

- Website: `http://localhost:3000`
- Maildev inbox for email sign-in links: `http://localhost:1080`
- Debug credentials login: enabled automatically in development; for a production build or container set `DEBUG_LOGIN=true` and use the debug credential section on the sign-in page.

Run `npx prisma db push` again after restarting the dependency stack from scratch or changing the Prisma schema. The website Postgres connection is driven by `DATABASE_URL`; in Docker service context it points at the `webdb` service, while local `npm run dev` typically uses a localhost connection value.

## Environment signals that affect website behavior

These environment names matter when debugging the website layer:

| Signal | Website effect |
|---|---|
| `DATABASE_URL` | Prisma connection for website auth/session/local task cache. |
| `FASTAPI_URL`, `FASTAPI_KEY` | Target and key for the frontend-side OASST API client used by Next API routes. |
| `NEXTAUTH_SECRET`, `NEXTAUTH_URL` | NextAuth JWT/session and callback behavior. |
| `EMAIL_SERVER_HOST`, `EMAIL_SERVER_PORT`, `EMAIL_FROM` | Email magic-link provider. Local development normally targets Maildev. |
| `ENABLE_EMAIL_SIGNIN`, `ENABLE_EMAIL_SIGNIN_CAPTCHA` | Enables email sign-in and optional captcha validation on sign-in. |
| `DEBUG_LOGIN` | Enables the debug credentials provider outside ordinary dev mode. |
| `ADMIN_USERS`, `MODERATOR_USERS` | Comma-separated `provider:id` role grants used during sign-in callbacks. Empty values should still be syntactically safe. |
| `ENABLE_CHAT` | Exposes chat pages and Next API chat routes when truthy. |
| `INFERENCE_SERVER_HOST`, `INFERENCE_SERVER_API_KEY` | Target and trusted-client token data for Next API routes that proxy to inference. |
| `ENABLE_DRAFTS_WITH_PLUGINS`, `NUM_GENERATED_DRAFTS` | Controls multi-draft assistant generation behavior in chat. |
| `CLOUDFLARE_CAPTCHA_SITE_KEY`, `CLOUDFLARE_CAPTCHA_SECRET_KEY` | Captcha UI/server validation when captcha sign-in is enabled. |
| `CURRENT_ANNOUNCEMENT`, `BYE` | Browser config values surfaced through the website config API. |

Do not put secrets into browser-exposed config. The browser config API intentionally exposes only selected non-sensitive values.

## Package scripts and when to use them

Run scripts from the website workspace or through `scripts/run_frontend_checks.sh`.

| Script | Use |
|---|---|
| `npm run dev` | Start Next dev server on port 3000. Requires dependency services for authenticated task work. |
| `npm run build` | Production Next build. Use for release-readiness or config regression checks. |
| `npm run lint` | Next/ESLint checks. |
| `npm run typecheck` | TypeScript `tsc --noEmit`. |
| `npm run storybook` | Interactive Storybook on port 6006. |
| `npm run build-storybook` | Static Storybook build for CI-style component surface checks. |
| `npm run cypress` | Interactive Cypress UI. Requires local site for e2e mode. |
| `npm run cypress:run` | Full Cypress run. Requires the website and its dependencies. |
| `npm run cypress:run:contract` | Cypress contract specs against a mock or local OASST API on the expected port. Does not use a browser page base URL. |
| `npm run cypress:component` | Cypress component specs with the Next webpack dev server. |
| `npm run cypress:image-baseline` | Updates visual screenshot baselines. Use only when the visual change is intentional and approved. |
| `npm run jest` | Jest watch mode. For deterministic one-shot checks, set CI-style flags or use the bundled check wrapper. |
| `npm run fix:lint` | ESLint autofix for source files. |
| `npm run fix:format` | Prettier over source files. |
| `npm run fix` | Format plus lint autofix. |
| `npm run inlang:lint` | Localization lint against the inlang config. |
| `npm run inlang:machine-translate` | Machine translation workflow; avoid unless explicitly requested because it may rewrite locale content. |
| `npm run inlang:open-editor` | Opens the inlang editor; interactive, not a CI check. |

For most implementation tasks, the minimum useful sequence after dependencies are installed is:

```bash
npm run lint
npm run typecheck
CI=true npm run jest -- --runInBand --watch=false
```

Add Cypress component/e2e/contract checks only when the matching service requirements are satisfied.

## Prisma website data model

The website schema contains only local website records:

- `Account`, `Session`, `User`, and `VerificationToken` support NextAuth providers, JWT sessions, roles, account deletion, and email magic links.
- `RegisteredTask` stores a raw backend task JSON blob linked to a website user.
- `TaskInteraction` stores a raw reply content JSON blob linked to a registered task.

Use `npx prisma db push` for local development sync. Do not treat these tables as the canonical Open-Assistant task/message backend database; backend DB schema and task semantics are owned by the `backend` sub-skill.

## Feature flags

The website uses `react-feature-flags` for in-progress UI.

Safe feature-flag workflow:

1. Add a named flag with `isActive: false` by default.
2. Wrap temporary UI in a `Flags` gate using that flag name.
3. During local testing, enable the flag only in the working tree or dev environment.
4. Before finalizing a broadly available feature, remove the gate and remove the flag entry rather than leaving dead flags.
5. Add tests for both the hidden state and the enabled state when behavior or route visibility changes.

Feature flags are not a substitute for backend capability checks. If a flag guards backend or inference behavior, keep the owning sub-skill boundary explicit.

## Localization and inlang workflow

Locale JSON conventions:

- English is the reference language.
- Locale files are organized by language and namespace: `public/locales/<language>/<namespace>.json` inside the website workspace.
- Common namespaces include `common`, `tasks`, `labelling`, `chat`, `dashboard`, `leaderboard`, `message`, `stats`, `tos`, `account`, and `error`.
- Page data loaders use the default server-side/static translation helper, so missing keys often surface as untranslated keys at render time rather than a build failure.
- Component code frequently uses type-safe key helpers and namespace-specific `useTranslation` calls; keep new keys in the namespace that the component already uses.

Useful checks:

```bash
# bundled, read-only JSON audit
python3 <skill-subtree>/scripts/find_missing_locales.py --repo-root <repo-root>
python3 <skill-subtree>/scripts/find_missing_locales.py --repo-root <repo-root> --lang de

# package linter, may use network if dependencies/cache are missing
npm run inlang:lint
```

The bundled locale audit reports:

- missing namespace files for languages that otherwise have locale content,
- missing nested keys compared with English,
- values that are identical to English and therefore may be untranslated.

When adding UI text, update English first, then either add target-language translations or document the intentionally deferred translations and run the read-only audit.
