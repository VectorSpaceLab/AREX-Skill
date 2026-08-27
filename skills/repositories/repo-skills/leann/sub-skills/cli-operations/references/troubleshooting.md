# CLI troubleshooting

## Fast triage

Run these from the project expected to own the index:

```bash
leann --help
leann list
leann daemon status
```

Then inspect the exact group's help. Do not repair a CLI problem by deleting
`.leann`, hand-editing daemon records, or creating placeholder index artifacts.

## Parser and command-shape failures

| Symptom | Likely cause | Correct action |
|---|---|---|
| `unrecognized arguments: --verbose` after a group | Global flag placed after the subcommand | Use `leann --verbose search ...`; global `-v/-q` precedes the group. |
| `unrecognized arguments: --query` for search | Search/react query is positional | Use `leann search INDEX "query"` or `leann react INDEX "query"`. |
| `unrecognized arguments: --llm-model` | Current ask/react flag is `--model` | Replace it with `--model`; verify the group's help. |
| `unrecognized arguments: --backend` | Current build flag is `--backend-name` | Use `--backend-name {hnsw,diskann,ivf}`. |
| File types parsed as extra arguments | `--file-types` takes one comma-separated string | Use `--file-types .md,.py`, not `--file-types .md .py`. |
| `daemon` prints “Please specify…” | Missing nested action | Use `daemon start`, `daemon stop`, or `daemon status`. |
| `daemon stop` prints “Provide an index name or pass --all.” | Neither selector provided | Supply one index, or explicitly accept global impact with `--all`. |
| `remove --force` refuses | More than one index has that name | Run without force, inspect every path, and select interactively; preferably rename future indexes uniquely. |
| `list --max-depth` parse error | Negative depth | Use zero or a positive integer. |

Repository documentation from older releases may show stale spellings. Treat
`leann GROUP --help` as authoritative for the installed version.

## Metadata-filter failures

Valid form:

```json
{"chapter":{"<=":5},"genre":{"==":"fiction"}}
```

| Failure | Cause | Fix |
|---|---|---|
| `not valid JSON` | Bad quoting, missing brace, or shell interpolation | Single-quote the complete JSON object in POSIX shells; validate with the bundled planner before executing. |
| `must be a JSON object` | Top-level value is a list/scalar/null | Wrap field specifications in an object. |
| Empty results with warning about unsupported operator | Operator not implemented | Use `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not_in`, `contains`, `starts_with`, `ends_with`, `is_true`, or `is_false`. |
| Empty results with `in`/`not_in` | Expected value is not a collection | Supply a JSON array, for example `{"tag":{"in":["a","b"]}}`. |
| Fewer results than expected | Filters run after candidate retrieval | Increase `--top-k`/search complexity or loosen the filter; verify metadata with `--show-metadata` or `--json`. |
| JSON automation hangs | Duplicate name causes selection prompt | Add `--non-interactive`, run from the owning project, and make index names unique. |

The CLI validates only that the filter is a JSON object before starting search or
chat. The bundled planner additionally validates field/operator shape and exits
nonzero on malformed input.

## Missing source or index

| Symptom | Diagnosis | Recovery |
|---|---|---|
| Build shows zero files/directories then `No documents found` | Paths missing, extensions excluded, hidden paths excluded, or readers produced no text | Run the planner with `--check-inputs`; inspect `--file-types` and `--include-hidden`; retry without changing the existing index. |
| `Index 'X' not found` | Wrong current project, unregistered/moved project, wrong name, or incomplete metadata | Run `leann list` in the likely owner. Do not create an empty metadata file. Rebuild from sources if artifacts are gone. |
| `ask` cannot find an index that search finds | `ask` only checks current-project CLI indexes | Change to the owning project or create a deliberate local index; do not expect global registry resolution. |
| Search chooses an unexpected index | Duplicate name and non-interactive/first-match resolution | Change to owner, use a unique name, and confirm with `leann list`. Search interactively once if safe. |
| `rebuild` says no sync config | Index came from Python API or config was lost | Re-run the original `leann build ... --docs ...` procedure. Never synthesize roots from guesses. |
| `rebuild` says no document roots | Stored scope has no directory roots, including explicit-file-only builds | Replay the original build command with its explicit files. |
| `watch` says sync config missing | Index was not successfully built by CLI | Rebuild with `leann build INDEX --docs ...`; watch cannot infer scope. |

## Unsafe rebuild or migration assumptions

| Risky assumption | Actual behavior | Safe response |
|---|---|---|
| `build` always appends | Only qualifying non-compact HNSW add-only or IVF deltas are incremental | Read the lifecycle decision table; modified/removed HNSW content, compact indexes, DiskANN, or model changes cause full rebuild. |
| `rebuild --force` is needed after every change | Default rebuild already detects deltas | Use default first. Reserve force for an intentional full replacement. |
| Full rebuild can corrupt the old complete index on builder failure | Existing complete CLI index is built in staging and restored/preserved on failure | Keep the old index; investigate the build error. Still back up before external/manual changes. |
| `migrate-ids --dry-run` is a backup | Dry run only counts planned IDs/collisions | Copy and verify the complete index directory first. |
| Content-hash migration preserves duplicate passages | Identical text hashes collide and later offsets win | Review collision count; retain the backup if duplicate identity matters. |
| `--yes` makes migration safer | It only skips the confirmation prompt | Use it only after backup, dry-run review, and daemon stop. |
| Deleting the index fixes stale daemon state | Daemon registry/process state is separate | Stop/prune daemons; never delete the index for a port issue. |

## Daemon, TTL, and port failures

| Symptom | Likely cause | Non-destructive recovery |
|---|---|---|
| Status shows no daemon after idle time | Default TTL expired | Run `warmup`/`daemon start` again; use a reviewed longer TTL or `0` if persistent service is intended. |
| Search starts another daemon | Model/provider/index signature differs, or prior process/port is dead | This is expected compatibility isolation. Stop obsolete daemons after confirming active workloads. |
| Startup says no ports available | Every localhost port in the 5557–5656 scan range is occupied | Stop stale LEANN daemons, inspect other local services, then retry. There is no CLI daemon-port flag. |
| Recorded port is open but wrong process serves it | Stale process/record mismatch | `daemon stop INDEX`, then `daemon status` to prune; if unresolved, stop all LEANN daemons during a maintenance window. Do not edit registry JSON. |
| Status for an index reports none but global status shows records | Index path/signature changed or duplicate name resolved elsewhere | Run from the owner, compare global status, stop obsolete records safely, then warm the desired index. |
| Search works with `--no-daemon` only | Reuse state is stale or startup signature differs | Stop index daemon, verify port range, warmup fresh, and retry before changing the index. |

The HTTP service port (`serve --port`, default 8000) is unrelated to the daemon
ZeroMQ port range.

## Watch surprises

| Symptom | Cause | Fix |
|---|---|---|
| Change repeats every dry-run | Dry-run does not rebuild or commit a snapshot | Expected. Run one non-dry `--once` after reviewing the changes. |
| Touching a file is ignored | Watch hashes bytes, not mtime | Change file content if a rebuild is intended. |
| Explicit README causes sibling assets to scan | This should not occur; explicit files remain separate | Check stored scope and version. Do not broaden the source to `.` as a workaround. |
| Hidden source is ignored | Original build used default hidden exclusion | Rebuild intentionally with `--include-hidden` after reviewing sensitive files. |
| Binary/media file is ignored | Extension is not in the stored allowlist | Expected. Add a supported reader/extension only through an intentional rebuild. |
| Two watch loops race | No index-build lock serializes watch loops | Stop both, verify the index, then run one owner loop. |

## Platform-only indexers and optional dependencies

| Command/problem | Requirement or action |
|---|---|
| Browser profile not found | Current `index-browser` builds a default macOS Chrome/Brave path and has no profile override. Use the supported default profile or the deeper RAG application workflow. |
| Apple Mail or iMessage permission denied | Grant Full Disk Access to the terminal/IDE, quit it completely, restart, and retry. |
| Calendar Cache not found | Run on macOS as the user owning Calendar data; verify Calendar has initialized its cache and privacy access is granted. |
| WeChat produces no documents | Supply an already exported JSON directory. The CLI does not run the exporter. |
| ChatGPT/Claude path error | Supply an existing supported HTML/JSON/ZIP export or reader-supported directory; validate with planner `--check-inputs`. |
| AST chunking import failure | `--use-ast-chunking` requires the optional `astchunk` package; omit the mode or install the documented optional dependency in the execution environment. |
| `serve` exits with missing FastAPI/Uvicorn | Install the package's server extra, then use the service sub-skill for endpoint/deployment checks. |

Shell/cron automation from data-indexer documentation is intentionally not
bundled: it changes long-running processes and indexes on a schedule. First
prove a bounded manual command, then design scheduling in the deployment
context with explicit logging, ownership, and overlap prevention.
