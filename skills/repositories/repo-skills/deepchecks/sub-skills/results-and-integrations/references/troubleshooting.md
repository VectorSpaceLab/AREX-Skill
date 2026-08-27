# Results and Integrations Troubleshooting

## Purpose

Use this reference for result display/export failures, JSON reconstruction problems, CI gate surprises, and optional integration dependency issues. Route package-wide installation or global import failures to the root Deepchecks troubleshooting reference.

## Quick diagnosis table

| Symptom | Likely cause | What to do |
|---|---|---|
| Notebook cell shows a blank result or widget error | Missing or incompatible Jupyter widget/Plotly support | Try `result.show_in_iframe()`. If the user only needs the report, use `result.save_as_html("report.html", connected=False)` and open/upload the HTML. |
| `show_in_window()` fails or logs missing GUI packages | Optional PyQt GUI dependencies are not installed or the environment is headless/cloud-hosted | Do not debug GUI display in CI. Save HTML instead. If the user specifically wants a local GUI, install the optional GUI packages in their environment. |
| `show_not_interactive()` cannot render static plots | Static Plotly image export support is missing | Save interactive HTML instead, or install the optional static-image dependency if the user needs static display. |
| HTML file name differs from the requested name | Deepchecks avoids overwriting an existing filename by creating a non-conflicting name | Always capture the return value of `save_as_html(...)` and report/upload that path. |
| HTML report fails to load offline | The report was saved with external assets expected, or the viewer blocks scripts | Save with `connected=False`. For headless pipelines, prefer `as_widget=False` if widget output is causing issues. |
| JSON file is very large | `to_json(with_display=True)` included display payloads | For CI gates use `to_json(with_display=False)`. Save HTML separately for human review. |
| `from_json(...)` raises an expected-type error | The JSON was not produced by Deepchecks `to_json`, is truncated, or has an unsupported `type` field | Recreate the artifact from `CheckResult.to_json(...)` or `SuiteResult.to_json(...)`. Confirm the top-level decoded JSON object has `type` equal to `CheckResult`, `CheckFailure`, or `SuiteResult`. |
| JSON reconstruction displays but does not let you rerun checks | Result JSON does not contain the original dataset, model, or service state | Treat `from_json(...)` as report/result reconstruction only. Rerun the original suite when a fresh validation decision is needed. |
| `suite_result.passed()` passes despite a check that did not run | `fail_if_check_not_run` defaults to `False` | For conservative CI use `suite_result.passed(fail_if_warning=True, fail_if_check_not_run=True)`. |
| A warning condition fails CI | `fail_if_warning=True` treats `WARN` as not passing | Keep this default for strict gates. Use `fail_if_warning=False` only when the user intentionally accepts warnings. |
| A result with no conditions appears to pass | `passed_conditions()` and `passed()` evaluate configured conditions; no conditions means no explicit gate | Add conditions to the check/suite for CI. The bundled JSON gate fails a zero-condition artifact by default unless `--allow-no-conditions` is passed. |
| Airflow DAG import fails | Airflow or provider packages are not installed, or connection IDs are missing | Keep Airflow as a project-specific integration. Install the required providers and configure connections outside this skill; do not store credentials in code. |
| S3 upload fails | Missing bucket permissions, wrong key, missing provider, network issue, or credential problem | Validate the object-storage connection separately. Save the local HTML/JSON first so the validation artifact exists even if upload fails. |
| H2O or Hugging Face example cannot run in CI | External runtime, model download, tokenizers, GPU, large data, or network side effects are required | Use precomputed predictions/probabilities or a small local adapter fixture. Do not run credential/network-heavy integration examples as default CI checks. |

## CI result gate script

The bundled script [../scripts/deepchecks_ci_result_gate.py](../scripts/deepchecks_ci_result_gate.py) exits with:

- `0`: JSON structure passed the selected gate.
- `1`: JSON was valid, but conditions/check failures/no-conditions policy failed the gate.
- `2`: the file could not be read, JSON was malformed, or the structure was unsupported.

Useful invocations:

```bash
# From the generated Deepchecks skill root.
# Strict/default gate: warnings fail, not-run checks fail, no-condition artifacts fail.
python sub-skills/results-and-integrations/scripts/deepchecks_ci_result_gate.py deepchecks_result.json

# Accept warnings but still fail FAIL/ERROR statuses and check failures.
python sub-skills/results-and-integrations/scripts/deepchecks_ci_result_gate.py --allow-warnings deepchecks_result.json

# Emit a machine-readable summary to stdout.
python sub-skills/results-and-integrations/scripts/deepchecks_ci_result_gate.py --emit-json-summary deepchecks_result.json
```

If the script reports malformed JSON:

1. Confirm the artifact contains only the JSON string/object, not log lines before or after it.
2. Confirm it was written from `result.to_json(...)`, not from `repr(result)` or a printed notebook cell.
3. If the file contains a quoted JSON string, the script attempts one nested decode; if that still fails, rewrite the artifact as raw JSON text.
4. If the error is a missing or unsupported `type`, reconstruct the artifact from a current Deepchecks `CheckResult` or `SuiteResult`.

If the script reports no conditions:

- A Deepchecks result can be useful for inspection without conditions, but it is not a reliable CI gate by itself.
- Add explicit conditions to the checks or suite, or use `--allow-no-conditions` only when another test already enforces pass/fail criteria.

## Choosing between live gating and JSON gating

Prefer live gating when possible:

```python
assert suite_result.passed(fail_if_warning=True, fail_if_check_not_run=True)
```

Use JSON gating when:

- A separate job produced a Deepchecks JSON artifact.
- The data/model required to rerun Deepchecks is no longer available in the gate job.
- The user accepts that structural JSON gating is conservative and may not reproduce every custom result variant.

Always pair JSON gating with an HTML artifact when humans need to inspect plots, tables, or condition context.

## Optional integration dependency boundaries

This sub-skill intentionally does not install or run optional integration stacks:

- Airflow/S3 needs Airflow, provider packages, configured connections, network, and write permissions.
- H2O may require a local or remote H2O cluster and adapter code to expose predictions in Deepchecks-friendly shapes.
- Hugging Face may require `transformers`, model weights, tokenizers, datasets, and optional GPU resources.
- Static display or GUI display may require optional visualization packages.

When those dependencies are missing, preserve the Deepchecks result locally first, then ask the user whether they want to install/run the external integration. Do not make credentialed uploads, service startup, model downloads, or destructive writes part of the default result-export workflow.
