# Security and Deployment

## Security Model

`markitdown-mcp` is designed for local trusted agents. It does not provide authentication, and the conversion tool runs with the privileges of the process user.

Security implications:

- A reachable MCP client can ask `convert_to_markdown(uri)` to read files the server user can read through `file:` URIs.
- A reachable MCP client can ask the server to fetch network resources through `http:` and `https:` URIs.
- Loopback HTTP/SSE is still reachable by processes and users on the same machine.
- Binding to `0.0.0.0`, a LAN address, or any non-loopback interface can expose file and network access to other machines.
- Enabling plugins expands the code that runs inside the server process and must be treated as additional trusted code.

Default to STDIO or `127.0.0.1`. Do not publish this server as a public unauthenticated service.

## Local Install Pattern

Use the Python environment that the MCP client will actually launch:

```bash
pip install markitdown-mcp
markitdown-mcp
```

For HTTP/SSE-only clients, bind to loopback:

```bash
markitdown-mcp --http --host 127.0.0.1 --port 3001
```

Do not add `--host` or `--port` for STDIO mode.

## Docker Pattern

Use Docker to narrow filesystem exposure and keep the server on STDIO. Use an image that contains `markitdown-mcp` and has `markitdown-mcp` as its entrypoint or command.

Remote-URI-only use does not require a file mount:

```bash
docker run --rm -i markitdown-mcp:latest
```

For local file conversion, mount only the intended directory and prefer read-only mounts:

```bash
docker run --rm -i \
  -v "<absolute-host-directory>:/workdir:ro" \
  markitdown-mcp:latest
```

Inside the container, files must be referenced by their container path, such as `file:///workdir/example.pdf`, not by the host path. If plugins are needed, the image must include the plugin packages and the environment variable must be set deliberately:

```bash
docker run --rm -i \
  -e MARKITDOWN_ENABLE_PLUGINS=true \
  -v "<absolute-host-directory>:/workdir:ro" \
  markitdown-mcp:latest
```

If creating a custom image, run as a non-root user where possible and install only the runtime packages and plugins needed for the user's conversion task.

## Claude Desktop Pattern

Claude Desktop works well with Docker over STDIO. Configure it to run Docker without publishing a network port.

Remote-URI-only configuration:

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "markitdown-mcp:latest"
      ]
    }
  }
}
```

Configuration with a constrained read-only file mount:

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "<absolute-host-directory>:/workdir:ro",
        "markitdown-mcp:latest"
      ]
    }
  }
}
```

When asking Claude Desktop to convert local files through this Docker server, use container-visible URIs such as `file:///workdir/report.docx`. Restart Claude Desktop after changing its MCP configuration.

To enable plugins in the Docker-launched server, add both the environment variable and an image that actually contains the plugin packages:

```json
{
  "mcpServers": {
    "markitdown": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "MARKITDOWN_ENABLE_PLUGINS=true",
        "-v",
        "<absolute-host-directory>:/workdir:ro",
        "markitdown-mcp:latest"
      ]
    }
  }
}
```

## Non-Localhost Requests

If a user starts or proposes `markitdown-mcp --http --host 0.0.0.0`, treat it as a security exception:

1. Explain that the server has no authentication and can read files and fetch network resources as the server user.
2. Recommend STDIO, Docker STDIO, or loopback HTTP/SSE instead.
3. If non-localhost binding is still required, require deliberate sandboxing such as a container or VM with minimal files, minimal network reachability, and no sensitive credentials.
4. Do not design an authentication gateway in this sub-skill; route that work to the user's infrastructure/security process.

Plugins make non-localhost exposure riskier because plugin code runs in the same privileged process. Enable plugins only in a constrained environment and route plugin setup details to `../../plugin-development/SKILL.md` or OCR-specific setup to `../../ocr-plugin/SKILL.md`.
