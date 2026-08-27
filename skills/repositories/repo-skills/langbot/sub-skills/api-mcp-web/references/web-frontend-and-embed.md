# Web Frontend and Page Bot Embed

## Frontend Stack

The `web/` app is Vite + React Router 7 + shadcn/ui + Tailwind. It is not
Next.js despite some historical filenames.

Common commands:

```bash
cd web
pnpm install
pnpm dev
pnpm build
pnpm lint
pnpm test:e2e
```

In development, set the API base URL so the browser talks to the backend. In
production/package mode, the backend serves built frontend assets with SPA
fallback.

## API Alignment

When backend response shapes or permissions change, update frontend callers,
forms, validation, i18n strings, and tests in the same pass. User-facing strings
should follow the repo's i18n convention; include `en_US` and `zh_Hans`, plus
`ja_JP` when nearby code already includes it.

## Page Bot Embed Contract

The Page Bot adapter exposes a browser widget script shaped like:

```html
<script data-title="Widget title" src="<langbot-base>/api/v1/embed/<bot_uuid>/widget.js"></script>
```

The browser must reach the LangBot base URL. A bot UUID comes from a Page Bot
created and bound to a working pipeline. The widget uses the bot config for
language/title/icon and optional Turnstile behavior.

## Frontend Verification

- Use `pnpm lint` after most frontend code changes.
- Use Playwright e2e when user paths, routing, login/session behavior, or mock
  API contracts change.
- Backend-only route changes still need frontend checks if the UI consumes the
  changed endpoint.
