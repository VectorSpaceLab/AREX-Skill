# Routes And Runtime

This file maps the frontend route tree and the configuration / build behavior that shapes it.

## Runtime Config

`frontend/src/config.js` resolves values in this order:

1. `window.RUNTIME_CONFIG` at runtime.
2. `import.meta.env.VITE_*` at build / dev time.
3. A small default fallback.

The runtime config generator in `frontend/generate-runtime-config.sh` writes a `window.RUNTIME_CONFIG` object with values such as:

- `faviconPath`
- `logoUrl`
- `enablePosthog`
- `version`

`frontend/vite.config.js` loads `VITE_BACKEND_URL` for the dev proxy and uses `VITE_*` variables in development.

## Route Tree Overview

### Public and shell routes

- `/landing` for the public landing page.
- `/simple-prompt-studio/*` for the simple prompt-studio flow.
- `/promptStudio/share/:id` and `/promptStudio/share/:id/outputAnalyzer` for public prompt sharing.
- `/setOrg`, `/selectProduct`, `/subscription-expired`, `/payment/success`, `/marketplace-landing`, and similar shell-level routes for onboarding and plugin pages.

### Authenticated app routes

The main authenticated tree is mounted under `:orgName` and includes:

- dashboard and profile pages,
- API, ETL, task, app, workflow, tools, logs, and settings pages,
- admin-only user / group / API-key pages,
- prompt-studio review and manual-review routes,
- platform settings and triad pages.

## Route Composition Notes

- `Router.jsx` owns the outer `Suspense` / error-boundary shell.
- `useMainAppRoutes.js` constructs the authenticated route subtree.
- Heavy pages are code-split so unauthenticated users do not download the whole app shell up front.
- Optional plugin routes degrade to `NotFound` / empty modules when the plugin package is absent, which is intentional.

## Build / Dev Notes

- Vite is configured for React, SVG-as-component imports, code splitting, and a proxy for `/api` requests.
- The dev server uses `0.0.0.0` and a configurable `PORT` so the app can run inside containerized environments.
- The proxy forwards websocket upgrades so Socket.IO log streaming continues to work in development.

## When To Read This File

Read this file when a task involves:

- changing or diagnosing a frontend route,
- changing the runtime config generator,
- debugging the dev proxy or build,
- or understanding why a page chunk loads the way it does.
