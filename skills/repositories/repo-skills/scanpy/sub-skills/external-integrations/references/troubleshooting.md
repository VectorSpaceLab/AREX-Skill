# External Integration Troubleshooting

Use this reference when optional Scanpy integrations fail at import time, runtime, or environment-planning time. Prefer targeted fixes over broad extra installation.

## Optional Import Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `ImportError` with note `Please install bbknn` | `sce.pp.bbknn` called without BBKNN | Install `scanpy[bbknn]` or `bbknn`. |
| `Please install mnnpy` | `sce.pp.mnn_correct` imports `mnnpy` lazily | Install `mnnpy` only if MNN correction is required. |
| `Please install scanorama` | `sce.pp.scanorama_integrate` called without Scanorama | Install `scanpy[scanorama]` or `scanorama`. |
| `Please install magic-impute` or MAGIC version error | `sce.pp.magic` called without a compatible MAGIC package | Install `scanpy[magic]`; require `magic-impute>=2.0.4` from the public extra even though the wrapper's minimum check is lower. |
| `Please install phate` | `sce.tl.phate` or `sce.pl.phate` called without PHATE | Install `phate`. |
| `Please install palantir` | `sce.tl.palantir` or `palantir_results` checks Palantir | Install `palantir`. |
| `Please install trimap` | `sce.tl.trimap` called without TriMap | Install `trimap`. |
| `Please install sc-sam` | `sce.tl.sam` imports `samalg` | Install the upstream SAM package only for SAM workflows. |
| `please install the latest release of phenograph` | Missing or old `phenograph` | Install or upgrade `phenograph>=1.5.3`; also verify Louvain/Leiden dependencies if selected. |
| `Please install harmonyTS` | `sce.tl.harmony_timeseries` imports `harmony` | Install `harmonyTS`; do not confuse with core `sc.pp.harmony_integrate`. |
| `Please install wishbone` | Wishbone wrapper or plotter imports Wishbone | Install `wishbone` and ensure trajectory prerequisites are present. |
| `You need to install pypairs` or version error | `sandbag`/`cyclone` missing `pypairs>=3.2.0` | Install/upgrade `pypairs`. |
| `Please install cellbrowser` | Cell Browser export called without exporter | Install `cellbrowser` only for that export route. |

Use `scripts/check_scanpy_optional_deps.py --feature <name> --json` to identify missing modules without importing heavy packages or changing the environment.

## Choosing Narrow Extras

- For Leiden plus Seurat v3 HVG plus plotting, recommend targeted extras such as `scanpy[leiden,skmisc,plotting]`; do not add BBKNN, Scanorama, MAGIC, Dask, or Scrublet unless requested.
- For external imputation only, install `scanpy[magic]` rather than a broad optional set.
- For Dask arrays, install `scanpy[dask]`; add `scanpy[dask-ml]` only when PCA needs Dask-ML.
- For methods without Scanpy extras (`phate`, `palantir`, `trimap`, `mnnpy`, `pypairs`, `wishbone`, `harmonyTS`, `sc-sam`, `phenograph`, `cellbrowser`), install the named upstream package for that method only.

## API Moved Or Deprecated

| Old path | Current guidance |
|---|---|
| `scanpy.external.pp.harmony_integrate` | Use `scanpy.pp.harmony_integrate`. |
| `scanpy.external.pp.scrublet` | Use `scanpy.pp.scrublet`. |
| `scanpy.external.pp.scrublet_simulate_doublets` | Use `scanpy.pp.scrublet_simulate_doublets`. |
| `scanpy.external.pl.scrublet_score_distribution` | Use `scanpy.pl.scrublet_score_distribution`. |

If a user reports deprecation warnings, update imports first before changing algorithm parameters.

## Data And Workflow Errors

| Symptom | Cause | Recovery |
|---|---|---|
| `sce.pp.scanorama_integrate` gives poor or failed integration | PCA is missing, batch key is wrong, or cells are not grouped consistently by batch | Verify `.obsm['X_pca']`, inspect `adata.obs[key]`, group/sort if needed, then use `adjusted_basis` for neighbors. |
| `sce.pp.bbknn` fails on missing `X_pca` | PCA not computed or `use_rep` wrong | Run `sc.pp.pca` or pass a valid `.obsm` key via `use_rep`. |
| `sce.tl.trimap` rejects sparse matrices | Wrapper checks sparse inputs | Use a dense/reduced representation if memory allows, or choose UMAP/PHATE depending on goals. |
| `sce.tl.harmony_timeseries` says timepoint column is not categorical | `adata.obs[tp]` dtype is not categorical | Convert with ordered categories before calling. |
| Scrublet output looks wrong | Input was normalized/logged when raw counts were expected | Use raw unnormalized counts or provide a consistently preprocessed `adata_sim`. |
| MAGIC consumes too much memory | `name_list='all_genes'` or default all-gene imputation on large sparse data | Use `name_list='pca_only'` or a targeted gene list. |
| HashSolo errors on barcode columns | Missing, non-numeric, or negative hashing counts | Verify barcode columns in `.obs`, non-negative counts, and sensible priors. |
| Exporting overwrites or writes unexpected files | Output path or overwrite policy was not checked | Confirm destination, permissions, size, and overwrite behavior before calling `sce.exporting.*`. |

## Dask Experimental/Selective Support

- If an error mentions feature-axis chunking, rechunk so chunks span all variables for the supported method.
- If an error mentions CSC sparse Dask blocks, convert to CSR-like sparse chunks when possible.
- If an external wrapper fails with a Dask array, materialize a reduced representation or use an in-memory subset; most upstream external packages are not Dask-aware.
- Do not claim a full pipeline is lazy until each method in that pipeline is known to preserve Dask arrays.
- If Dask and numba interact poorly in a threaded scheduler, try a single-threaded or process-safe scheduler for the failing step.

## GPU/RAPIDS Mismatch

- There is no `scanpy[gpu]` or RAPIDS extra in Scanpy's optional dependencies.
- Use `rapids-singlecell` for GPU workflows and verify CUDA, RAPIDS, CuPy, and driver compatibility in that separate stack.
- Scanpy's RAPIDS neighbor backend imports `cuml.neighbors.NearestNeighbors`; absence of `cuml` is an environment issue, not a Scanpy core install bug.
- Keep CPU Scanpy and RAPIDS code paths distinct; do not pass GPU arrays into Scanpy external wrappers unless the wrapper's upstream package explicitly supports them.

## Network, Credentials, And Large Downloads

- Some examples and user workflows fetch remote datasets or use large reference files; network or credential failures should be separated from Scanpy API failures.
- Prefer tiny synthetic AnnData fixtures for dependency/import checks.
- If a real workflow needs a remote dataset, validate optional dependencies and minimal API calls first, then handle data acquisition with explicit retry, cache, and credential rules.

## Conflicting Optional Packages

- Avoid installing broad dev/test groups and user runtime extras into a production environment unless the user explicitly asks for development setup.
- If `pip check` or import errors appear after adding external packages, inspect the last package added and solve that specific dependency conflict rather than adding more extras.
- For conda users, prefer conda-forge for compiled packages such as `igraph`, `leidenalg`, RAPIDS, and CUDA-dependent packages when possible; do not mix package managers blindly in an existing environment.
