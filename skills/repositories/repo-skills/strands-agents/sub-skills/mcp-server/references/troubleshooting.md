# MCP Server Troubleshooting

Use this guide for package/server issues. If the problem is an MCP client implementation issue in the Python SDK or a docs-site content/sourceLinks issue, route out of this sub-skill.

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `{"error": "only https://strandsagents.com URLs allowed", ...}` | The requested URL is not HTTPS on exactly `strandsagents.com`. Subdomains, userinfo tricks, other schemes, and other hosts are rejected. | Use the canonical `https://strandsagents.com/...` URL returned by `search_docs` or catalog mode. Do not loosen the host check unless the security model is intentionally redesigned. |
| `{"error": "fetch failed", "url": ...}` | The URL passed validation, but the fetch/clean step failed because of network, timeout, unavailable page, or transient service issue. | Retry when network is available; verify the URL came from the catalog; keep this in live integration coverage rather than offline unit checks. |
| `{"error": "section '<id>' not found", ...}` | The section ID is not in the current document's TOC, is from another page, is malformed, or is deeper than the supported dotted child level. | Call `fetch_doc(uri="...")` without a section, then choose an ID from the returned `sections`/`children`. For deeper content, fetch the nearest returned child section and inspect it manually. |
| Search returns only title matches or body terms are missing after startup. | The catalog loaded titles from `llms.txt`, but the relevant page has not been hydrated yet. Background prefetch is asynchronous and best-effort. | Call `fetch_doc` on the relevant URL, run `search_docs` again after snippet hydration, or enable `STRANDS_MCP_PREFETCH_ALL=1` and wait for hydration to finish. |
| Search snippets are just the title. | The page is not cached, content is empty, or the snippet fetch failed. | Treat this as non-fatal if URL/title/score are present. Fetch the document directly to hydrate it or investigate live network failures if snippets remain absent. |
| Background prefetch ran but body-only search still fails. | All page fetches may have failed, or the search happened before hydration completed. | Check logs for the background prefetch summary; rerun after the daemon has time to hydrate; fall back to explicit `fetch_doc` for the target URL. |
| Live docs integration tests fail, hang, or are not allowed in the environment. | `tests_integ` reaches public documentation URLs and depends on live network access. | Skip intentionally with `SKIP_INTEG_TESTS=1` when network access is unavailable or out of scope. Do not use skipped live tests as proof that live fetching works. |
| Console help or import emits a `pydantic_settings` `IncompleteFieldDefinitionWarning`. | A dependency warning can appear even when the server import and `strands-agents-mcp-server --help` succeed. | Treat it as non-fatal when the process exits 0 and `search_docs`/`fetch_doc` signatures import correctly. Escalate only if it becomes an import failure or startup exit failure. |
| `strands_mcp_server` cannot be imported. | The active environment does not have the package installed, or dependency resolution pulled an incompatible `mcp` major. | Install the package into the active environment and check that `mcp` resolves within the declared `<2.0.0` major bound. Then rerun the smoke script. |
| Offline unit tests unexpectedly reach the network. | The test selection may have included live integration tests or an unmocked fetch path. | Use the bundled unit-check script or explicitly select the offline server, indexer, cache, text-processor, and dependency tests. Keep live fetch tests under integration-only execution. |

## Safe triage order

1. Run [../scripts/mcp-smoke.sh](../scripts/mcp-smoke.sh) in an environment where the package should import.
2. If editing the package, run [../scripts/mcp-unit-check.sh](../scripts/mcp-unit-check.sh) from a checkout with test dependencies.
3. Use live integration tests only after confirming network access and deciding that live docs behavior is in scope.
