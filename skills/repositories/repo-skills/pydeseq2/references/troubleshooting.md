# Cross-Cutting Troubleshooting

## Install Or Import Fails

Symptom: `ModuleNotFoundError: No module named 'pydeseq2'`.

Likely causes: PyDESeq2 is not installed in the active Python environment, or the command is running under a different Python than the one used for installation.

Recovery:

1. Run `python -m pip install pydeseq2` in the active environment.
2. Run `python scripts/check_pydeseq2_environment.py` from the skill root.
3. If multiple Python environments exist, run `python -c "import sys; print(sys.executable)"` in the same shell where the analysis will run.

## Dependency Conflicts

Symptom: imports fail for `anndata`, `formulaic`, `formulaic_contrasts`, `numpy`, `pandas`, `scipy`, `sklearn`, or `matplotlib`, or `python -m pip check` reports incompatible requirements.

Recovery:

- Use a clean environment with Python `>=3.11`.
- Reinstall PyDESeq2 with dependencies: `python -m pip install --upgrade pydeseq2`.
- Avoid mixing package managers in the same environment unless the user explicitly wants that setup.
- Run `python -m pip check` before analyzing results.

## Input Data Looks Valid But `DeseqDataSet` Fails

Symptoms include:

- `NaNs are not allowed in the count matrix.`
- `The count matrix should only contain numbers.`
- `The count matrix should only contain integers.`
- `The count matrix should only contain non-negative values.`
- AnnData index-alignment errors.
- `NaNs are not allowed in the design.`

Recovery:

1. Route to `sub-skills/data-io-validation/SKILL.md`.
2. Run `python sub-skills/data-io-validation/scripts/validate_pydeseq2_inputs.py --counts-csv counts.csv --metadata-csv metadata.csv --design '~condition' --orientation auto`.
3. Fix orientation, sample indexes, count values, missing metadata, or formula columns before modeling.

## The Fit Runs Slowly Or Uses Too Many CPUs

Symptoms: joblib starts many workers, the machine becomes overloaded, or a small smoke test takes longer than expected.

Recovery:

- Use `DefaultInference(n_cpus=1)` for examples, tests, and troubleshooting.
- Increase `n_cpus` only after confirming the user wants parallelism.
- For wide datasets or memory pressure, route to `sub-skills/dea-workflows/SKILL.md` and consider `low_memory=True`.

## Plotting Fails In Headless Sessions

Symptoms: MA plot code fails because an interactive display backend is unavailable.

Recovery:

- Save plots to a file using `plot_MA(save_path='ma.png')`.
- In scripts, set a non-interactive backend before importing `pyplot`, for example `matplotlib.use('Agg')`.
- Route plot-specific ordering issues to `sub-skills/statistics-and-results/SKILL.md`.

## Results Are Empty Or Full Of `NaN`

Likely causes:

- Genes have all-zero counts.
- Cook's filtering removed p-values for outlier genes.
- Independent filtering changed adjusted p-values.
- The dataset was not fitted before `DeseqStats`.

Recovery:

- Check input filtering in `sub-skills/data-io-validation/SKILL.md`.
- Check fit and outlier behavior in `sub-skills/dea-workflows/SKILL.md`.
- Check p-value and result-column behavior in `sub-skills/statistics-and-results/SKILL.md`.

## Formula And Contrast Confusion

Symptoms:

- Factor names or reference levels are rejected.
- List contrasts fail after using a precomputed design matrix.
- LFC shrinkage coefficient names do not match expectations.

Recovery:

- Formula-based designs can use list contrasts such as `["condition", "B", "A"]`.
- Direct design matrices generally require numeric contrast vectors whose length matches the design matrix columns.
- Inspect `dds.obsm["design_matrix"].columns` for coefficient names before `lfc_shrink(coeff=...)`.
- Route details to `sub-skills/statistics-and-results/SKILL.md`.

## Requested DESeq2 Feature Is Missing

PyDESeq2 broadly mirrors common DESeq2 defaults for Python workflows, but it is not a full drop-in replacement for every DESeq2 feature. If a requested analysis option is not exposed in `DeseqDataSet`, `DeseqStats`, or the documented preprocessing utilities, state the limitation clearly and suggest either a supported PyDESeq2 route or using R DESeq2 for that specific feature.
