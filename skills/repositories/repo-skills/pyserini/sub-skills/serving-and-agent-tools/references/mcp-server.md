# MCP Server

Pyserini's MCP server exposes search, document retrieval, index discovery, qrels, evaluation, and result fusion tools to MCP clients. It uses the same `SharedSearchBackend` and optional YAML aliases as the REST server.

## Choose a Transport

Use `stdio` when the MCP client launches Pyserini as a local child process:

```bash
python -m pyserini.server.mcp
python -m pyserini.server.mcp --config server.yaml
```

Use HTTP transport when Pyserini runs as a long-lived local, remote, container, or forwarded service:

```bash
python -m pyserini.server.mcp --transport http --port 8000 --config server.yaml
```

The HTTP endpoint path used by common clients is `/mcp`, for example `http://127.0.0.1:8000/mcp`.

## Local Client Config

A local stdio client should run the Python executable from an environment where `import pyserini`, Java-backed Lucene, and any optional dense/Faiss dependencies needed by the target indexes work.

```json
{
  "mcpServers": {
    "mcpyserini": {
      "command": "python",
      "args": ["-m", "pyserini.server.mcp", "--config", "server.yaml"]
    }
  }
}
```

If Java resolution fails in the client-launched process, set `JAVA_HOME` or equivalent environment variables in the client config. Keep the value environment-specific; do not bake machine paths into reusable instructions.

```json
{
  "mcpServers": {
    "mcpyserini": {
      "command": "python",
      "args": ["-m", "pyserini.server.mcp", "--config", "server.yaml"],
      "env": {
        "JAVA_HOME": "replace-with-java-home-for-this-machine"
      }
    }
  }
}
```

## Remote or Forwarded Client Config

Run the server on the machine with Pyserini and index access:

```bash
python -m pyserini.server.mcp --transport http --port 8000 --config server.yaml
```

If connecting over SSH, forward the port:

```bash
ssh -L 8000:localhost:8000 user@host
```

Then configure an HTTP-capable MCP client:

```json
{
  "mcpServers": {
    "mcpyserini": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

For clients that only support local stdio but need a remote Pyserini HTTP server, use a small local bridge that forwards MCP calls to the HTTP endpoint. Keep such bridge code client-local and review it for the target deployment rather than relying on a source checkout file.

## Tools

Ask the client for the live `tools/list` schema when available. The source-grounded tool summary is:

| Tool | Purpose | Key arguments |
| --- | --- | --- |
| `search` | Search a sparse, dense, impact, Lucene dense, or Faiss index and render rich content. | `query`, `index`, `hits`, `parse`, `ef_search`, `encoder`, `query_generator`, `k1`, `b` |
| `get_document` | Fetch one stored document and render text/image content when available. | `docid`, `index`, `parse` |
| `list_indexes` | List prebuilt or configured index names for a family. | `index_type`: `tf`, `lucene_flat`, `lucene_hnsw`, `impact`, `faiss` |
| `get_index` | Return metadata and download status for an index name. | `index_name` |
| `fuse_search_results` | Fuse two ranked result lists. | `results1`, `results2`, `hits` |
| `get_qrels` | Return relevance judgments for a Pyserini qrels collection id and topic id. | `index_name`, `query_id` |
| `eval_hits` | Evaluate a provided hit dictionary using Java-backed `trec_eval`. | `index_name`, `metric`, `query_id`, `hits`, `cutoff` |

## Search Tool Details

`search` accepts either a string-like text query through a dict or a multimodal query dictionary:

```json
{"query_txt": "what is a lobster roll"}
```

Multimodal-capable indexes may accept fields such as `query_img_path` where supported by the index backend. For ordinary text indexes, provide `query_txt`.

Sparse TF options:

- `query_generator`: `BagOfWords`, `DisjunctionMax` or `dismax`, `QuerySideBm25` or `bm25qs`, `Covid19`.
- `k1` and `b`: must be set together; omit both for Pyserini/Anserini defaults.

Dense/HNSW options:

- `encoder`: query encoder id for dense, impact, or Faiss indexes when the index requires one.
- `ef_search`: HNSW search parameter, default `100`.

MCP returns rich content lists so clients can render mixed text and image parts. Do not force everything into a flat table unless the user explicitly asks for a transformed summary.

## Qrels and Evaluation Caveat

`get_qrels` and `eval_hits` use qrels collection ids, which may differ from Lucene index names. For example, a search index can be `msmarco-v1-passage`, while qrels may use a collection id such as `msmarco-v1-passage-dev`.

`eval_hits` depends on Pyserini's Java-backed evaluation resources. If MCP startup or tool calls fail with missing eval resources, route to `../../install-and-runtime/SKILL.md` for package/runtime checks and `../../repo-development/SKILL.md` when the user is working from a source checkout that must build or provide evaluation jars.

## Prompting an Agent Client

Good prompts are explicit about the tool, index alias, and output size:

- Search `local_sparse` for `information retrieval` with 5 hits and summarize docids and scores.
- Use `get_document` for docid `CACM-3134` from `local_sparse` with `parse=false`.
- List available `tf` indexes, then explain which one is appropriate for a short RAG demo.
- Search `local_hnsw` with `ef_search=200` and encoder `BAAI/bge-base-en-v1.5`.

If the client repeatedly chooses a prebuilt index when deployment requires local aliases, configure `--config` and prompt with the alias name. If `--no-prebuilt-indexes` is desired, use REST for that flag; the MCP CLI currently accepts `--config` but not a `--no-prebuilt-indexes` flag.
