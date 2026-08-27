# CellTypist Troubleshooting

Use this root guide for cross-cutting CellTypist failures. For workflow-specific problems, route to the nearest sub-skill troubleshooting reference.

## Install or Import Fails

Symptoms:
- `ImportError` for `celltypist`, `scanpy`, `anndata`, `leidenalg`, or `sklearn`.
- The `celltypist` command is missing after installation.

Likely causes:
- CellTypist is not installed in the active Python environment.
- Runtime dependencies from the package metadata are missing or broken.
- The shell is using a different Python environment than the one where the package was installed.

Recovery:
- Install with `pip install celltypist` or `conda install -c bioconda -c conda-forge celltypist`.
- Verify with `python -c "import celltypist; print(celltypist.__version__)"` and `celltypist --help`.
- Run the bundled CLI helper with the same Python environment: `python scripts/celltypist_cli_smoke.py`.

## Model Cache or Network Surprises

Symptoms:
- A seemingly simple model listing starts downloading files.
- `Model.load()` with no argument fails offline.
- Built-in model names work on one machine but not another.

Likely causes:
- CellTypist stores models under `CELLTYPIST_FOLDER/data/models` or a default `.celltypist/data/models` cache.
- `get_all_models()`, `get_default_model()`, and `models_description()` can fetch model metadata or model files when the cache is empty.

Recovery:
- For offline work, pass an explicit local model path such as `./model.pkl` to `Model.load()` or `celltypist.annotate()`.
- Inspect cache state without network using `sub-skills/model-management/scripts/model_cache_check.py`.
- Set `CELLTYPIST_FOLDER` before importing `celltypist.models` if the cache must be redirected.

## Data Format or Feature Matching Fails

Symptoms:
- `No features overlap with the model. Please provide gene symbols`.
- Warnings say the input looks gene-by-cell or not like raw counts.
- `.h5ad` input raises an expression normalization error.

Likely causes:
- Query genes are Ensembl IDs while the model expects gene symbols, or the species does not match.
- Count-table orientation is wrong.
- Matrix Market input is missing sidecar gene/cell files.
- AnnData `.X` or `.raw.X` is not log1p normalized to 10,000 counts per cell.

Recovery:
- Read `sub-skills/annotation-workflows/references/data-formats.md` before annotation.
- Use `--transpose-input` or `transpose_input=True` when the input is gene-by-cell.
- Provide both `gene_file` and `cell_file` for `.mtx` input.
- Convert or choose a model whose features match the query namespace using `sub-skills/model-management/references/conversion-and-subsetting.md`.

## Optional GPU Packages Are Missing

Symptoms:
- Majority-voting over-clustering logs that `rapids_singlecell` is missing and falls back to CPU.
- Training with `use_GPU=True` warns that `cuml` is not installed.

Likely causes:
- GPU-specific packages are optional and not installed by default.
- SGD training ignores GPU training paths.

Recovery:
- Use CPU behavior unless the user explicitly needs GPU acceleration.
- Install RAPIDS components only in a compatible CUDA/RAPIDS environment.
- For custom training, read `sub-skills/training-and-custom-models/references/troubleshooting.md` before enabling `use_GPU=True`.

## Output or Plotting Fails

Symptoms:
- `to_table()` or CLI export says the output folder does not exist.
- `to_adata(insert_conf_by="majority_voting")` fails.
- `celltypist.dotplot()` cannot find `majority_voting` or reference labels.

Likely causes:
- CellTypist expects output folders to exist before writing.
- Majority voting was not run, so the result has only `predicted_labels`.
- Dotplot defaults to `use_as_prediction="majority_voting"`.

Recovery:
- Create output directories before export.
- Use `use_as_prediction="predicted_labels"` for raw prediction dotplots.
- Use `sub-skills/visualization-and-results/scripts/result_shape_check.py` to validate result files before plotting.
