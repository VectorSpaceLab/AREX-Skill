# Daemon, watch, registry, and source indexers

## Embedding daemons

Search starts an embedding server with daemon reuse, startup warmup, and a
900-second idle time-to-live (TTL) by default. Control those behaviors per
search:

```bash
leann search notes "query" --daemon --daemon-ttl 900 --warmup
leann search notes "query" --no-daemon --no-warmup
leann warmup notes --daemon --daemon-ttl 0
```

`0` means the daemon does not expire for idleness. A non-daemon server belongs
to the invoking process and is cleaned up with it. Daemon registry records are
stored in the user's LEANN state directory and keyed by backend plus the full
server configuration, including model, embedding mode/provider options,
distance metric, index metadata path, and signatures of the passage/index
sources. An index or model change therefore starts or adopts a different
compatible process instead of blindly reusing a stale configuration.

The embedding server begins at TCP port 5557 and scans up to 100 consecutive
localhost ports for an available one. The public CLI does not expose a daemon
port flag. Do not confuse these internal ZeroMQ ports with `leann serve --port`
(the HTTP service port).

### Explicit management

```bash
leann daemon start notes --daemon-ttl 900 --warmup
leann daemon status
leann daemon status notes
leann daemon stop notes
leann daemon stop --all
```

`status notes` resolves the index and filters records by that index's metadata
path. Status removes unreadable/dead records when their process ID is gone or
the recorded port no longer accepts a localhost connection. `stop notes` sends
a termination signal only to records for that index; `stop --all` targets all
live registered LEANN daemons.

Safe stale-daemon recovery, without deleting the index:

1. `leann daemon status INDEX_NAME`.
2. `leann daemon stop INDEX_NAME`; if the name no longer resolves but stale
   daemons remain, inspect `leann daemon status` and use `stop --all` only when
   stopping unrelated LEANN daemons is acceptable.
3. Re-run `leann daemon status` to let dead records be pruned.
4. Confirm that localhost ports 5557 through 5656 are not all occupied by other
   services. LEANN automatically selects the first available port; there is no
   supported `--daemon-port` override.
5. Run `leann warmup INDEX_NAME --daemon --daemon-ttl 900`, then a small search.
6. If the index changed, do not restore or edit a daemon registry JSON record;
   let the new content signature create a fresh compatible record.

## Watch scope and checkpoints

A successful CLI build stores `sync_roots.json` and Merkle-tree snapshots inside
the index directory. Watch reloads exactly that scope:

- directory inputs remain recursive directory roots;
- explicit file inputs remain individual files;
- the build's extension allowlist is retained;
- the build's hidden-path policy is retained;
- file bytes are hashed with SHA-256, so an mtime-only touch is ignored;
- sibling directories of an explicit file are not scanned.

```bash
leann watch notes --once --dry-run
leann watch notes --once
leann watch notes --interval 30
```

`--once --dry-run` is the safest diagnostic. It reports added, removed, and
modified paths plus known passage IDs, but does not rebuild or commit a new
snapshot. `--once` without dry-run triggers the same idempotent build path used
by `leann rebuild`, and successful build processing commits fresh snapshots.
The continuous loop repeats this behavior at the interval.

Watch requires a resolvable index and CLI sync config. It cannot infer source
roots from passage metadata. If it says the sync config is missing, rebuild the
index with `leann build INDEX_NAME --docs ...`; do not create a hand-written
empty config. If watch reports no changes unexpectedly:

1. Confirm the changed path is under a stored directory root or is an explicitly
   stored file.
2. Confirm its extension is in the stored `--file-types` allowlist.
3. Confirm hidden components were included at build time when needed.
4. Confirm file bytes changed, not only mtime.
5. Run `leann rebuild INDEX_NAME` to surface missing roots or metadata.

Do not run concurrent watch loops for the same index. The file lock in daemon
management does not serialize index builds or watch snapshot publication.

## Project registry and local/global names

The global project registry records project directories, not a second copy of
index data. `leann list` scans the current project and valid registered projects.
CLI commands still resolve a name to an index's original project directory.
Consequences:

- changing the current working directory changes the direct local index root;
- the same index name may exist in several registered projects;
- app-format indexes can be addressed by parent-directory name or file base;
- `--max-depth` affects app-index discovery for `list`, not CLI index lookup;
- stale project entries whose directories no longer exist are ignored.

Use unique names for non-interactive workflows. For duplicate names, see the
per-command resolution table in
[index lifecycle operations](index-lifecycle-operations.md).

## Personal-data indexer routing

The `index-*` commands are convenience readers followed by a local HNSW build.
They are not incremental `leann build` aliases: rerunning one builds the named
index again from the source reader. Use `--max-count` for a bounded first pass.
All share embedding configuration and `--no-recompute`; provider details belong
in [embeddings and chat](../../embeddings-and-chat/SKILL.md), while reader and
chunking behavior belongs in [RAG applications](../../rag-applications/SKILL.md).

| Command | Default index | Source and prerequisites |
|---|---|---|
| `index-browser [chrome|brave]` | `browser_history` | Current CLI paths are hard-coded to the default macOS Chrome/Brave profile. Close/synchronize the browser database if reads fail. There is no CLI profile-path override. |
| `index-email` | `email` | Apple Mail on macOS. Grant Full Disk Access to the terminal/IDE and restart it; the command auto-discovers Mail `Messages` directories. |
| `index-calendar` | `calendar` | Apple Calendar on macOS. Reads the Calendar Cache SQLite database through a temporary copy; Full Disk Access may be needed. |
| `index-imessage` | `imessage` | iMessage on macOS, normally backed by the user's Messages SQLite database. Grant Full Disk Access and restart the terminal/IDE. There is no CLI database-path override. |
| `index-wechat --export-dir DIR` | `wechat` | Existing directory of exported WeChat JSON. This command does not run an exporter. |
| `index-chatgpt --export-path PATH` | `chatgpt` | Existing ChatGPT `chat.html`/HTML export, ZIP, or reader-supported export directory. |
| `index-claude --export-path PATH` | `claude` | Existing Claude JSON, ZIP, or reader-supported export directory. |

For macOS privacy failures, granting access after a terminal is already running
is insufficient on some systems: quit and restart the application before
retrying. Browser CLI support should be treated as macOS-only in this version,
even though browser databases can exist on other platforms, because the CLI
constructs macOS profile paths and has no path flag.

## HTTP service boundary

`leann serve --host HOST --port PORT` starts the optional HTTP API service. Its
host/port are passed through the `LEANN_SERVER_HOST` and `LEANN_SERVER_PORT`
runtime configuration. If optional FastAPI/Uvicorn dependencies are absent,
the command exits with an installation hint. Endpoint contracts, MCP, exposure,
authentication, and deployment are owned by
[MCP and services](../../mcp-and-services/SKILL.md), not this CLI operations
reference.
