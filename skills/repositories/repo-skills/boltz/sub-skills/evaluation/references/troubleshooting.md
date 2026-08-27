# Troubleshooting

## Updated Boltz-2 Evaluation Assets Are Missing

Symptom: the user asks for official Boltz-2 evaluation commands or benchmark files, but the repo only has placeholder text.

Resolution: state that updated Boltz-2 evaluation files, setup, and scripts are documented as coming soon. Use local confidence/affinity summaries when possible, or ask the user to provide the newer benchmark assets.

## OpenStructure Is Missing or the Version Differs

Symptom: structural benchmark reproduction cannot run, or results differ from published legacy numbers.

Resolution: the legacy benchmark script requires OpenStructure 2.8.0 for reproduction consistency and shells out through Docker. Confirm Docker access, image availability, mounted paths, and the exact OpenStructure version before treating metric differences as model differences.

## Benchmark Folder Layout Does Not Match

Symptom: prediction outputs exist, but evaluation fails with missing model files, missing target files, or empty aggregations.

Checklist:

- predictions are under the expected model/testset folder and target names match the target files;
- reference structures exist under the matching `targets/<dataset>/` folder;
- generated evaluation JSONs exist under `evals/<dataset>/<tool>/` before aggregation;
- CASP target capitalization and PDB/test lowercase naming rules match the script expectations;
- Boltz prediction subfolders contain `confidence_<target>_model_<n>.json` when top-1 selection is needed.

If only `predictions/<input-name>/` output exists, use output interpretation rather than benchmark reproduction.

## Metric Columns Do Not Match

Symptom: aggregation reports missing metrics, different ligand counts, or incomparable rows.

Resolution: compare only metrics present for every tool/target combination being reported. For ligand and interface metrics, preserve the assigned-score count and skip comparisons where counts differ. For CSV summaries, verify whether the file is long-form (`metric,value`) or wide-form numeric columns.

## CASP/PDB Overlap Caveats

Symptom: the user wants a fairness claim for CASP or PDB benchmark numbers.

Resolution: document the authors' overlap filtering for their own validation set, but avoid stronger claims about closed-source model validation sets. AF3 and Chai-1 training/validation details were not fully public in the legacy evaluation evidence, so absence of overlap cannot be guaranteed.

## Top-1 and Oracle Are Confused

Symptom: a report presents oracle results as if they are normal single-sample model performance.

Resolution: label top-1 and oracle separately. Top-1 uses the confidence-selected sample. Oracle is the best of multiple samples for a metric and should be treated as an upper-bound diagnostic.

## Affinity Value and Binary Probability Are Mixed

Symptom: `affinity_pred_value` and `affinity_probability_binary` are averaged or ranked together.

Resolution: keep them separate. `affinity_probability_binary` estimates binder likelihood from 0 to 1 and is appropriate for binder-vs-decoy ranking. `affinity_pred_value` is an affinity value on a `log10(IC50)` scale using micromolar IC50, where lower means stronger predicted binding and the field is most appropriate for comparing active binders.

## Physical-Similarity Script Cannot Run

Symptom: physical-validity evaluation fails because caches, chemistry assets, or source paths are unavailable.

Resolution: treat the legacy physical-similarity script as reference-only unless the user has prepared the required CCD/molecule cache, prediction folders, and chemistry/structure dependencies. Do not reuse environment-specific absolute paths from the source script.

## Summary Script Finds No Records

Symptom: `boltz_evaluation_summary.py` exits with no records.

Checklist:

- pass the directory that contains per-input prediction folders, commonly `out/predictions`, not the parent output root unless recursive search is intended;
- confirm files are named like `confidence_*.json` or `affinity_*.json`;
- confirm JSON values are numeric at the top level, or add `--include-nested` for nested numeric maps;
- for CSVs, confirm numeric columns exist or long-form `metric,value` columns are present;
- use `--metric <name>` to restrict summaries only after confirming the exact field names.
