# UI Contracts and Icons

## Frontend/Backend Contract Touchpoints

The frontend does not invent component semantics; it renders and edits metadata returned by the backend. Treat the following as contract surfaces:

- Component metadata and templates consumed by `typesStore` and custom nodes.
- Flow JSON serialized as React Flow nodes, edges, and viewport data.
- Build/run status, vertex order, validation results, and event delivery types consumed by `flowStore` and node status UI.
- Auth, store, project, flow, variable, file, and API-key endpoints accessed through controllers and React Query hooks.
- Runtime configuration returned by backend config endpoints and compiled frontend environment flags.

When changing a contract, update the full chain:

1. Backend route/schema or component metadata owner in the sibling backend/component sub-skill.
2. TypeScript API model or local type alias.
3. Controller function and query/mutation hook.
4. Store action or UI component consumer.
5. Focused Jest test and, for workspace behavior, a Playwright candidate.

## Component Names and Flow Compatibility

Backend component class names are durable identifiers used to match saved flows and surface update prompts. Do not rename a backend component class to satisfy a frontend display change. Use display metadata, icon metadata, UI labels, or frontend mapping changes instead.

If a component appears stale after backend changes:

- Confirm whether the backend was started with dynamic component loading during development.
- If dynamic loading is not enabled, rebuild or refresh the backend component index through component-development guidance.
- Refresh the browser after backend restart or index rebuild.
- Check whether the node reports update availability, breaking change, user-edited code, or blocked update status before forcing a template replacement.

## Icons

Langflow uses both Lucide icons and custom icons:

- Lucide names are checked through `lucide-react/dynamicIconImports`.
- Category icons can also be accepted through frontend style utilities.
- Custom provider/product icons live under the frontend `icons` tree and are exposed by import maps.
- Lazy icon imports are used for most custom icons to keep the initial bundle smaller.
- Some icons support dark mode through an `isDark` prop or use `currentColor`; keep dark/light behavior visible when adapting SVGs.

When adding a new custom icon:

1. Create a dedicated icon directory and an `index.tsx` export that follows existing `forwardRef` patterns.
2. Keep the exported component name stable and descriptive, usually ending with `Icon`.
3. Add SVG/JSX assets under the same icon directory; avoid remote image dependencies.
4. Add an entry to the lazy icon import map using the exact icon key that backend component metadata will provide.
5. Add an eager import only when the existing UI path requires immediate availability.
6. Update or add tests for the UI path that resolves the icon, especially if the icon is referenced by component metadata.
7. Verify the icon in light and dark UI modes when the graphic sets explicit fill colors.

If the icon key is coming from a backend component, coordinate with component-development so the backend `icon` string matches the frontend lazy import key or a valid Lucide/category icon name.

## Generic Icon Resolution

The generic icon component accepts icon names used across nodes, palette cards, controls, and status UI. Resolution failures usually display a fallback, a blank icon, or a console/import error. To debug:

- Check exact spelling and casing of the icon key.
- Check whether the key is a Lucide dynamic import, a category icon, or a custom lazy import.
- Check whether the custom icon module exports the name used by the lazy import callback.
- Check whether path aliases resolve through Vite and Jest module mapping.
- Check whether JSX/SVG syntax compiles under the Vite React SWC setup.

## UI Controls and Graph Actions

Before adding a new graph control, identify the ownership layer:

- Pure presentation belongs in shared UI components or a graph-specific component.
- Canvas/node operations belong near existing React Flow utilities or `flowStore` actions.
- Backend mutations belong in controller/query hooks.
- Keyboard shortcuts belong in the shortcuts store and should not be hard-coded in one component if a global shortcut already exists.
- Node code/template updates should use existing validation and pending-update helpers so runs do not race with in-flight updates.

For a new icon/control in the graph workspace, a safe change usually includes:

1. A small UI component or existing UI primitive update.
2. Store action or controller hook update only if behavior changes state or calls the backend.
3. Lazy icon mapping when a custom icon is required.
4. Jest coverage for store/controller/util behavior.
5. A Playwright candidate for canvas-visible behavior, deferred if browser dependencies are not available.

## API Error and Auth UI Contracts

The Axios interceptor is part of the UI contract. Be careful when changing auth or error behavior:

- Do not make refresh/login/logout/auto-login failures recursively trigger another refresh.
- Preserve rejection of non-recoverable API errors so React Query and callers can show failures instead of hanging spinners.
- Preserve external-domain exclusions for headers; custom headers should not leak to public GitHub, analytics, or other explicitly external URLs.
- Preserve build-state cleanup after failed build/run requests so nodes do not remain stuck as running.
- Keep same-origin and proxied API behavior clear when adding a new endpoint.

## Validation Matrix for Contract Changes

Use this matrix to pick checks:

| Change type | Minimum check | Stronger check |
| --- | --- | --- |
| Store-only state update | Focused store Jest test | Full `npm test` |
| Controller/API hook update | Mocked controller/query Jest test | `npm run type-check` plus backend route test by backend owner |
| Graph node rendering change | Component/helper Jest test | Playwright graph workspace candidate |
| Custom icon addition | Import/lazy resolution test or build | Visual browser check in light/dark mode |
| Vite/env/proxy change | Static config review and `npm run build` | Dev server with backend health check |
| Backend component metadata change | Component-development validation plus browser refresh | Playwright palette/node regression |
