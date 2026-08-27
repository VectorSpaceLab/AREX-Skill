# GenBI, MCP, and WASM Troubleshooting

## GenBI verification fails

Read the failure literally. Common causes are missing `index.html`, invalid or
empty `mdl.json`, missing snapshot data asset, or a possible credential in a
static file. Fix the app directory and rerun `wren genbi verify`; do not deploy
on a failed preflight.

## Deployment token or provider command is missing

Set `VERCEL_TOKEN` for Vercel. For Cloudflare, set `CLOUDFLARE_API_TOKEN` and
`CLOUDFLARE_ACCOUNT_ID`, then make `wrangler` or `npx` available. Keep values in
the environment or project environment file, never in command arguments.

## Deployed app returns 401 or 403

A Vercel preview/production URL can be protected by deployment authentication.
The provider deployment succeeded, but anonymous sharing is disabled. Confirm
the desired protection policy in the provider account before promising a public
link.

## MCP cannot start

Install `wrenai[mcp]`, build `target/mdl.json`, and check project discovery.
For a schema-only service, use `--no-connect`; otherwise fix profile/secret
resolution before starting the server.

## MCP may be serving stale context

The server warns if project source is newer than the target. Stop/rebuild/restart
rather than assuming a running server has automatically loaded new models.

## WASM `Unresolved models` error

In local/strict mode, register every physical table before `loadMDL`. In URL
mode, verify remote Parquet names and source prefix. If data is too large,
switch from inline registration to remote Parquet rather than increasing browser
memory use.
