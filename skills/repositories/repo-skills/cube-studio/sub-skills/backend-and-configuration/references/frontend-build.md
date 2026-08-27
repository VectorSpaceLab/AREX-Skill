# Frontend build and proxy customization

CubeStudio has three frontend packages. This reference covers build/proxy
plumbing only; UI semantics for pipelines, data, notebooks, serving, or AIHub
belong to their sibling sub-skills.

## Frontend package map

| Directory | Role | Package name | Main scripts |
| --- | --- | --- | --- |
| `myapp/frontend` | Main CubeStudio SPA under `/frontend/` plus FAB-adjacent assets | `kubeflow-frontend` | `start`, `build`, `buildSelf`, `buildFab`, `test` |
| `myapp/vision` | AI pipeline flow editor | `vite-ml-platform` | `dev`, `build`, `test`, `prettier` |
| `myapp/visionPlus` | Data ETL pipeline flow editor | `vite-ml-platform` | `dev`, `build`, `test`, `prettier` |

Observed scripts:

```text
myapp/frontend:
  start     cross-env NODE_OPTIONS=--max-old-space-size=8192 node scripts/start.js
  build     npm run buildSelf
  buildSelf cross-env TSC_COMPILE_ON_ERROR=true APP_ENV=frontend NODE_OPTIONS=--max-old-space-size=8192 node scripts/build.js
  buildFab  cross-env TSC_COMPILE_ON_ERROR=true APP_ENV=fab NODE_OPTIONS=--max-old-space-size=8192 node scripts/build.js
  test      node scripts/test.js

myapp/vision and myapp/visionPlus:
  dev       react-app-rewired start
  build     TSC_COMPILE_ON_ERROR=true react-app-rewired build
  test      react-app-rewired test
  prettier  prettier --write '**/*.{tsx,ts,less}'
```

The Docker README states the development expectation as Node 16.15.0+ and npm
6.14.8+, with yarn recommended for package management. Do not run `npm install`,
`yarn`, or builds unless the user explicitly permits network/package work.

## Entrypoint build mode

When `STAGE=build`, the runtime entrypoint runs these commands inside the
backend image:

```bash
cd /home/myapp/myapp/frontend && npm install --force && npm run build
cd /home/myapp/myapp/vision && npm install && npm run build
cd /home/myapp/myapp/visionPlus && yarn && npm run build
```

The Docker README documents output under `myapp/static/appbuilder`. The separate
frontend container copies built static assets into `/data/web/frontend` and
serves `/frontend/` through nginx. Backend Jinja manifest loading in
`myapp/__init__.py` uses `myapp/assets/dist/manifest.json` for its own asset
manifest helpers; do not confuse that with the SPA output directory.

## Local frontend development proxy

Each frontend package has `src/setupProxy.js` using `http-proxy-middleware`.
Default target is `http://localhost`. Change only the `target` to point to the
running backend service and restart the frontend dev server.

Proxy behavior distilled from the checked-in files:

- `myapp/frontend/src/setupProxy.js`
  - redirects `/frontend` to `/frontend/`;
  - proxies `/workflow_modelview`;
  - proxies `**/api/**`, `/myapp`, `/login`, `/idex`, `/users`, `/roles`,
    `/static/assets`, `/static/appbuilder`, `/pipeline_modelview`, and
    `/project_modelview`.
- `myapp/vision/src/setupProxy.js`
  - proxies `**/api/**`, `/myapp`, `/login`, `/idex`, `/users`, `/roles`,
    `/static/assets`, and `/static/appbuilder`.
- `myapp/visionPlus/src/setupProxy.js`
  - same proxy pattern as `myapp/vision`.

Local dev entry points documented by the Docker README:

- Main frontend: after login bootstrap,
  `http://localhost:3000/frontend/`.
- Vision editor: `http://localhost:3000/#/home/` or
  `http://localhost:3000/?pipeline_id=1#/`.
- VisionPlus editor: `http://localhost:3000/?scenes=etl_pipeline&pipeline_id=1`.

## Backend/frontend route coupling

- Backend model/API routes are registered by AppBuilder during `myapp.views`
  import.
- Shared UI routes are mapped by `MODEL_URLS` in the runtime config overlay.
  For example, backend model names such as `pipeline`, `job_template`,
  `notebook`, `service`, `inferenceservice`, `dataset`, and `sqllab` map to
  paths below `/frontend/...`.
- If a backend API exists but the UI cannot navigate to it, inspect both the
  AppBuilder registration and the overlay `MODEL_URLS` entry.
- If the frontend dev server works but API requests hit the wrong host, inspect
  `setupProxy.js` in the package being run; all three packages have their own
  proxy file.

## Safe checks

Use static checks before any install/build:

```bash
python scripts/inspect_cube_studio_structure.py /path/to/cube-studio --json
```

This parses package JSON and proxy files without running Node. It reports
scripts, proxy targets, and package JSON parse errors.

## Common frontend build/proxy fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `/frontend` redirects or 404s inconsistently | Missing trailing slash or nginx/SPAs not serving `/frontend/` | Keep the main frontend redirect from `/frontend` to `/frontend/`; check frontend container nginx when deployed. |
| Browser login succeeds but API calls 404 | Wrong `setupProxy.js` target or backend not running on expected host | Update the target in the exact frontend package being run, then restart dev server. |
| API returns 401 in local frontend dev | Login cookie/header not established, cookie domain mismatch, or backend auth rejects unauthenticated paths | Visit the documented login bootstrap URL, check `COOKIE_DOMAIN`, and confirm backend `check_login` exemptions. |
| `npm run build` runs out of memory | Main frontend already sets `NODE_OPTIONS=--max-old-space-size=8192`; local shell may override or lack memory | Preserve the script's `NODE_OPTIONS` and build in the documented container when local Node differs. |
| Install/build resolution prompts or registry timeouts | Network/registry dependency resolution | Only proceed with user approval; the Docker README suggests mirror configuration for npm/yarn in constrained environments. |
| Windows `visionPlus` lint linebreak error | ESLint `linebreak-style` expects Unix | Follow the README note to switch the relevant `.eslintrc` rule for Windows or normalize line endings. |
