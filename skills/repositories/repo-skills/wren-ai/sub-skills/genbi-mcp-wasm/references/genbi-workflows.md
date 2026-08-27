# GenBI Application Workflow

## When to read

Read this before creating a Wren-powered static analytics app or deploying it to
a provider.

## Data mode decision

| Mode | Use when | Requirements |
| --- | --- | --- |
| `snapshot` | Demo, report, small dataset, or dlt-produced local data | Bundle one or more `.parquet` or `.duckdb` assets; browser executes queries |
| `live` | Large or changing data | Endpoint-only connection design, CORS configuration, no shipped credentials |

Snapshot data should contain only the rows/columns the dashboard needs. It is
not a full warehouse-export pattern.

## Build, author, verify

```bash
wren genbi build sales-overview \
  --prompt "Show revenue trend and top customers" \
  --data-mode snapshot

# Author the application under the target app directory from the instruction.
wren genbi register sales-overview --data-mode snapshot
wren genbi verify sales-overview
wren genbi open sales-overview
```

The build command prints the authoritative instruction: model inventory,
pinned browser-engine version, target folder, data-mode constraints, and
acceptance criteria. Do not hand-edit the machine-maintained app index; use
`register`/`remove`.

## Static preflight contract

A snapshot app needs an `index.html`, a nonempty parseable `mdl.json`, and at
least one `.parquet` or `.duckdb` asset. Both modes must avoid inline secrets.
Run `wren genbi verify` until it passes before deployment.

## Deployment

```bash
wren genbi deploy sales-overview --provider vercel
wren genbi deploy sales-overview --provider cloudflare
```

- Vercel resolves `VERCEL_TOKEN` from environment or environment files and uses
  its API. Never add a token argument.
- Cloudflare needs `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, and either
  `wrangler` or `npx` available. Its token needs Pages edit capability.
- Deploys default to preview. Confirm an explicit production deploy.

## Verify the actual URL

A Vercel deployment can succeed while Vercel Authentication protects the URL
with 401/403 for logged-out viewers. Confirm the page is reachable before
calling it shareable; the user may need to change deployment-protection policy.
