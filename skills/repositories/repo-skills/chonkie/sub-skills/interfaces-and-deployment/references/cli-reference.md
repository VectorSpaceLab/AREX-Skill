# Chonkie CLI reference

This reference covers the installed `chonkie` console script for command construction and safe diagnostics. Install the `cli` extra when the console script or Typer help is unavailable:

```bash
pip install "chonkie[cli]"
```

The console entry point is `chonkie`, with three commands: `chunk`, `pipeline`, and `serve`.

## Top-level command

```bash
chonkie --help
```

Top-level options:

| Option | Purpose |
| --- | --- |
| `--install-completion` | Install shell completion for the current shell. |
| `--show-completion` | Print shell completion configuration. |
| `--help` | Show help and exit. |

Commands:

| Command | Purpose |
| --- | --- |
| `chonkie chunk` | Chunk text or a file with one selected chunker and optionally store chunks. |
| `chonkie pipeline` | Run a fetch/process/chunk/refine/store pipeline on text, a file, or a directory. |
| `chonkie serve` | Start the local FastAPI API server. |

## `chonkie chunk`

Usage:

```bash
chonkie chunk [OPTIONS] TEXT
```

`TEXT` is either raw text or a file path. If the value points to an existing file, the CLI reads that file as UTF-8. If it does not point to a file, the value is treated as raw text.

Options from installed help:

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `--chunker` | string | `semantic` | Chunking method. Installed help lists `code`, `fast`, `late`, `neural`, `recursive`, `semantic`, `sentence`, `slumber`, `table`, `teraflopai`, `token`. |
| `--chunk-size` | integer | unset | Maximum number of tokens per chunk; passed to chunkers that accept `chunk_size`. |
| `--chunk-overlap` | integer | unset | Number of tokens to overlap between chunks; useful for token/sentence chunkers. |
| `--threshold` | float | unset | Semantic similarity threshold in `[0, 1]`; only meaningful for semantic chunking. |
| `--chunker-params` | repeated string | unset | Extra chunker constructor parameters as `key=value` strings, or bare boolean flags. Repeat the option for multiple values. |
| `--handshaker` | string | unset | Store chunks using a vector/datastore handshake. Installed help lists `chroma`, `elastic`, `lancedb`, `milvus`, `mongodb`, `pgvector`, `pinecone`, `qdrant`, `turbopuffer`, `weaviate`. Route datastore setup to `../integrations-and-storage/`. |
| `--help` | flag | n/a | Show help and exit. |

Safe deterministic examples:

```bash
# Avoids the semantic default and any model downloads.
chonkie chunk "First paragraph. Second paragraph." --chunker recursive --chunk-size 256

# Token-window chunking with explicit tokenizer and overlap.
chonkie chunk notes.txt --chunker token --chunk-size 512 --chunk-overlap 64 --chunker-params tokenizer=character

# Recursive recipe/parameter values are passed through --chunker-params.
chonkie chunk README.md --chunker recursive --chunker-params recipe=markdown --chunker-params min_characters_per_chunk=24
```

Storage example boundary:

```bash
chonkie chunk notes.txt --chunker token --chunk-size 512 --handshaker qdrant
```

Use that only after the selected handshake package, service URL, collection/index behavior, and credentials are clear. The `chunk` command instantiates the handshaker without additional CLI parameters, so non-default service settings often require a Python workflow instead; route to `../integrations-and-storage/`.

## `chonkie pipeline`

Usage:

```bash
chonkie pipeline [OPTIONS] [TEXT]
```

Input selection:

- If `TEXT` is an existing file, it adds a file fetch step.
- If `TEXT` is not a file, it is treated as raw text and passed directly to the pipeline run.
- If `--d DIR` is provided, it processes a directory with the selected fetcher and optional repeated `--ext` values.
- One of raw text, file path, or `--d` is required.

Options from installed help:

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `--fetcher` | string | `file` | Fetcher method, usually `file`. |
| `--d` | string | unset | Directory to process when no `TEXT` file/raw text is supplied. |
| `--ext` | repeated string | unset | File extensions to include with `--d`, for example repeat `--ext .md --ext .txt`. |
| `--chef` | string | unset | Processing/chef step, for example `text` or `markdown`. Route Python chef details to `../pipelines-and-processing/`. |
| `--chef-params` | repeated string | unset | Chef parameters as `key=value` strings. |
| `--chunker` | string | `semantic` | Chunker method. Prefer `recursive`, `token`, or `sentence` for no-download CLI examples. |
| `--chunk-size` | integer | unset | Maximum number of tokens per chunk. |
| `--chunk-overlap` | integer | unset | Number of tokens to overlap between chunks. |
| `--threshold` | float | unset | Semantic similarity threshold. |
| `--chunker-params` | repeated string | unset | Extra chunker parameters as `key=value` strings. |
| `--refiner` | string | unset | Refinery method, for example `overlap`. Embeddings refineries may need model/provider setup; route to `../embeddings-and-generative/`. |
| `--refiner-params` | repeated string | unset | Refinery parameters as `key=value` strings. |
| `--handshaker` | string | unset | Storage handshake method. Route service setup to `../integrations-and-storage/`. |
| `--handshaker-params` | repeated string | unset | Handshaker parameters as `key=value` strings. |
| `--help` | flag | n/a | Show help and exit. |

Safe deterministic examples:

```bash
# Raw text, deterministic recursive chunking.
chonkie pipeline "A short document. It has two sentences." --chunker recursive --chunk-size 256

# File input with markdown processing and overlap refinement.
chonkie pipeline README.md --chef markdown --chunker recursive --chunker-params recipe=markdown --refiner overlap --refiner-params context_size=32

# Directory input with repeated extension filters.
chonkie pipeline --d ./docs --ext .md --ext .txt --chunker recursive --chunk-size 512
```

## Shared parameter parsing

`--chunker-params`, `--chef-params`, `--refiner-params`, and `--handshaker-params` parse repeated strings with these rules:

| Input form | Parsed value |
| --- | --- |
| `flag_name` | `flag_name=True` |
| `enabled=true` / `enabled=false` | booleans |
| `value=none` / `value=null` | `None` |
| `n=42` | integer |
| `x=3.14` or `x=1e2` | float |
| anything else | string |

Explicit options such as `--chunk-size`, `--chunk-overlap`, and `--threshold` override the same keys provided through `--chunker-params`.

## `chonkie serve`

Usage:

```bash
chonkie serve [OPTIONS]
```

This starts a long-running Uvicorn server for `chonkie.api.main:app`. It requires the API dependencies:

```bash
pip install "chonkie[api]"
```

Options from installed help:

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `--host` | string | `0.0.0.0` | Host interface to bind. Use `127.0.0.1` for local-only development. |
| `--port` | integer | `8000` | Port to bind. |
| `--reload` / `--no-reload` | flag pair | `--no-reload` | Enable code auto-reload for development; avoid in production. |
| `--log-level` | string | `info` | Uvicorn/API log level: `debug`, `info`, `warning`, or `error`. |
| `--help` | flag | n/a | Show help and exit. |

Examples:

```bash
# Local-only development server.
chonkie serve --host 127.0.0.1 --port 8000

# Development reload and debug logging.
chonkie serve --host 127.0.0.1 --port 3000 --reload --log-level debug

# Equivalent direct Uvicorn command.
uvicorn chonkie.api.main:app --host 0.0.0.0 --port 8000
```

`chonkie serve` sets the `LOG_LEVEL` environment variable to the chosen log level before starting Uvicorn. For Chonkie's package-level logging controls, see `api-and-cloud-reference.md` and `troubleshooting.md`.
