# Troubleshooting

## `markitdown-mcp` Is Not Found

- Install `markitdown-mcp` in the Python environment that the MCP client launches.
- For Claude Desktop with Docker, ensure the Docker image contains the package and that Docker is available to the desktop app.
- Run `python scripts/check_mcp_cli.py --transport stdio` from this sub-skill directory to verify command discovery and help text without starting the server.

## `--host` or `--port` Fails in STDIO Mode

`--host` and `--port` are only valid with `--http` or `--sse`. These are invalid because STDIO mode does not bind a socket:

```bash
markitdown-mcp --host 127.0.0.1
markitdown-mcp --port 3001
```

Use one of these instead:

```bash
markitdown-mcp
markitdown-mcp --http --host 127.0.0.1 --port 3001
```

## Non-Localhost Warning Appears

The CLI warns when an explicit host is not `127.0.0.1` or `localhost`. This is expected for hosts such as `0.0.0.0` or a LAN address.

Respond by:

- Switching back to STDIO or loopback HTTP/SSE when possible.
- Avoiding Docker `-p` port publication unless the user has explicitly accepted the risk.
- Running in a sandbox with minimal mounts and no sensitive credentials if non-localhost binding is unavoidable.
- Treating plugin-enabled non-localhost servers as higher risk because plugin code runs in the server process.

## Local Files Cannot Be Read

`convert_to_markdown(uri)` can read only files visible to the server process.

- Local process: use a valid absolute `file:` URI for a file readable by the process user.
- Docker: mount the host directory and use the container path in the URI, such as `file:///workdir/example.pdf`.
- Read-only Docker mounts are usually sufficient for conversion and reduce accidental modification risk.
- If the container runs as a non-root user, ensure file permissions allow reads from the mounted directory.

## Plugins Do Not Load

Check all of these conditions:

- `MARKITDOWN_ENABLE_PLUGINS` is set to `true`, `1`, or `yes` in the server process environment.
- The plugin package is installed in the same environment or Docker image as `markitdown-mcp`.
- The MCP client was restarted after changing environment variables or Docker args.
- For Docker, `-e MARKITDOWN_ENABLE_PLUGINS=true` is present before the image name.

Route plugin discovery and custom plugin setup to `../../plugin-development/SKILL.md`; route OCR plugin usage to `../../ocr-plugin/SKILL.md`.

## MCP Inspector Cannot Connect

Choose the Inspector transport that matches how the server is started:

- STDIO: do not start a separate server; choose `STDIO` and command `markitdown-mcp`.
- Streamable HTTP: start `markitdown-mcp --http --host 127.0.0.1 --port 3001`, then connect to `http://127.0.0.1:3001/mcp`.
- SSE: start `markitdown-mcp --http --host 127.0.0.1 --port 3001`, then connect to `http://127.0.0.1:3001/sse`.

If HTTP/SSE still fails, check that the chosen port is free, the server process is still running, and the client is using the same host and port.

## URI Conversion Fails

The MCP tool accepts `http:`, `https:`, `file:`, and `data:` URIs. If the URI is valid but conversion fails, route detailed diagnosis to `../../core-conversion/SKILL.md` for converter coverage, missing optional dependencies, unsupported formats, and conversion exceptions.
