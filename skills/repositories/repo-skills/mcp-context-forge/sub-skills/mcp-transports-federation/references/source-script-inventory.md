# Source Script Inventory

| Source script | Decision | Reason |
|---|---|---|
| `scripts/test_mcp_client.py` | adapt | Good seed for a read-only transport smoke, but it was hard-coded and created a token inline. The bundled replacement in this skill accepts command-line inputs and avoids resource creation. |
| `mcp-servers/scaffold-python-server.sh` | reference-only | It scaffolds a new server from templates and writes files on disk. Useful as a reference for server starter workflows, but not safe or relevant for transport operation. |
| `mcp-servers/scaffold-go-server.sh` | reference-only | Same reason as the Python scaffold: it creates a new project from templates instead of operating an existing gateway. |

## Bundled replacement

- `scripts/contextforge_mcp_smoke.py` is the safe, read-only helper for this sub-skill.
- It requires a base URL, accepts a token, server id, and transport endpoint path, and defaults to health-only checks.
