# CLI and Container Reference

Use this reference when the task asks for shell commands, batchable CellTypist invocation, or container execution.

## CLI Verification

Check the command without model downloads or annotation:

```bash
celltypist --help
python scripts/celltypist_cli_smoke.py
```

`celltypist_cli_smoke.py` validates that the command exposes expected options such as `--indata`, `--model`, `--mode`, `--majority-voting`, `--show-models`, and `--update-models`.

## Annotation Command Pattern

Create the output directory before running the CLI:

```bash
mkdir -p results
celltypist --indata query_counts.csv --model local_model.pkl --outdir results --prefix query_ --quiet
```

Important flags:

- `--indata`: path to `.csv`, `.txt`, `.tsv`, `.tab`, `.mtx`, `.mtx.gz`, or `.h5ad` input.
- `--model`: built-in model name or local model path. Use `./local_model.pkl` for strict offline local loading.
- `--transpose-input`: use when the file is gene-by-cell instead of cell-by-gene.
- `--gene-file` and `--cell-file`: required sidecar files for Matrix Market input.
- `--mode best_match`: default single-label prediction.
- `--mode prob_match --p-thres 0.5`: multi-label probability-match mode.
- `--majority-voting`: run over-clustering and majority voting when enough cells are present.
- `--over-clustering`: file or AnnData metadata key used with majority voting.
- `--use-GPU`: optional RAPIDS-based over-clustering path; CPU fallback applies when `rapids-singlecell` is missing.
- `--xlsx`: write one Excel workbook instead of separate CSV files.
- `--plot-results`: write UMAP figures after annotation.
- `--show-models` and `--update-models`: model inventory/download operations that can require network access.

## Docker and Singularity Notes

The public CellTypist documentation describes container usage with the image `quay.io/teichlab/celltypist:latest`.

Docker pattern:

```bash
docker run --rm -it \
  -v /path/to/data:/data \
  quay.io/teichlab/celltypist:latest \
  celltypist --indata /data/query_counts.csv --model Immune_All_Low.pkl --outdir /data/output
```

For a custom model cache or local models, mount the model directory as well and pass an explicit path:

```bash
docker run --rm -it \
  -v /path/to/data:/data \
  -v /path/to/models:/models \
  quay.io/teichlab/celltypist:latest \
  celltypist --indata /data/query_counts.csv --model /models/local_model.pkl --outdir /data/output
```

Singularity pattern:

```bash
singularity run \
  -B /path/to/data:/data \
  celltypist-latest.sif \
  celltypist --indata /data/query_counts.csv --model Immune_All_Low.pkl --outdir /data/output
```

## When to Use Python Instead

Prefer the Python API when:

- The input is already an in-memory `AnnData` object.
- The workflow needs custom pre/post-processing.
- The user wants `AnnotationResult.to_adata()` or `celltypist.dotplot()` inside a notebook or pipeline.
- You need to pass a loaded `Model` object created by conversion, subsetting, or custom training.

Route Python prediction setup to `sub-skills/annotation-workflows/SKILL.md`.
