# Index lifecycle operations

## Path model and preflight

The CLI is project-local by construction. At startup it uses the current
working directory as the project root and stores a CLI-built index at:

```text
./.leann/indexes/INDEX_NAME/documents.leann*
```

The `documents.leann` portion is a base path; metadata, passages, offsets, and
backend files are sibling artifacts. Run lifecycle commands from the project
that owns the index whenever possible.

Before any mutation:

1. Run `leann list` from the intended project and confirm the index type,
   project, status, and name.
2. Run `leann daemon status INDEX_NAME`; stop that index's daemon before a full
   rebuild, migration, manual backup, or removal.
3. For automation, reject ambiguous names rather than relying on first-match
   resolution. Search supports `--non-interactive`; mutation commands do not
   have a path argument.
4. Back up the **entire index directory**, not only `.meta.json`, before
   `migrate-ids`, risky rebuilds, or manual artifact work. Keep the backup
   outside the live index name and verify that it contains the metadata,
   passages JSONL, passage offset map, backend index, and optional BM25/ID map.
5. Never use `remove --force` as a recovery step. It deletes artifacts and does
   not repair them.

## Build decision table

`leann build` is idempotent when its sync snapshots and stored metadata are
available. It hashes file bytes, so touching a file without changing content is
not a modification.

| Existing index and detected change | Default behavior |
|---|---|
| No content changes | Print `Index up to date.` and exit |
| Non-compact HNSW, same embedding, added files only | Incremental append |
| Non-compact IVF, same embedding, additions/modifications/removals | Incremental remove/add |
| Compact index | Full rebuild |
| DiskANN index | Full rebuild |
| HNSW with modified or removed files | Full rebuild |
| Embedding model or mode changed | Full rebuild |
| `--force` | Full rebuild regardless of snapshots |

Full replacement of a complete existing CLI index is built in a sibling staging
directory and then published. A build exception removes the staging directory
and preserves the prior complete index. This protects against build-time
failure, but it is not a substitute for a backup before deliberate migration or
external artifact changes.

A first build records absolute source paths, extension/hidden policy, chunking,
backend settings, recomputation, and embedding provider options. In the current
build path, an embedding API key supplied explicitly or resolved from the
provider environment can be written into index metadata; protect such an index
as sensitive. `rebuild` deliberately does not replay that key. When
incrementally updating an existing index, the stored passage-ID scheme wins; a
conflicting new `--id-scheme` is ignored to prevent mixed ID schemes.

### Mixed file and directory build

```bash
leann build project-notes \
  --docs ./README.md ./src ./notes/plan.md \
  --file-types .md,.py \
  --embedding-mode openai \
  --embedding-model text-embedding-example \
  --embedding-api-base http://127.0.0.1:1234/v1 \
  --embedding-prompt-template "passage: " \
  --query-prompt-template "query: " \
  --no-compact
```

Directory roots are scanned recursively within the extension and hidden-file
policy. Explicit files remain explicit: watch does not broaden an explicit file
to its parent directory. Unsupported extensions and missing paths are skipped;
if no documents remain, the CLI reports `No documents found`.

## Rebuild

```bash
leann rebuild INDEX_NAME          # replay stored config; delta by default
leann rebuild INDEX_NAME --force  # replay stored config; full replacement
```

`rebuild` reconstructs a `build` invocation from the index metadata and
`sync_roots.json`. It requires:

- a resolvable index;
- `sync_roots.json`;
- at least one stored directory root;
- index metadata;
- still-accessible source paths and any required embedding service/model.

A CLI index built from **only explicit files and no directory root** can be
watched, but the current rebuild preflight reports that its sync config has no
document roots. Re-run the original `build ... --docs FILE...` command for that
case. An index built through the Python API normally has no CLI sync config and
cannot be rebuilt by this command.

Rebuild restores endpoint and prompt templates but deliberately does not replay
stored credentials. Make required credentials available only in the execution
environment. Use `--force` only when changing behavior requires a full
replacement or when a delta is not trusted; it is not needed for ordinary
add/modify/remove detection.

## Passage-ID migration

```bash
leann migrate-ids INDEX_NAME --dry-run
leann migrate-ids INDEX_NAME
```

Migration changes `sequential` passage IDs to `sha256(text)[:16]` content-hash
IDs. It rewrites the passages JSONL and offset map, rewrites the backend label
ID map when present, sets `passage_id_scheme` in metadata, and rebuilds the FTS5
BM25 artifact when configured. It does not rewrite the vector graph.

Identical passage text has the same 16-character hash. Later duplicates win in
the offset map, so the dry run reports how many collisions will be deduplicated.
The operation is irreversible and has no built-in backup flag.

Safe procedure:

1. Stop the daemon for this index.
2. Identify the exact local/app index selected by `leann list`; resolve any
   duplicate-name ambiguity before continuing.
3. Copy the complete index directory to a separately named backup on the same
   filesystem or another reliable destination.
4. Compare backup and live file counts/sizes; retain the backup until search and
   any BM25 workflow are verified.
5. Run `leann migrate-ids INDEX_NAME --dry-run` and record passage, unique-ID,
   and collision counts.
6. Run without `--yes` for an interactive confirmation. Use `--yes` only in an
   already reviewed non-interactive procedure.
7. Verify `leann search INDEX_NAME "known query" --non-interactive`, then start
   a fresh daemon if desired.

If required passages or offset artifacts are missing, stop. Do not create empty
replacement files or proceed with a partial copy.

## List and resolution behavior

`leann list` combines:

- CLI indexes under the current/registered project's `.leann/indexes/`;
- app-format `*.leann.meta.json` indexes discovered within `--max-depth`
  (default 5);
- the current project even when it is not already in the global project
  registry.

A successful CLI build or personal-data indexer registers its current project.
Nested registered projects are kept distinct to avoid duplicate app-index
listings.

Resolution is not identical across commands:

| Command family | Duplicate-name behavior |
|---|---|
| `search` | prompts unless `--non-interactive`; non-interactive prefers current project, then first match |
| `warmup`, `daemon`, `migrate-ids` | non-interactive; prefer current project, then first match |
| `watch`, `rebuild` | prefer a direct local CLI index; otherwise current match, then first match |
| `react` | uses its first discovered match when duplicates exist |
| `ask` | accepts only a CLI index in the current project |
| `remove` | displays every match and requires selection; `--force` refuses ambiguity |

For deterministic automation, change to the owning project and use unique index
names. `ask` is especially important: unlike search and react, it does not
resolve a registered index from another project.

## Remove

```bash
leann remove INDEX_NAME
leann remove INDEX_NAME --force
```

Removal searches current and registered projects and supports CLI-format and
app-format indexes. With one match it asks for confirmation unless `--force` is
present. A cross-project match gets an explicit warning. With multiple matches,
it requires interactive selection and then requires typing the index name;
`--force` refuses to choose.

For an app index, only files sharing that app index's `.leann*` base are
removed; the parent data directory is retained. For a CLI index, the selected
index directory is removed. Always back up an index whose source data cannot be
reproduced.
