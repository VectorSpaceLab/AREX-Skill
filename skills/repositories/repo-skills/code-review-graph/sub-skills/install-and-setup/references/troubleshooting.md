# Install and Setup Troubleshooting

## `code-review-graph: command not found`

**Symptoms**
- `pip install code-review-graph` succeeds, but the command is unavailable.
- `python -m code_review_graph --help` works.

**Likely causes**
- The user install `bin/` directory is not on PATH.
- The package was installed into a different environment than the shell is using.

**Recovery**
1. Prefer `pipx install code-review-graph` or `uvx code-review-graph ...` for isolated CLI usage.
2. If using a virtual environment, run the CLI from that environment or reinstall from inside it.
3. If the package imports but the command is missing, use `python -m code_review_graph --help` as a temporary fallback.

## `install` wrote stale or broken client config

**Symptoms**
- MCP client does not list CRG in a new session.
- The client starts but the server cannot find the graph.
- A previous virtual environment path is still embedded in config.

**Likely causes**
- `install` ran before the final environment was chosen.
- The editor/client was not restarted after the config changed.
- The repo root opened in the client is not the same repo root used for install/build.

**Recovery**
1. Re-run `code-review-graph install` from the repository root.
2. Re-run `code-review-graph build` if the database is missing or stale.
3. Restart the client/editor completely.
4. Verify the open folder is the same repository root.

## `status` says no graph found

**Symptoms**
- `code-review-graph status` exits non-zero and reports that no graph exists.

**Likely causes**
- `build` has not been run yet.
- A different repo root or `CRG_DATA_DIR` is being checked.
- The graph was deleted or not written successfully.

**Recovery**
1. Run `code-review-graph build`.
2. If the repo has moved or the database is stale, run `build` again from the current root.
3. Check whether an external `CRG_DATA_DIR` is intentionally set.

## HTTP serve rejected by the Host/Origin guard

**Symptoms**
- `code-review-graph serve --http` returns 403 for browser requests or startup failures mention middleware/host handling.

**Likely causes**
- The request used a foreign Origin or a rebinding-style Host header.
- The client is not talking to the loopback host/port that CRG bound.

**Recovery**
1. Bind to `127.0.0.1` or `localhost` only.
2. Use the same host/port in the client Origin/URL.
3. For non-browser MCP clients, send no Origin header.

## `install` can’t reach PyPI while fetching build dependencies

**Symptoms**
- Editable install fails while resolving build-time dependencies.
- The failure mentions TLS, PyPI, or `hatchling` download problems.

**Likely causes**
- The terminal’s Python cannot reach `pypi.org`.
- A corporate proxy, VPN, or IDE terminal is interfering with HTTPS.

**Recovery**
1. Run the bundled `scripts/diagnose_pypi_connectivity.py` helper.
2. Re-run the install from a terminal with working HTTPS access.
3. If `uv` is available, use a `uvx`-based install path.

## When to stop

Stop and ask for help when the issue requires:
- a different Python version than the repo supports,
- a network policy change,
- a new client/editor installation,
- or a repo-root decision that the user has not clarified.