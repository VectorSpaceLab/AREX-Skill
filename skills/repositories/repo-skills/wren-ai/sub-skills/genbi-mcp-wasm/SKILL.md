---
name: genbi-mcp-wasm
description: "Guide Wren GenBI applications, MCP server setup, browser-side
  wren-core-wasm APIs, static app verification, and safe Vercel or Cloudflare
  deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# GenBI, MCP, and WASM

Use this sub-skill to expose a prepared Wren project to an agent client, build a
browser-side analytics application, or run Wren's browser engine directly.

## GenBI Workflow

1. Confirm a project and its MDL exist. `wren genbi build` can compile a missing
   target only when source project files are valid.
2. Choose data mode:
   - `snapshot`: bundle small Parquet/DuckDB assets and query in the browser.
   - `live`: call a user-owned endpoint at view time; never ship credentials.
3. Request a project-aware build instruction:
   ```bash
   wren genbi build sales-overview --prompt "Revenue by month" --data-mode snapshot
   ```
4. Write the app only under the generated app directory, copy `mdl.json`, and
   include the required data asset for snapshot mode.
5. Register and verify before preview or deployment:
   ```bash
   wren genbi register sales-overview --data-mode snapshot
   wren genbi verify sales-overview
   wren genbi open sales-overview
   ```
6. Deploy only when asked, and confirm before `--prod`:
   ```bash
   wren genbi deploy sales-overview --provider vercel
   ```

## MCP Workflow

Install the extra and build the project first:

```bash
pip install "wrenai[mcp]"
wren context build
wren serve mcp
```

Use stdio when an MCP client launches `wren` itself. Use local Streamable HTTP
when a local client connects to a service:

```bash
wren serve mcp --transport http --host 127.0.0.1 --port 8080
```

Use `--no-connect` for planning/schema/knowledge tools without database query
tools. Use `--allow-write` only when the client should be able to store a query
pair.

## WASM Workflow

Use `@wrenai/wren-core-wasm` for browser-side semantic queries over static or
registered data. Register local data before `loadMDL` in local mode, then use
`query()` or `cubeQuery()`. It is not the server-side connector runtime and has
no semantic-memory module.

## References and Helper

- Read `references/genbi-workflows.md` for data modes, verification, and deploy
  decisions.
- Read `references/mcp-server.md` for flags, tools, resources, and security.
- Read `references/wasm-sdk.md` for TypeScript API and browser constraints.
- Read `references/troubleshooting.md` for secret, target, provider, MCP, and
  WASM failures.
- Run `scripts/check_genbi_app.py --app <directory> --data-mode snapshot` before
  deployment. It is a static check only.

## Guardrails

- A static app must not ship `.env` files, DB passwords, provider tokens, or
  connection strings. Treat the built-in verifier as defense in depth, not a
  replacement for safe design.
- A successful provider response does not guarantee the deployed URL is publicly
  viewable. Check the returned page; Vercel protection can produce 401/403.
- The MCP HTTP transport is local by default and has no bearer-token layer in
  this workflow. Do not expose it broadly without an external security design.
