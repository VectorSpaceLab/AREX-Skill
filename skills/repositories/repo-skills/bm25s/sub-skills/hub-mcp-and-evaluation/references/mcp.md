# Local MCP integration

The MCP adapter exposes a saved bm25s index through two tools. It is an
optional integration and should be treated as a local process boundary unless
the operator separately configures and secures a transport.

## Dependency and version gate

Install the package's `mcp` extra or install a compatible MCP package. The
verified environment for this revision imported `mcp.server.fastmcp` from
MCP `1.29.0`. An observed MCP `2.0.0` installation was incompatible with the
source import, so use and document a bounded constraint such as `mcp<2` when
reproducing this revision. Do not infer compatibility from the package name or
from the newest release.

The import path that is supported by the implementation is:

```python
from bm25s.mcp.server import create_mcp_server
```

The package initializer imports the `server` module but does not re-export
`create_mcp_server`. A direct `from bm25s.mcp import create_mcp_server` can
therefore fail even when MCP itself is installed. Treat that as an import-path
issue, not as evidence that the index is invalid.

A minimal diagnostic is safe and does not load an index:

```bash
python -c "import mcp; from mcp.server.fastmcp import FastMCP; print(getattr(mcp, '__version__', 'unknown'))"
python -c "from bm25s.mcp.server import create_mcp_server; print(create_mcp_server)"
```

If the second command fails, do not start a long-lived server. Record the
exception and the installed MCP version, then repair the dependency or use
`python scripts/verify_mcp_fixture.py --diagnose-import`.

## Index contract

`create_mcp_server(index_dir: str, port: int = 8000)` immediately calls the
normal loader with `load_corpus=True`. The directory must therefore be a valid
local bm25s save directory and must contain a compatible serialized corpus.
An index with score arrays and vocabulary but no corpus is insufficient for
this adapter, even though ordinary score-only retrieval can be possible in
other routes.

The `port` parameter is accepted by the factory, but this revision does not
pass it into the `FastMCP` constructor. The CLI's `--port` argument is parsed
and forwarded, yet `main` calls `mcp.run()` without a transport argument;
MCP's default run mode is therefore the installed library's default (verified
as stdio for the inspected API). Do not describe `bm25 mcp launch --port` as
an HTTP listener unless a separately inspected MCP version and transport
configuration establish that behavior.

## Tools and outputs

The factory creates a `FastMCP("bm25s")` instance and registers:

### `get_info()`

Returns a string with the vocabulary size, document count, and backend, for
example:

```text
BM25S Index Info:
- Vocab Size: 123
- Num Docs: 3
- Backend: numpy
```

The values are read from the loaded retriever. A missing vocabulary or malformed
parameters file should be repaired at the index layer rather than worked
around in MCP.

### `retrieve(query: str, k: int = 10)`

The tool tokenizes the one query string with `bm25s.tokenize`, invokes the
loaded retriever, and formats each returned document and score as a string:

```text
Rank 1 (Score: 1.2345):
<document text>
```

Use a small positive `k` for a fixture check. The tool is not an arbitrary
query-language endpoint, does not expose raw score matrices, and does not
return a structured authorization or provenance record. Document identifiers
or metadata are only as useful as the corpus representation saved with the
index.

## Bounded in-process check

The bundled scripts make a five-document-or-smaller index and call the tools
without opening a port:

```bash
python scripts/create_mcp_fixture.py --output-dir ./bm25s-mcp-fixture
python scripts/verify_mcp_fixture.py \
  --index-dir ./bm25s-mcp-fixture --query "blue fox" --k 2
```

The verifier discovers the tool names with `list_tools` when available and
then calls `get_info` and `retrieve`. In the verified MCP API,
`FastMCP.call_tool(name, arguments)` is an async method returning content
blocks or a mapping, so the helper normalizes those values for display. It
never calls `run`, `run_sse_async`, or an HTTP app. If the installed MCP API
has no compatible direct-call method, the helper emits import/help diagnostics
instead of silently launching a server.

This check proves only local index loading, factory registration, and bounded
function behavior. It does not prove client negotiation, stdio framing,
network isolation, authentication, concurrency, or transport security.

## CLI route

After the dependency and index checks, the package entry point is:

```bash
bm25 mcp --help
bm25 mcp launch --help
bm25 mcp launch --index-dir /path/to/saved-index --port 8000
```

The index path must be explicit. Use a foreground process and a disposable
fixture when diagnosing. Do not run the command in a background service or
publish its transport configuration as deployment guidance without an
independent security review.

## Recovery order

1. Confirm the directory exists and contains the normal BM25 files plus corpus
   data.
2. Confirm `from bm25s.mcp.server import create_mcp_server` works.
3. Confirm the MCP major version is on the tested compatibility line.
4. Run the in-process fixture verifier.
5. Inspect `bm25 mcp launch --help`.
6. Only then, with explicit operator intent, launch a foreground process.

For missing corpus, import-path, CLI, and version failures, see
[troubleshooting.md](troubleshooting.md).
