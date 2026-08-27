# Frontend Apps Workflows

## App Split Map

| Concern | Platform app | Client app |
|---|---|---|
| Repo path | `src/frontend/platform/` | `src/frontend/client/` |
| User surface | Admin, model/config, knowledge, workflow/app builder | End-user workspace, chat, app chat, Linsight, knowledge browsing, subscriptions |
| Dev server | `npm start -- --host 0.0.0.0` on `:3001` | `npm run dev` on `:4001`, strict port, base `/workspace` |
| Build | `npm run build` | `npm run build` |
| Tests | `npm test` / `npm run test:coverage` (Vitest + jsdom) | `npm run test:ci` (Jest + jsdom) |
| Request wrapper | `@/controllers/request.ts`; API modules in `@/controllers/API/` | `~/api/request.ts`; API/query code under `~/api/` and `~/hooks/queries/` |
| Query library | `react-query` v3 | `@tanstack/react-query` v4 |
| State | Zustand stores in `@/store/`; React Context in `@/contexts/` | Recoil atoms/selectors in `~/store/` |
| UI | `@/components/bs-ui/`, `@/components/bs-icons/` | `~/components/ui/`, `bisheng-icons` first, `lucide-react` fallback |
| i18n | `useTranslation()`; `public/locales/{en-US,zh-Hans,ja}/{ns}.json` | `useLocalize()`; `src/locales/{en,zh-Hans,ja}/translation.json` |

Run the bundled checker whenever stack drift is suspected:

```bash
python scripts/check_frontend_packages.py --repo-root <bisheng-checkout>
```

## Universal Frontend Triage

1. Classify the edited path. If it starts with `src/frontend/platform/`, use only Platform rules. If it starts with `src/frontend/client/`, use only Client rules.
2. Read the nearest app instruction file before editing: `src/frontend/platform/AGENTS.md` or `src/frontend/client/AGENTS.md`.
3. Confirm the task's backend dependency. Frontend work may call `/api/v1` or `/api/v2`, but backend contracts and permission semantics belong to sibling sub-skills.
4. Keep requests out of stores. Put HTTP calls in the app request/API layer, then call them from hooks/components/query functions.
5. Use existing providers in tests. Platform tests often need a `react-query` `QueryClientProvider`; Client tests may need Recoil, auth, router, and local storage setup.
6. Verify with the narrowest command first, then the app-level command if behavior spans routing, providers, aliases, or package configuration.

## Platform Workflow

### Route and navigation changes

- Main route definitions live in `src/frontend/platform/src/routes/index.tsx`.
- Page components are lazy-loaded and usually mounted under `MainLayout` unless they are full-screen editors/share/report/chat compatibility routes.
- Routes can carry a `permission` key. `getPrivateRouter()` filters by current `web_menu`; `getAdminRouter()` keeps all private routes.
- Preserve special permission mapping such as `sys` accepting `system_config`, department admin fallback for `create_app`, and child-admin fallback permissions.
- Standalone chat routes under Platform are compatibility/redirect surfaces into Client `/workspace`; do not re-implement Client chat UI inside Platform.

Checklist:

```bash
cd src/frontend/platform
npm test -- --runInBand=false src/test/resolveRoutePermissions.test.ts
npm test
```

If a single Vitest filename is not accepted by the local npm script, run `npx vitest run <file>` from the same app directory.

### API and data flow

- Add or adjust API functions under `src/frontend/platform/src/controllers/API/`.
- Import the wrapped axios instance from `@/controllers/request`, not from `axios`, in API modules.
- Component-side callers can use `captureAndAlertRequestErrorHoc(...)` from `@/controllers/request` when they need the app's existing toast behavior.
- Platform response handling unwraps `{ status_code, status_message, data }`, treats blobs as downloads, redirects some GET 403/404 responses, handles login expiration, and throttles license-expired toasts.
- For query caching, import from `react-query` v3, not `@tanstack/react-query`.

### State, context, and UI

- Cross-page editor/application state belongs in Zustand stores under `src/frontend/platform/src/store/`.
- Global infrastructure state belongs in contexts under `src/frontend/platform/src/contexts/`; preserve provider ordering in `contexts/index.tsx`.
- Use `bs-ui` components from `@/components/bs-ui/` and icons from `@/components/bs-icons/`.
- Toast pattern:
  ```typescript
  import { toast } from "@/components/bs-ui/toast/use-toast";
  toast({ title, variant: "error", description });
  ```
- Confirm dialog pattern:
  ```typescript
  import { bsConfirm } from "@/components/bs-ui/alertDialog/useConfirm";
  ```

### Platform i18n

- Initialize behavior is in `src/frontend/platform/src/i18n.js`.
- Locale resources are HTTP-loaded from `public/locales/{en-US,zh-Hans,ja}/{namespace}.json` with the package version as cache buster.
- Common namespaces include `bs`, `flow`, `permission`, `orgSync`, `model`, `tool`, `dashboard`, and `knowledge`.
- Use `useTranslation()` / `t()` and add keys for all supported languages. If a namespace must render before lazy loading, ensure it is included in the eager `ns` list.
- Brand interpolation variables come from `window.BRAND_CONFIG`; do not hardcode deploy-specific names when an interpolation variable already exists.

### Platform dev/build/proxy

- `src/frontend/platform/vite.config.mts` uses Vite 5 + SWC, `@/` alias, `build/` output, and port `3001`.
- `VITE_PROXY_TARGET` points API and `/health` to FastAPI or the commercial gateway.
- `VITE_MINIO_PROXY_TARGET` must match the backend MinIO `sharepoint` host for presigned object URLs; host spelling matters.
- Vendor chunks are manually split for PDF, xlsx/document parsing, editors, markdown, and common vendor dependencies.

## Client Workflow

### Route and workspace changes

- Main routes live in `src/frontend/client/src/routes/index.tsx` and use `basename: __APP_ENV__.BASE_URL`, normally `/workspace`.
- Core user paths include `/c/:conversationId?`, `/linsight/:conversationId?`, `/app/:conversationId/:fid/:type`, `/apps`, `/channel`, `/knowledge`, `/share/:token/:vid?`, and `/knowledge/file/:fileId`.
- Keep legacy route redirects, especially old `/chat/:conversationId/:fid/:type` to `/app/...`.
- Menu availability is guarded by `MenuApprovalPluginGate` with plugin ids such as `home`, `apps`, `subscription`, `knowledge_space`, and `linsight_task_mode`.
- Authenticated standalone chat routes and guest standalone chat routes are intentionally separate; do not collapse them unless backend authentication behavior is also designed.

Checklist:

```bash
cd src/frontend/client
npm run check-imports
npm run test:ci
```

For focused Jest tests, run `npx jest path/to/file.test.ts --runInBand` from `src/frontend/client/`.

### API, query, and errors

- Use `~/api/request.ts`; business code must not import `axios` directly.
- `request.ts` exports `get`, `post`, multipart, TTS, response-returning variants, token refresh helpers, and a shared parameter serializer.
- Query hooks use `@tanstack/react-query` v4 under `src/frontend/client/src/hooks/queries/`.
- Client request handling redirects legacy 403s to `/c/new?error=11403` unless `skip403Redirect` is passed, dispatches a service-maintenance event on backend 500 envelopes, handles license-expired toasts, and avoids redirecting guest standalone chat on 401.
- Prefer API/query-layer adaptation over ad hoc component parsing of raw response envelopes.

### State and UI

- Use Recoil atoms/selectors in `src/frontend/client/src/store/`; many exported slices are gathered by `store/index.ts`.
- New state should not use Zustand, React Context, Redux, or another library unless the app already owns that surface.
- Use `~/components/ui/` for shadcn/Radix-style components.
- Use `bisheng-icons` first:
  ```tsx
  import { Outlined } from "bisheng-icons";
  <Outlined.Delete />
  ```
  Use `lucide-react` only when no semantically matching `bisheng-icons` icon exists.
- Client toast pattern:
  ```typescript
  const { showToast } = useToastContext();
  showToast?.({ message, severity: "error" });
  ```

### Client i18n and brand theme

- I18n initialization is in `src/frontend/client/src/locales/i18n.ts`; locale files are bundled from `src/locales/{en,zh-Hans,ja}/translation.json`.
- Use `useLocalize()` and `localize()` from `~/hooks`; new keys use nested namespace-style names inside `translation.json`.
- `window.APP_CONFIG.disableJa` removes/restores Japanese behavior at runtime; avoid assuming Japanese is always selectable.
- Brand theme state is a Recoil atom in `src/frontend/client/src/store/brand.ts`; theme application is done by `src/utils/theme.ts` and `theme-green` on `<html>`.
- Brand-colored UI must use tokenized `blue-*` classes or `rgb(var(--brand-NNN))`; in this app, `blue-*` means brand, not literal blue.
- Primary filled buttons should use the default `<Button>` variant. Hand-rolled `bg-blue-500 text-white` also needs `btn-brand-primary`.
- Use `rgb(var(--illus-NNN))` for themed illustrations. Do not theme semantic colors, type colors, or third-party logos.

### Client dev/build/PWA

- `src/frontend/client/vite.config.ts` uses Vite 6, base `/workspace`, port `4001`, PWA auto-update in production builds, and production console stripping unless the vconsole build is explicitly requested.
- `VITE_DEV_API_TARGET` points `/workspace/api` at FastAPI or gateway.
- `VITE_DEV_MINIO_TARGET` points `/workspace/bisheng` and `/workspace/tmp-dir` at MinIO and must match backend `sharepoint` host for signed URLs.
- Client env variables are loaded from the parent frontend directory via `envDir: '../'`; verify the location before assuming an app-local `.env` is read.

## Review Checklist

- App boundary is explicit; no Platform import from Client or Client import from Platform.
- Request code uses the app wrapper and keeps stores HTTP-free.
- Query imports match the app (`react-query` v3 vs `@tanstack/react-query` v4).
- New components use the app's existing UI/icon system and no new UI/state libraries.
- Routes preserve basename, redirects, and permission/menu-gate semantics.
- I18n keys are added for all supported locales and loaded in the correct namespace/file.
- Client brand-colored UI follows tokenized brand classes/variables; no new hardcoded brand hex values.
- Tests run from the app directory with the app's test runner and providers.
