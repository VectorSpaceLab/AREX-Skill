# Results Troubleshooting

Use this matrix after a result JSON, gather command, TSV, or analysis artifact looks incomplete, inconsistent, or hard to interpret. Stay read-only unless the user explicitly asks for cleanup; rerunning simulations belongs in the CLI workflow skill.

## Quick Triage

1. Confirm the protocol family: RBFE/RHFE, ABFE, SepTop, or Plain MD.
2. Count result JSONs before inspecting trajectories. Result summaries usually require JSON files, not `.nc`, `.xtc`, `.chk`, or PDB artifacts.
3. Decode JSON with gufe when available; otherwise use a diagnostic parser to identify corrupted files and missing top-level fields.
4. Check `estimate`, `uncertainty`, `unit_results`, and `protocol_result` before interpreting plots.
5. For network results, choose the correct `gather*` command and report type before deciding a result is missing.

## Failure Modes

| Symptom | Likely cause | Recovery steps |
| --- | --- | --- |
| Result JSON has no `estimate` or `estimate` is `null`. | Simulation or analysis failed, JSON is not an OpenFE result, or the protocol does not produce free energy estimates. | Inspect `unit_results` for exceptions; summarize status with the helper; route rerun/resume decisions to `cli-workflows`. |
| Result JSON has no `uncertainty` or `uncertainty` is `null`. | Failed analysis, incomplete result, or unsupported result type. | Treat as failed for gather-style summaries; inspect analysis unit outputs and exceptions. |
| `unit_results` is empty. | Execution did not complete or wrote a malformed/incomplete result. | Report as incomplete; look for logs in the corresponding shared unit directory; do not infer values from trajectory files. |
| Every unit result contains `exception`. | All units failed. | Extract exception summaries; do not include the edge as successful; route execution fixes to `cli-workflows` or `protocols` depending on cause. |
| `openfe gather` says no result JSON files found. | Wrong directory, JSON files do not end in `.json`, compressed fixtures, or files are not result JSONs with an `estimate` key near the start. | Point gather at the repeat root; ensure result summaries are real plain `.json` files; use the bundled helper for `.json.gz` diagnostics only. |
| Missing runs / missing legs warning. | RBFE/RHFE edge lacks required `complex`/`solvent` or `solvent`/`vacuum` legs. | Use `--report raw` to list present legs; use `--allow-partial` only when the user accepts omitted edges. |
| `dg` MLE fails because the network is disconnected. | Failed/missing edges break connectivity. | Produce `ddg` or `raw` report instead; identify missing edges; route new edge planning to `network-planning`. |
| `dg` MLE fails with too few edges. | Fewer than the required connected pairwise edges for MLE. | Use `ddg`/`raw` reports; gather more completed edges before trying MLE. |
| TSV rows show `Error`. | Gather found a failed result or a missing/invalid leg. | Keep the row as failed; explain which leg/result failed rather than averaging it away. |
| ABFE report lacks expected complex/solvent contribution. | Missing leg JSON, failed analysis unit, or unexpected protocol/unit schema. | Use `gather-abfe --report raw`; inspect `unit_results` source keys for analysis outputs and `simtype` fields. |
| SepTop current and legacy TSVs differ. | SepTop output schema changed across OpenFE versions; gather has compatibility branches. | Identify source version if known; compare within the same schema generation when possible; avoid mixing legacy/current result sets in one scientific comparison. |
| SepTop output missing complex or solvent leg. | One leg failed, was not run, or result path selection omitted it. | Use `gather-septop --report raw`; check for both `complex` and `solvent` analysis outputs and standard-state correction fields. |
| JSON decoding fails. | Corrupted/truncated file, compressed file passed to a plain JSON parser, or non-JSON artifact. | Try the bundled helper, which supports `.json` and `.json.gz`; report parse errors with filenames; do not edit original outputs. |
| Values print with unit objects instead of floats. | OpenFE/gufe decoded unit-bearing quantities. | Preserve value and unit; convert only with explicit target units. |
| Huge output directory makes summary slow. | Directory contains trajectories/checkpoints and analysis artifacts. | Summarize result JSONs only; skip `.nc`, `.xtc`, `.chk`, `.pdb`, `.npz`, and images unless diagnosing convergence. |
| Analysis plots exist but result JSON failed. | Some artifacts may have been written before final aggregation failed. | Treat plots as diagnostic context, not proof of a valid estimate. |
| `structural_analysis.json` is expected but absent. | Current outputs store structural analysis arrays in `structural_analysis.npz`. | Look for `structural_analysis.npz` and plot PNGs; do not require legacy JSON. |
| Storage client raises missing/changed external resource errors. | Metadata and external store are out of sync. | Run storage audit methods such as `find_missing_files()` if available; avoid `allow_changed=True` unless the user approves accepting changed artifacts. |

## Choosing `raw`, `ddg`, and `dg`

- Use `raw` when diagnosing missing repeats, failed legs, or inconsistent per-leg values.
- Use `ddg` for pairwise relative results when the network is incomplete but useful edges remain.
- Use `dg` only when the relative network is sufficiently connected for MLE and the user wants ligand-level absolute estimates.
- Use `--allow-partial` for exploratory summaries, not for final scientific reporting without documenting omitted edges; for ABFE/SepTop, remember the option is accepted but the current aggregators still need enough complete leg data for the selected report.

## Mixed Successful and Failed RBFE JSONs

For a mixed set:

1. Summarize every JSON filename, parse status, estimate, uncertainty, inferred leg, and exception count.
2. Mark rows with missing estimate/uncertainty or all-exception unit results as failed.
3. Run or recommend `openfe gather --report raw --tsv` to expose per-leg failures.
4. Use `openfe gather --report ddg --allow-partial --tsv` only to preview usable edges.
5. Explain omitted edges by missing leg type (`complex`, `solvent`, or `vacuum`) or failed result status.

## Repeat and Partial-Result Warnings

Repeated calculations are independent evidence for uncertainty. If repeat folders are partial:

- Do not average by hand unless the user asks for exploratory diagnostics.
- Do not mix overwritten repeats with independent repeats.
- Treat a single completed repeat as less robust than multiple independent repeats, even if a gather command can produce a table.
- For final reporting, document which repeats were included and which were missing or failed.

## Large Artifact Handling

Most user questions about estimates do not require loading trajectories or checkpoints. Prefer this order:

1. Result JSON summary.
2. Gather TSV summary.
3. Analysis PNG/NPZ inspection for convergence or structural concerns.
4. Trajectory/checkpoint inspection only when the task explicitly asks for structural/trajectory diagnostics.

Skip or defer large binary artifacts when producing a quick report; note that they are not needed for `estimate`/`uncertainty` summaries.
