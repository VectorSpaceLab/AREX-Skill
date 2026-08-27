# Platform Frontend Architecture

## Package and runtime

The frontend lives under `autogpt_platform/frontend`. It is a Next.js 15 App Router application using React 18, TypeScript, Tailwind, React Query, Orval-generated API clients, MSW, Vitest, Playwright, and Storybook. The package declares Node `24.x` and Corepack-managed `pnpm@10.20.0`.

Run commands from `autogpt_platform/frontend` after enabling Corepack and installing dependencies:

```bash
corepack enable
pnpm install
```

## App structure

| Area | Purpose |
| --- | --- |
| `src/app/(platform)/` | Authenticated app shell and product pages such as Builder, Copilot, Library, Marketplace, settings, admin, team, and artifacts |
| `src/app/(no-navbar)/` | Login, signup, onboarding, share/link, and other pages without the Platform chrome |
| `src/app/(public)/` | Public tour/chat routes |
| `src/app/api/` | Next API proxy/auth/chat/transcription routes, OpenAPI source, mutators, transformers, and generated clients |
| `src/components/` | Design system atoms/molecules/organisms plus contextual components |
| `src/mocks/` | MSW server and aggregated handlers |
| `src/tests/integrations/` | Vitest/RTL setup, provider-wrapped render helper, Next.js mocks, auth mock helpers |
| `src/playwright/` | Real-browser happy-path E2E specs, coverage fixture, global setup, and auth state utilities |

`src/components/__legacy__` exists but should not be used for new code.

## Component and page conventions

- Use App Router under `src/app`; do not introduce `pages/` routes.
- Prefer client-first components. Server components/actions are reserved for cases where they clearly reduce complexity or are needed for SEO/performance.
- Pages go under semantic route segments. Non-trivial page logic belongs in `use<PageName>.ts` or cohesive hooks next to the page.
- Sub-components belong in local `components/` folders when they are feature-specific.
- A component with logic should split render, hook, and pure helpers: `ComponentName.tsx`, `useComponentName.ts`, and `helpers.ts`.
- Use function declarations for components and handlers. Use callbacks as inline/arrow callbacks where appropriate.
- Avoid `useMemo` and `useCallback` unless there is a measured performance reason.
- Keep render functions and hooks small; split large files by responsibility.

## Data fetching

Use generated React Query hooks and types from `@/app/api/__generated__/endpoints/...` and `@/app/api/__generated__/models/...`. `BackendAPI` and legacy server API helpers are deprecated for new uses.

The frontend generation source is `src/app/api/openapi.json`, transformed by `src/app/api/transformers/fix-tags.mjs`, and emitted by Orval with `tags-split` output under `src/app/api/__generated__`. Generated MSW handlers use base URL `http://localhost:3000/api/proxy`.

## UI and styling

- Tailwind CSS only, using design tokens.
- Use design-system components from `src/components/atoms`, `molecules`, and `organisms`.
- Use Hugeicons through the `Icon` atom; do not render `HugeiconsIcon` directly.
- Use Next.js `Link` or the project `Link` atom for internal navigation; avoid raw internal anchors.
- Avoid `dark:` classes; the design system owns dark mode.
- Do not use linter suppressors or `any` unless the value genuinely can be anything.

## Product surfaces

- Builder (`src/app/(platform)/build`) owns graph editing, nodes, edges, run dialogs, block menu, save/duplicate logic, tutorial state, and stores.
- Copilot (`src/app/(platform)/copilot`) owns chat sessions, tools, artifacts, onboarding, rate-limit UI, and sharing.
- Library and Marketplace own saved agents, presets, search, publication, and marketplace cards.
- Settings/admin/team/auth areas own account, API keys, OAuth apps, integrations, billing, users, diagnostics, and protected route behavior.
