# Web UI development

This reference covers the maintainer workflow for the `webui/` frontend and the backend integration points that affect it.

All commands assume the **target gptme checkout**. The backend commands run from the checkout root; the frontend commands run from `webui/`.

## Local development setup

Start the backend and frontend in separate terminals:

```bash
# Terminal 1 — backend, from the checkout root
uv pip install -e "[server]"
uv run gptme-server --cors-origin='http://localhost:5701'

# Terminal 2 — frontend
cd webui
npm ci
npm run dev
```

Notes:

- The backend defaults to port `5700`.
- The frontend dev server is typically available on `5701` in this setup.
- If you are iterating locally and intentionally want to refresh dependencies, `npm i` is acceptable, but `npm ci` is the reproducible CI-style path.

## Web UI command set

Run these from `webui/`:

```bash
npm test           # Jest unit tests
npm run typecheck   # TypeScript type check
npm run lint        # ESLint + typecheck
npm run build       # production build used for bundling
npm run test:e2e    # Playwright E2E
npm run test:e2e:ui # Playwright with the interactive UI
```

For quick visual debugging, a Playwright test or script can open a specific conversation URL and take a screenshot:

```ts
await page.goto('http://localhost:5701/chat/<conversation-id>?server=<server-id>');
await page.screenshot({ path: 'screenshot.png', fullPage: true });
```

## Bundling and packaging flow

When the built frontend needs to ship with the Python package:

1. Build the frontend: `cd webui && npm run build`
2. Bundle it into the Python package tree: `make bundle-webui`
3. Build the package: `poetry build`
4. Validate the archive: `make validate-release-package` from the checkout, or run the bundled repo-development checker against the target checkout's built `dist/*.whl` and `dist/*.tar.gz` artifacts.

`make bundle-webui` copies `webui/dist/` into `gptme/server/webui-dist/`, which is what the server and release artifacts expect.

## Rendering and state gotchas

The UI has a few maintenance traps that commonly cause regressions:

- There are **two markdown rendering paths**:
  - streaming path: `ChatMessage.tsx` → `markdownRenderer.ts`
  - non-streaming path: `parseMarkdownContent()` in `markdownUtils.ts`

  If you add preprocessing or transformation logic, update both paths.

- The project uses a nested code-block convention:
  - `````lang`` opens a block
  - a bare ````` closes it

  The parsers do not understand that convention by themselves; `processNestedCodeBlocks()` widens the fences before parsing.

- Legend state / `<For>` rerendering:
  - `<For>` only re-renders on observable changes.
  - React `useState` is invisible inside `<For>` callbacks.
  - Use `useObservable` when the rendered value must react to updates.

- `ChatInput` stays mounted across conversation switches.
  - `useState` initializers do not re-run on switch.
  - Draft persistence uses `localStorage` keys of the form `gptme-draft-{conversationId}`.

- Server ↔ Web UI data flow must stay aligned:
  - `LogManager.to_dict()` and `Message.to_dict()` feed GET responses.
  - `msg2dict()` feeds SSE responses.
  - `onMessageComplete` must update metadata and timestamps from the final event.

## Practical maintainer rule

If a backend change affects message shape, metadata, conversation routing, or streaming events, run both:

- the relevant Python server tests, and
- the focused Web UI unit tests for the affected components/hooks/utils.

If a change only touches CSS or static layout, a narrower `npm test` selection may be enough, but keep the render-path split in mind.
