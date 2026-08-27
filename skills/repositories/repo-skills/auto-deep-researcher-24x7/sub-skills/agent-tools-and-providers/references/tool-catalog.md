# Tool catalog and safety contract

`ToolRegistry(backend)` is the single execution boundary. `get_tools_for`
returns JSON-schema-like definitions; `execute_tool(name, args)` dispatches by
name, catches handler exceptions, logs the failure, and returns
`{"error": "..."}` rather than raising through the worker loop. The backend
may be local, SSH, or Slurm; backend selection and transport details belong to
the execution skill.

## Allow-lists

| agent type | exact tools | purpose |
|---|---|---|
| `leader` | `log_memory`, `write_file`, `read_file` | decisions and context files |
| `idea` | `search_papers`, `search_arxiv`, `get_paper`, `write_file`, `read_file` | literature and notes |
| `code` | `run_shell`, `launch_experiment`, `write_file`, `read_file`, `list_files`, `list_tree`, `search_code` | inspect, edit, dry-run, and launch |
| `writing` | `write_file`, `read_file`, `list_files`, `search_code` | reports and analysis |

An unknown agent type receives an empty list from `get_tools_for`; dispatcher
worker validation still rejects unknown worker types before it asks for tools.
The allow-list is descriptive, not an authorization to bypass the registry.

## File and repository tools

### `read_file`

Schema: required `path`; optional integer `start_line` and `end_line` (both
1-indexed, inclusive). Without a range, returns raw file text capped at 10,000
characters. With either range field, the backend returns numbered lines in the
form `<line>\t<text>`, capped at 20,000 characters. A missing file yields a
structured `File not found` error. A range with an end before its start returns
an empty string.

### `write_file`

Schema: required string `path` and `content`. Creates parent directories and
returns JSON such as `{"status":"written","path":"notes/x.md","bytes":12}`.
The basenames `state.json`, `MEMORY_LOG.md`, `PROJECT_BRIEF.md`, and `.lock` are
protected at every directory depth. Attempting one returns
`{"error":"Cannot overwrite protected file: <path>"}` without invoking the
backend. This tool does not make writes atomic and is not a substitute for
experiment lifecycle state management.

### `list_files`

Schema: optional `path`, default `.`. Lists one directory, non-recursively,
sorted and capped at 100 names. A non-directory is a structured error.

### `list_tree`

Schema: optional `path` (default `.`), integer `max_depth` (default 3), and
integer `max_entries` (default 300). Depth and entry limits are clamped to at
least 1. Directory names end in `/`. It skips `.git`, `__pycache__`,
`node_modules`, `.venv`, `venv`, `.mypy_cache`, `.pytest_cache`, `.idea`, and
`.ipynb_checkpoints`, and never follows symlinks. It is a bounded structural
map, not a data inventory.

### `search_code`

Schema: required regex string `pattern`; optional `path` (default `.`),
`max_results` (default 50), and boolean `ignore_case` (default false). Returns:

```json
{"matches":[{"file":"src/train.py","line":2,"text":"def main():"}],"count":1}
```

Matches are relative to the workspace, line text is capped at 300 characters,
and results are bounded. Empty patterns and invalid regular expressions return
an error; files over 2,000,000 bytes, binary/unreadable files, and symlinks are
skipped. Search uses regex semantics, not a shell or literal substring search.

## Command tools

### `run_shell`

Schema: required string `command`; optional integer `timeout` (default 120).
The registry uses `shlex.split`, then passes an argv list to the backend's
non-shell subprocess call. It returns backend JSON with `stdout` capped at the
last 2,000 characters, `stderr` at the last 500, and `returncode`, or a timeout
error. Empty input returns `Command cannot be empty`; malformed quoting returns
`Invalid command syntax: ...`.

Before execution, the executable basename is blocked when it is one of:
`rm`, `sudo`, `su`, `mkfs`, `dd`, `shutdown`, `reboot`, `poweroff`, `halt`.
For example, `echo hello; touch injected.txt` is parsed as arguments to
`echo`, not as shell syntax, so it prints the semicolon text and does not create
a file. This protection is not a full sandbox: a user/model can explicitly
name an interpreter such as `sh` or `python`, and commands may still have
legitimate side effects. Use only commands appropriate for the project.

### `launch_experiment`

Schema: required string `command` and `log_file`; optional string `gpu`. It
uses the same argv parsing and blocked executable list as `run_shell`,
normalizes the log path, and invokes the backend's launch operation. `gpu`,
when non-empty, is passed as `CUDA_VISIBLE_DEVICES`; Slurm-specific behavior
may ignore it. A successful local/SSH result has the shape:

```json
{"pid": 1234, "log_file":"logs/exp.log", "status":"launched"}
```

The returned PID and log path are authoritative only when returned by this
tool. The worker result parser promotes those fields for a code worker; the
monitor then owns liveness and terminal outcome. Traversal in `log_file` is
rejected before launch.

## Path boundary

Every path-bearing tool first calls `normalize_relative_path`:

- blank/`None` → `ValueError: Path cannot be empty`;
- absolute POSIX paths → `ValueError: Path must be relative to workspace`;
- any `..` component → `ValueError: Path escapes workspace: <path>`;
- `.` and equivalent components normalize to workspace-relative text.

The backend then resolves the path under its workspace and checks that the
resolved path remains under the root. This second check catches symlink escapes;
repo listing and grep additionally skip symlink entries. A rejected path
returns JSON from `execute_tool`, and no recording backend call should occur.
The path is not interpreted relative to the process's current directory.

## Literature tools

Literature calls intentionally access external services. Obtain permission and
expect rate limits, transient failures, and incomplete indexes. Do not place
credentials in query strings or results.

### `search_papers` (Semantic Scholar)

Required string `query`; optional integer `limit` (minimum 1, default 10) and
string `year` such as `2024-2026`. The request asks for
`title,year,authors,abstract,citationCount,url` and returns
`{"papers":[...]}` capped to the requested limit. A network or decoding
failure returns `{"error":"Search failed: <detail>"}`.

### `search_arxiv` (Atom API)

Required string `query`; optional integer `limit` (minimum 1, default 10) and
string `category` such as `cs.CV`. It searches `all:<query>`, or
`cat:<category> AND (all:<query>)`, sorted by submitted date descending. Each
parsed result has `arxiv_id`, normalized `title`, `published`, author names,
normalized `abstract`, and `url`. A network failure returns
`{"error":"arXiv search failed: <detail>"}`. Malformed XML after a successful
HTTP response is caught by the outer tool boundary and becomes a generic
structured error.

### `get_paper` (Semantic Scholar)

Required nonblank `paper_id`, accepted by the upstream API as a Semantic
Scholar ID, `arXiv:...`, `DOI:...`, or `CorpusId:...`. Optional booleans
`include_references` and `include_citations` default true. It requests title,
year, authors, abstract, citation count, venue, URL, plus selected reference
and citation fields. Each of `references` and `citations` is trimmed to the
first 25 entries. Blank IDs fail locally with `paper_id cannot be empty`; other
network/API/decode failures return `get_paper failed: <detail>`.

`search_papers`, `search_arxiv`, and `get_paper` use bounded urllib timeouts
(15s, 20s, and 20s respectively) and identify as `AutoResearcher/1.0`. These
are the only catalog operations that intentionally have network side effects.

## Observable error discipline

Prefer the JSON error object over inferring success from model prose. Preserve
the error detail for the next worker turn, but redact any accidental secret
material before writing logs or reports. If a tool returns an error, the worker
may correct its arguments or stop; do not automatically retry unboundedly.
