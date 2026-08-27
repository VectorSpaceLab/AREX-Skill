# Frontend Apps Troubleshooting

Start by confirming which app is failing:

```bash
python scripts/check_frontend_packages.py --repo-root <bisheng-checkout>
```

## Install and Import Failures

### Wrong working directory

Symptoms:
- `npm run dev` or `npm start` reports a missing script.
- Package install unexpectedly tries to use the wrong lockfile.

Fix:
- Platform commands run from `src/frontend/platform/`.
- Client commands run from `src/frontend/client/`.
- There is no shared root frontend script contract for normal app work; use each app's `package.json`.

### Node/npm dependency mismatch

Symptoms:
- Vite plugin failures, TypeScript parser errors, or package engine warnings.
- Platform local package install fails around `vditor`.

Fix:
- Use Node 18 or newer.
- Run `npm install` in the specific app directory.
- Platform depends on a local `local-packages/vditor-3.11.1.tgz`; if install cannot find it, verify the app-local package tree before changing dependency versions.
- Avoid upgrading shared React, router, query, state, or UI libraries as a bug workaround.

### Alias or case-sensitive import errors

Symptoms:
- Vite resolves imports locally but CI/Linux fails.
- Jest cannot resolve `~/...`, or Vitest cannot resolve `@/...`.

Fix:
- Platform alias is `@/` to `src/`.
- Client aliases are `~/` and `@/` to `src/`; Jest also maps `test/*`.
- Client has `npm run check-imports` for case-sensitive import checks.
- Keep imports inside the owning app; do not import from the sibling app.

### Query library split mistakes

Symptoms:
- `QueryClientProvider` type errors.
- Hooks fail at runtime because the wrong context is installed.

Fix:
- Platform imports from `react-query` v3.
- Client imports from `@tanstack/react-query` v4.
- Do not move query hooks between apps without translating the query API and test providers.

### Direct axios or store HTTP violations

Symptoms:
- Architecture guard reports frontend store HTTP usage.
- Error toasts, 401/403 redirects, license messages, or envelope unwrapping behave inconsistently.

Fix:
- Business code must not `import axios` directly.
- Platform API modules import from `@/controllers/request` and live under `@/controllers/API/`.
- Client API code uses `~/api/request.ts` and query hooks under `~/hooks/queries/`.
- Stores may hold state only; move network calls to API/query layers.

### Client icon prebundle stale after icon upgrade

Symptoms:
- Client page crashes with `Element type is invalid` after changing `bisheng-icons`.

Fix:
```bash
cd src/frontend/client
npm run dev -- --force
# or
rm -rf node_modules/.vite && npm run dev
```

## Optional Services and Backend Connectivity

### API proxy points to the wrong service

Symptoms:
- `/api/...` returns 404 in dev.
- Gateway-only endpoints fail when running against bare FastAPI, or bare FastAPI endpoints fail through an unexpected gateway.

Fix:
- Platform uses `VITE_PROXY_TARGET` in `src/frontend/platform/vite.config.mts`.
- Client uses `VITE_DEV_API_TARGET` in `src/frontend/client/vite.config.ts`.
- In commercial gateway mode, point the app proxy at the gateway rather than FastAPI.
- If the backend contract is unclear, route backend API semantics to `backend-core` or permission semantics to `identity-permissions-tenancy`.

### MinIO files or images return 403

Symptoms:
- Image/file URLs under `/bisheng` or `/tmp-dir` load as 403.
- Dev console warns about MinIO SigV4 host mismatch.

Fix:
- The dev proxy target host must exactly match backend `object_storage.minio.sharepoint`; `127.0.0.1` and `localhost` are not interchangeable for signed URLs.
- Platform env: `VITE_MINIO_PROXY_TARGET`.
- Client env: `VITE_DEV_MINIO_TARGET`.
- Do not work around this by stripping signatures or adding auth headers to MinIO object requests.

### Client base path or PWA interference

Symptoms:
- Client routes work directly but fail under `/workspace`.
- OAuth callback, standalone chat, or dev HMR behaves unexpectedly.

Fix:
- Preserve Client `base: '/workspace'` and router basename from `__APP_ENV__.BASE_URL`.
- Client proxy rewrites `/workspace/api`, `/workspace/bisheng`, and `/workspace/tmp-dir` by removing `/workspace` before forwarding.
- Service worker registration is disabled in development; production PWA changes need route-level testing, especially OAuth denylist and offline cache behavior.

## Data and Runtime Config Issues

### Brand names or theme do not apply

Symptoms:
- UI renders raw `BISHENG`, wrong Linsight name, or hardcoded blue/green colors.
- Switching to green theme leaves some brand UI blue.

Fix:
- Brand names come from `window.BRAND_CONFIG` and i18n interpolation variables.
- Client brand theme is driven by Recoil `brandTheme`, `applyBrandTheme()`, and CSS variables.
- Replace hardcoded brand hex values with `blue-*` Tailwind classes or `rgb(var(--brand-NNN))`.
- For themed illustrations use `rgb(var(--illus-NNN))`; leave semantic success/error/warning colors and third-party logos fixed.

### Locale keys render as raw strings

Symptoms:
- UI shows `errors.21000`, `api_errors.403`, or a nested key path instead of translated text.

Fix:
- Platform: add the key to the correct namespace in `public/locales/{en-US,zh-Hans,ja}/`. If a component renders early, ensure the namespace is eagerly loaded in `src/i18n.js`.
- Client: add keys to all three `src/locales/{en,zh-Hans,ja}/translation.json` files and use `useLocalize()`.
- Respect `window.APP_CONFIG.disableJa`; do not depend on Japanese being available at runtime.

### Auth and redirect state is stale

Symptoms:
- Login loops, unexpected jump to admin panel, or stale chat preferences after relogin.

Fix:
- Platform token comes from `localStorage.ws_token`; request interceptors handle expiration and SSO redirects.
- Client request handling distinguishes production admin-panel redirects, guest standalone chat, and auth routes. Preserve these branches instead of adding component-level redirects.
- Do not manually handle 403 in business components; response interceptors and route gates own it.

## API and CLI Misuse

### Wrong app command

Symptoms:
- `npm start` opens Platform but the task is Client, or `npm run dev` fails in Platform.

Fix:
- Platform: `npm start -- --host 0.0.0.0`, `npm run build`, `npm test`.
- Client: `npm run dev`, `npm run build`, `npm run check-imports`, `npm run test:ci`.

### Passing backend paths to frontend helpers

Symptoms:
- Frontend helper reports missing package files.

Fix:
- Run helpers with `--repo-root .` from the repository root or pass the repository root explicitly.
- The checker expects `src/frontend/platform/package.json` and `src/frontend/client/package.json` under that root.

### Editing API callers instead of contracts

Symptoms:
- Many components start parsing `{ status_code, data }` manually.
- One component handles 403 differently from the rest of the app.

Fix:
- Normalize response handling in request/API/query layers.
- If backend envelope semantics are wrong, route to `backend-core`; do not patch every frontend caller.

## Workflow-Specific Failures

### Route is hidden for an allowed user

Platform checks:
- Verify route `permission` matches backend `web_menu` keys.
- Remember `/sys` allows `sys` or `system_config`.
- Department admins may need `create_app` fallback; child admins receive a specific admin route fallback set.
- Use route permission tests as the first regression target.

Client checks:
- Verify the correct `MenuApprovalPluginGate pluginId` is used.
- Landing behavior depends on plugin availability and menu approval mode.
- If the plugin source or ReBAC decision is wrong, route to `identity-permissions-tenancy`.

### Standalone chat or app chat opens in the wrong SPA

Checks:
- Platform standalone chat routes mostly redirect to `/workspace` Client routes.
- Client maintains legacy `/chat/:conversationId/:fid/:type` redirection to `/app/...`.
- Guest standalone chat must not be forced through authenticated refresh/login behavior.

### UI tests fail only after adding a provider-dependent component

Fix:
- Platform: wrap focused renders with app test utilities that include `QueryClientProvider` and required global providers.
- Client: use existing layout/test utilities and include Recoil/auth/router setup as needed.
- Mock request wrappers, not raw axios.

### Build size or chunking regresses

Checks:
- Platform manually chunks PDF, xlsx/document parsing, editor, markdown, and generic vendor dependencies.
- Client has finer manual chunks for sandpack, virtualization, i18n, utilities, date utilities, avatars, forms, routing, security UI, CodeMirror, and other large libraries.
- Avoid adding a new heavyweight frontend dependency; reuse current libraries.
