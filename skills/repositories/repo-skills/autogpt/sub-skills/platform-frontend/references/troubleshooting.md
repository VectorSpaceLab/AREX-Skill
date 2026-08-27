# Frontend Troubleshooting

## pnpm is not found

The project relies on Corepack and the `packageManager` field. Use Node 24, then enable Corepack and let it select the pinned pnpm version. Do not install a random global pnpm version as the first fix.

```bash
node -v
corepack enable
pnpm --version
```

## Generated API imports are missing

`src/app/api/__generated__` may be absent or stale before generation. Confirm the backend OpenAPI source, then run `pnpm generate:api`. Do not hand-edit generated hooks, models, or MSW handlers. If generation creates unexpected operation names, fix the backend route summary/tag or the transformer.

## API calls hit the wrong URL

Generated MSW handlers use `http://localhost:3000/api/proxy`, and runtime API calls pass through Next API/proxy routes. Confirm the frontend env, proxy route, backend port, and generated client base path before changing component code.

## Auth redirects or sessions fail

Check the route group: authenticated pages usually live in `(platform)`. Confirm Better Auth env values, proxy/auth route behavior, and protected route middleware before debugging page components. For tests, use the repository integration helpers and auth mocks rather than real sign-in.

## Vitest/MSW failures

Start from the closest `__tests__` file and `src/tests/integrations/test-utils`. Use generated MSW handlers for endpoint status variants. If a test hangs, look for missing `await screen.findBy...`, unmocked network calls, timers, or a component that assumes browser-only APIs not covered by setup mocks.

## Playwright login failures after DB reset

Delete stale files under `.auth/states` and any user-pool cache, reseed backend E2E data, then rerun the happy-path spec. Full Playwright depends on backend services, seeded accounts, and browser dependencies; a failure there is not automatically a unit-level UI bug.

## Type or lint failures after a quick UI change

Follow project conventions: function declarations, no legacy components, no raw internal anchors, no `dark:` classes, no `any`, no linter suppressors, and no unnecessary `useMemo`/`useCallback`. If a component becomes large, extract local sub-components or hooks rather than suppressing lint/type feedback.

## Next build memory or browser-only errors

The build script already sets a high Node memory limit. For browser-only code, ensure it is in a client component and does not run during server rendering. Avoid importing browser-only modules from shared files used by server routes or server components.
