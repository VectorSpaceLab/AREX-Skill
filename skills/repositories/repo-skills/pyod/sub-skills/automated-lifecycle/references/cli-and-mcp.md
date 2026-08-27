# PyOD CLI and MCP Reference

PyOD exposes the automated lifecycle through a unified `pyod` command and an
optional MCP server. This file describes commands and JSON contracts; the bundled
smoke script deliberately does **not** start a server.

## CLI commands

Run through the console script when available:

```bash
pyod --help
pyod info
pyod install skill
pyod install skill --project
pyod install skill --list
pyod mcp serve
```

If the `pyod` executable is not on `PATH`, use the module form from the Python
environment that has PyOD installed:

```bash
python -m pyod.cli --help
python -m pyod.cli info
python -m pyod.cli install skill --list
```

### `pyod info`

Self-diagnostic command. It returns exit code `0` in a core install and prints:

- PyOD version.
- ADEngine detector count and modality breakdown; planned entries without a
  backing implementation are excluded.
- Classic detector API status.
- ADEngine status.
- MCP extra status. If missing, it prints an install hint for `pyod[mcp]`.
- `od-expert` skill install state for user-global Claude Code and project-local
  `./skills/od-expert` paths, plus agent-stack hints for Claude Code and Codex.

Use it first when a user says "PyOD agentic mode is not active" or "MCP is not
working".

### `pyod install skill`

Copies PyOD's packaged `od-expert` skill tree, including references, into an
agent skill directory.

| Command | Purpose |
|---|---|
| `pyod install skill` | User-global Claude Code activation. Installs `od-expert` under Claude Code's user skill directory. |
| `pyod install skill --project` | Project-local activation. Installs into `./skills/od-expert`; this is the Codex path and also works for project-local Claude Code sessions. |
| `pyod install skill --list` | Lists packaged skills; expected canonical name is `od-expert`. |
| `pyod install skill --skill od_expert` | Underscore input is accepted and normalized to canonical `od-expert`. |
| `pyod install skill --target <directory>` | Custom install root; creates `<directory>/od-expert`. |

The legacy `pyod-install-skill` command is an alias for the same install helper.
After installing into an external agent, restart that agent session so it can
load the new skill.

### `pyod mcp serve`

Starts the PyOD MCP server and blocks until stopped. It is an alias for
`python -m pyod.mcp_server`.

- Requires optional extra `pyod[mcp]`.
- If the `mcp` package is missing, the server entry point prints:
  `PyOD MCP server requires the 'mcp' package. Install with: pip install pyod[mcp]`
  and returns nonzero.
- Importing `pyod.mcp_server` is safe in a core install without the extra; the
  dependency check is lazy and does not exit at import time.
- Do not start the server from validation or smoke scripts unless the user
  explicitly asked for a live MCP service.

## MCP server tools

When `pyod mcp serve` runs successfully, it registers ten tools in this order:

1. `profile_data`
2. `plan_detection`
3. `build_detector`
4. `list_detectors`
5. `explain_detector`
6. `compare_detectors`
7. `get_benchmarks`
8. `run_detection`
9. `analyze_results`
10. `explain_findings`

The tools are stateless wrappers around `ADEngine`. Most return JSON strings.
Use `json.loads(...)` on the client side and treat any object containing an
`error` key as a recoverable tool-level failure.

## MCP file loading rules

Tools that take `data_path` load local files by extension:

| Extension | Loader behavior |
|---|---|
| `.npy` | `numpy.load(..., allow_pickle=False)` |
| `.npz` | Loads the first array inside the archive. |
| `.csv` | `numpy.genfromtxt(..., delimiter=",", skip_header=1)`; when there is more than one column, the last column is treated as a label and dropped from features. |
| `.json` | `json.load` result. |
| `.mat` | `scipy.io.loadmat`; prefers key `X`, otherwise first non-private key. |

Unsupported extensions raise a loading error. For predictable agent handoffs,
prefer `.npy` feature matrices or CSV files with one header row.

## Tool contracts and payloads

### `profile_data(data_path: str, data_type: str = "auto") -> str`

Loads the dataset, profiles it, and returns a JSON profile. `data_type="auto"`
defers to ADEngine's type sniffer; otherwise pass a concrete type such as
`"tabular"` or `"time_series"`.

Example response:

```json
{
  "data_type": "tabular",
  "n_samples": 120,
  "n_features": 5,
  "has_nan": false,
  "dtype": "float64",
  "dimensionality_class": "low"
}
```

### `plan_detection(data_profile: str, priority: str = "balanced", constraints: str = "") -> str`

`data_profile` must be a JSON object string, usually the output of
`profile_data`. `constraints`, when non-empty, must also be a JSON object string.

Example call payloads:

```json
{"data_type":"tabular","n_samples":120,"n_features":5,"dimensionality_class":"low"}
```

```json
{"exclude_detectors":["IForest"]}
```

Error returns:

```json
{"error":"Invalid JSON","details":"..."}
{"error":"data_profile must be a JSON object"}
{"error":"constraints must be a JSON object"}
```

### `build_detector(plan: str) -> str`

Returns constructor metadata without fitting a detector:

```json
{
  "detector_name": "IForest",
  "class_path": "pyod.models.iforest.IForest",
  "params": {"contamination": 0.1},
  "preset": null,
  "code_snippet": "from pyod.models.iforest import IForest\nclf = IForest(contamination=0.1)"
}
```

Validation errors are JSON objects:

- `Invalid JSON` or `plan must be a JSON object`.
- `Unknown detector` for a name not present in the knowledge base.
- `params must be a JSON object`.
- `Preset only valid for EmbeddingOD`.
- `Unknown preset` when not `for_text` or `for_image`.
- `Invalid parameter name` when a param key is not a safe Python identifier or is
  a keyword.

### Knowledge tools

```text
list_detectors(data_type: str = "", status: str = "shipped")
explain_detector(name: str)
compare_detectors(names: str = "", data_type: str = "tabular", top_k: int = 3)
get_benchmarks(benchmark: str = "all")
```

- `list_detectors` returns a JSON array. Empty `data_type` means all data types.
  `status="all"` includes planned entries; default `shipped` filters to usable
  detectors.
- `explain_detector` returns a detector record or `{"error":"Unknown detector ..."}`.
- `compare_detectors` accepts comma-separated names. Empty `names` selects
  benchmark-ranked top-k detectors for data types with ranking evidence and
  catalog-order fallback otherwise.
- `get_benchmarks` returns benchmark metadata. Use `"all"` for every bundled
  benchmark.

### `run_detection(data_path: str, plan: str, test_data_path: str = "") -> str`

Wraps `ADEngine.run_detection`.

- Parses `plan` JSON into a DetectionPlan object.
- Loads train and optional test data from files.
- Fits the detector and returns a JSON-serializable result.
- Omits the fitted `detector` object.
- Converts NumPy arrays to lists for `scores_train`, `labels_train`,
  `scores_test`, and `labels_test`.

Common error returns:

```json
{"error":"Invalid plan JSON","details":"..."}
{"error":"plan must be a JSON object"}
{"error":"Failed to load training data","details":"..."}
{"error":"Failed to load test data","details":"..."}
{"error":"Detection failed","type":"ValueError","details":"..."}
```

### `analyze_results(result: str, data_path: str = "", top_k: int = 10) -> str`

Pass the JSON returned by `run_detection`. Optional `data_path` enables
feature-level analysis. Error returns include `Invalid result JSON`,
`Failed to load data`, and `Analysis failed` with exception type/details.

### `explain_findings(result: str, indices: str = "", top_k: int = 5, data_path: str = "") -> str`

Pass the JSON returned by `run_detection`. `indices` is a comma-separated list of
zero-based row indices such as `"0,5,12"`; leave it empty for top-k anomalies.
Optional `data_path` enables feature-level explanations.

Error returns include:

```json
{"error":"Invalid result JSON"}
{"error":"Invalid indices","details":"..."}
{"error":"Failed to load data","details":"..."}
{"error":"Explanation failed","type":"...","details":"..."}
```

## Safe availability probe pattern

Use this pattern when an agent needs to check MCP without starting it:

```python
import importlib.util
import pyod.mcp_server as m

mcp_parent_available = importlib.util.find_spec("mcp") is not None
fastmcp_class = m._check_mcp()          # returns FastMCP or None
registered_tool_names = [fn.__name__ for fn in m._TOOL_FUNCTIONS]
```

Only call `m.main()` or `pyod mcp serve` when the user explicitly wants a live
server process.
