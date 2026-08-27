# Deepchecks Result API Reference

## Purpose

Read this when the user needs to export, display, serialize, reconstruct, or programmatically gate a Deepchecks result object. The APIs below are verified for Deepchecks result classes and should be used after a check or suite has already been run.

## Result object roles

| Object | Created by | Use it for |
|---|---|---|
| `deepchecks.core.CheckResult` | A single check's `.run(...)` call | Inspect one check's value/display, save one check as HTML, serialize one check, or call `passed_conditions()` for check-level assertions. |
| `deepchecks.core.SuiteResult` | A suite's `.run(...)` call | Inspect a collection of check results, save one report, serialize the suite, identify not-run checks, and call `passed()` for suite-level gates. |
| `deepchecks.core.CheckFailure` | A check that could not run inside a suite | Preserve failure metadata and exception text. It is not a passing/failing condition result unless the gate explicitly treats not-run checks as failures. |

## Core method signatures

| Method | Verified signature | Primary use |
|---|---|---|
| `SuiteResult.save_as_html` | `(self, file=None, as_widget=True, requirejs=True, unique_id=None, connected=False, **kwargs)` | Save a full suite report to HTML. |
| `CheckResult.save_as_html` | `(self, file=None, unique_id=None, show_additional_outputs=True, as_widget=True, requirejs=True, connected=False, **kwargs)` | Save one check report to HTML; optionally hide additional outputs. |
| `SuiteResult.to_json` | `(self, with_display=True, **kwargs)` | Serialize a suite result to a JSON string. |
| `CheckResult.to_json` | `(self, with_display=True, **kwargs) -> str` | Serialize one check result to a JSON string. |
| `SuiteResult.passed` | `(self, fail_if_warning=True, fail_if_check_not_run=False) -> bool` | Gate a suite by condition statuses and, optionally, check failures/not-run checks. |
| `CheckResult.passed_conditions` | `(self, fail_if_warning=True) -> bool` | Gate one check by its conditions. |
| `deepchecks.utils.json_utils.from_json` | `(json_dict)` where `json_dict` is a JSON string or decoded dict | Reconstruct a `SuiteResult`, `CheckResult`, or `CheckFailure` from JSON produced by Deepchecks `to_json`. |

Related helpers on `SuiteResult`:

- `get_not_passed_checks(fail_if_warning=True)` returns condition-bearing checks that do not pass.
- `get_passed_checks(fail_if_warning=True)` returns condition-bearing checks that pass.
- `get_not_ran_checks()` returns `CheckFailure` records for checks that could not run.
- `SuiteResult.from_json(json_res)` reconstructs suite JSON, but `deepchecks.utils.json_utils.from_json` is the safer common entry point when the caller does not know whether the JSON is a check or suite result.

## HTML export guidance

Use HTML when a human needs the original visual report.

```python
html_path = result.save_as_html("deepchecks_report.html", connected=False)
print(f"Deepchecks report saved to {html_path}")
```

Practical details:

- If `file` is omitted, Deepchecks writes `output.html`.
- When `file` is a string and the target already exists, Deepchecks chooses a new non-conflicting filename; capture the returned value instead of assuming the exact path.
- `connected=False` embeds JavaScript assets for offline viewing. Use `connected=True` only when the viewer can load CDN assets.
- `as_widget=True` uses the widget serializer; `as_widget=False` uses the non-widget HTML serializer and is often simpler in headless or documentation builds.
- For a single `CheckResult`, pass `show_additional_outputs=False` when the condition table is enough and the full plots/tables are too large for the artifact.
- Save HTML before raising an assertion or exiting non-zero so CI artifact upload still has a report to preserve.

## JSON export and reconstruction

Use JSON when a later Python process needs to inspect the result, reconstruct the display object, or apply a structural CI gate.

```python
from pathlib import Path
from deepchecks.utils.json_utils import from_json

json_text = result.to_json(with_display=False)
Path("deepchecks_result.json").write_text(json_text, encoding="utf-8")

recovered = from_json(json_text)
# recovered is a SuiteResult, CheckResult, or CheckFailure depending on the JSON.
```

JSON shape to expect:

- `SuiteResult.to_json(...)` returns a JSON string whose decoded object has `type: "SuiteResult"`, `name`, and `results`.
- Each suite item is usually a `CheckResult` with `type: "CheckResult"`, `check`, `header`, `value`, `conditions_results`, and `display`; a not-run check is a `CheckFailure` with `exception` text.
- `conditions_results` rows contain `Status`, `Condition`, and `More Info`. `Status` values are `PASS`, `WARN`, `FAIL`, or `ERROR`.
- `with_display=True` keeps display payloads and can make JSON much larger. Use it when later `from_json(...).show()` or `save_as_html(...)` matters; use `with_display=False` for smaller CI-only payloads.

Limitations:

- JSON reconstruction does not recover the original data, model, or external service state; it reconstructs the result/report object and metadata saved by Deepchecks.
- Custom or very large display payloads can make JSON slow or unwieldy. Prefer HTML for human inspection and `with_display=False` JSON for gates.
- For long-lived archival, keep the Deepchecks version reasonably aligned between writer and reader because result JSON is produced by Deepchecks serializers rather than by a separately versioned interchange standard.
- The bundled [CI result gate script](../scripts/deepchecks_ci_result_gate.py) evaluates the visible JSON structure without rerunning Deepchecks. It is intentionally conservative and cannot perfectly reproduce every behavior of the live result object.

## Display guidance

Use display methods only in interactive contexts:

```python
result.show()                 # notebook/interactive default
result.show_in_iframe()       # iframe fallback for difficult notebook/cloud displays
result.show_not_interactive() # static display; needs image export support for Plotly figures
result.show_in_window()       # local GUI window; requires optional GUI packages
```

For non-interactive CI or batch jobs, prefer `save_as_html(...)` and upload the file as an artifact rather than calling `show()`.
