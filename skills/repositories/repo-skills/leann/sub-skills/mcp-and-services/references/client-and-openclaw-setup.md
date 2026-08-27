# Client and OpenClaw setup

## Preflight

Use one installation context consistently: `leann_mcp` launches the LEANN CLI
with its own Python interpreter. Confirm both entry points are present before
editing a client configuration:

```bash
command -v leann_mcp
command -v leann
leann_mcp --help
```

A documented isolated install is:

```bash
uv tool install leann-core --with leann
```

If the entry point is unavailable but the selected Python contains
`leann-core`, use `python -m leann.mcp`. Installation/backend details belong to
the root installation guidance.

Create or identify the project index before testing search:

```bash
cd /path/to/project
leann list
leann build project-docs --docs ./docs ./src
```

The path above is illustrative. Do not copy a private path into a shared config
or bug report.

## Claude Code

The repository-documented registration commands are:

```bash
# User scope: available to Claude Code in every project
claude mcp add --scope user leann-server -- leann_mcp

# Local/default scope: register from the current project
claude mcp add leann-server -- leann_mcp

claude mcp list | cat
```

Remove the registration with:

```bash
claude mcp remove leann-server
```

Prefer local scope when each project owns a different `.leann/indexes` tree.
A user-scoped server still inherits a working directory chosen by the client;
verify that directory with `leann_status` before trusting search results.

For clients that consume an MCP JSON file, use the same stdio entry:

```json
{
  "mcpServers": {
    "leann-server": {
      "command": "leann_mcp",
      "args": [],
      "env": {}
    }
  }
}
```

Merge the `mcpServers` member into existing configuration rather than replacing
other servers. Keep command and args separate; never construct one shell string.

## Claude Desktop

Claude Desktop uses the same `mcpServers` command/args pattern. Add the fragment
through the client's MCP settings or merge it into that client's existing JSON.
Configuration locations vary by operating system and client release, so inspect
the client's active settings rather than assuming a path.

If Desktop starts MCP outside the indexed project, generate a project-pinned
configuration:

```bash
python scripts/generate_service_config.py mcp \
  --client claude-desktop \
  --server-name leann-server \
  --project-dir "/path/to/project with spaces"
```

With `--project-dir`, the generator emits a shell-free `python -c` module runner
that changes directory and then runs `leann.mcp`. The configured Python command
must resolve to an interpreter containing `leann-core`. This is used instead of
`leann_mcp --base-dir`, whose parsed directory is not applied by the verified
server implementation.

## OpenClaw through MCP

MCP and the separate OpenClaw skill are two integration choices. For MCP, merge:

```json
{
  "mcpServers": {
    "leann": {
      "command": "leann_mcp",
      "args": [],
      "env": {}
    }
  }
}
```

into OpenClaw's active JSON configuration. Generate the same shape, optionally
pinned to a project directory, with:

```bash
python scripts/generate_service_config.py mcp --client openclaw --server-name leann
```

### Memory index contract

A conventional OpenClaw memory index is named `openclaw-memory` and includes the
main memory file plus the memory directory:

```bash
leann build openclaw-memory \
  --docs "$HOME/.openclaw/workspace/MEMORY.md" \
         "$HOME/.openclaw/workspace/memory" \
  --embedding-mode sentence-transformers \
  --embedding-model all-MiniLM-L6-v2
```

Re-running the same build updates changed inputs according to the selected
backend's capabilities. To query through MCP, call `leann_search` with
`index_name: "openclaw-memory"`; to query directly:

```bash
leann search openclaw-memory "database decisions" \
  --top-k 5 --json --non-interactive
```

Memory files and result metadata are private. Run the process under the user who
owns the workspace, do not index broad home-directory roots, and inspect
results before sharing them.

### Keep identities separate

The OpenClaw/ClawHub artifact has identity `leann-memory`; this DisCo operating
sub-skill has identity `mcp-and-services`. Do not copy, rename, or install one as
the other.

The source `leann-memory` manifest contract requires:

- name `leann-memory`;
- a version, description, author, license, permissions, and entry file;
- `shell` permission because it invokes the LEANN CLI;
- memory/search discovery tags and at least one compatible model family;
- instructions containing installation preflight plus `leann build` and
  `leann search --json` workflows.

If OpenClaw reports a manifest mismatch, validate those fields in the actual
OpenClaw skill. MCP-only setup does not need that manifest.

## Project-directory choices

| Situation | Recommended setup |
|---|---|
| Client is launched from the indexed project | Direct `leann_mcp` entry point. |
| Desktop/global client chooses another cwd | Generate a project-pinned module config with `--project-dir`. |
| Multiple projects need independent indexes | Register local servers per project or generate distinct server names/configs. |
| One client needs global discovery only | `leann_list` can enumerate registered projects, but search/build/status still depend on the subprocess cwd and index name. |
| Project path contains spaces | Keep it as one JSON `args` item; use the generator rather than hand-built shell quoting. |

## Client validation checklist

1. Parse the final JSON with a JSON parser; comments and trailing commas are not
   valid JSON even if a source guide showed JSON5-style examples.
2. Confirm the configured executable or module interpreter resolves in the GUI
   client's environment, not only in an interactive shell.
3. Start with `initialize`, then `tools/list`; expect four tools in the current
   implementation.
4. Call `leann_status` for the intended index before `leann_search`.
5. Check client logs for stderr diagnostics, but inspect stdout as raw protocol
   if parsing fails.
6. Revoke broad filesystem/network permissions after testing.

Provider-specific OpenClaw/Ollama tool-calling setup belongs to
`embeddings-and-chat`; continuous `leann watch` operation belongs to
`cli-operations`.
