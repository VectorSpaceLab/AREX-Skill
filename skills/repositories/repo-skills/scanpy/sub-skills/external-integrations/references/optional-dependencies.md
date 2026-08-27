# Optional Dependency Matrix

Scanpy's core install intentionally excludes several ecosystem packages. Recommend the narrow extra or upstream package that matches the requested method, and only discuss broad environments when the user explicitly asks for one.

## Public Install Baseline

| Goal | Recommended install guidance | Notes |
|---|---|---|
| Common Scanpy workflows with Leiden clustering | `pip install 'scanpy[leiden]'` or conda install `scanpy python-igraph leidenalg` from conda-forge | This is the common documented clustering install because Leiden needs `igraph` and `leidenalg`. |
| Plain core APIs without optional clustering extras | `pip install scanpy` | Works for many preprocessing, tools, plotting, and AnnData tasks, but popular Leiden/PAGA paths may need extras. |
| GPU acceleration | Install and use `rapids-singlecell` separately, or use Scanpy's cuML-backed neighbor transformer only in a compatible RAPIDS environment | RAPIDS is not a Scanpy optional extra. |

## Scanpy Optional Extras

| Extra | Packages installed by the extra | Use when |
|---|---|---|
| `bbknn` | `bbknn` | Calling `scanpy.external.pp.bbknn`. |
| `dask` | `anndata[dask]`, `dask[array]>=2024.5.1` | Working with selected Dask-backed AnnData arrays. |
| `dask-ml` | `dask-ml`, `scanpy[dask]` | Running PCA paths that use Dask-ML for dense Dask arrays. |
| `leiden` | `igraph>=0.10.8`, `leidenalg>=0.10.1` | Running `sc.tl.leiden` with `flavor='leidenalg'` or common clustering workflows. |
| `louvain` | `igraph`, `louvain>=0.8.2`, `setuptools` | Running Louvain-specific workflows. |
| `magic` | `magic-impute>=2.0.4` | Calling `scanpy.external.pp.magic`; the wrapper enforces a MAGIC version at runtime. |
| `paga` | `igraph` | Running PAGA workflows requiring graph abstraction support. |
| `plotting` | `colour-science` | Plotting workflows that need optional color-science support. |
| `scanorama` | `scanorama` | Calling `scanpy.external.pp.scanorama_integrate`. |
| `scrublet` | `scikit-image>=0.25` | Calling `sc.pp.scrublet` or `sc.pp.scrublet_simulate_doublets` when automatic thresholding needs scikit-image. |
| `skmisc` | `scikit-misc>=0.5.1` | Calling `sc.pp.highly_variable_genes(..., flavor='seurat_v3' or 'seurat_v3_paper')`. |
| `scanpy2` | `igraph>=0.10.8`, `scikit-misc>=0.5.1` | Preview/preset-style workflows needing both Leiden graph tooling and Seurat v3 HVG support. |

## Feature-To-Install Routing

| User asks for | Prefer | Why |
|---|---|---|
| Leiden clustering only | `scanpy[leiden]` | Matches common Scanpy clustering guidance and avoids unrelated external wrappers. |
| Seurat v3 HVG selection | `scanpy[skmisc]` | `highly_variable_genes(..., flavor='seurat_v3')` needs `scikit-misc`. |
| Publication plots with optional color handling | `scanpy[plotting]` | Adds `colour-science` only. |
| MAGIC imputation | `scanpy[magic]` | Provides `magic-impute>=2.0.4`. |
| Scanorama integration | `scanpy[scanorama]` | Provides `scanorama`. |
| BBKNN batch-balanced graph | `scanpy[bbknn]` | Provides `bbknn`; run after PCA. |
| Scrublet doublet prediction | `scanpy[scrublet]` | Provides `scikit-image`; Scrublet itself is implemented in Scanpy. |
| Dask-backed preprocessing | `scanpy[dask]` | Adds AnnData/Dask array support, but method coverage is selective. |
| Dask-ML PCA | `scanpy[dask-ml]` | Pulls `dask-ml` plus `scanpy[dask]`. |
| RAPIDS/GPU acceleration | `rapids-singlecell` or a compatible `cuml` stack for Scanpy's RAPIDS KNN transformer | Not a Scanpy extra; compatibility depends on CUDA, RAPIDS, CuPy, and drivers. |

## External Packages Without Scanpy Extras

Some `scanpy.external` wrappers lazily import packages that are not exposed as Scanpy optional extras. Recommend the specific upstream package only when the method is requested:

| Wrapper | Package/module checked by wrapper | Install note |
|---|---|---|
| `scanpy.external.pp.mnn_correct` | `mnnpy` | Install `mnnpy` only for MNN correction. |
| `scanpy.external.tl.phate` and `scanpy.external.pl.phate` | `phate` | Install `phate` only for PHATE embedding/plotting. |
| `scanpy.external.tl.palantir`, `palantir_results` | `palantir` | Palantir can use MAGIC-style imputation internally. |
| `scanpy.external.tl.trimap` and `scanpy.external.pl.trimap` | `trimap` | TriMap wrapper rejects sparse matrices. |
| `scanpy.external.tl.sam` and `scanpy.external.pl.sam` | `samalg` from `sc-sam` | Wrapper error note says install `sc-sam`. |
| `scanpy.external.tl.phenograph` | `phenograph>=1.5.3` | Clustering can also require Louvain or Leiden packages depending on `clustering_algo`. |
| `scanpy.external.tl.harmony_timeseries` and plotter | `harmony` from `harmonyTS` | Distinct from core `sc.pp.harmony_integrate`. |
| `scanpy.external.tl.wishbone` and plotter | `wishbone` | Typical workflows require precomputed diffusion/neighbor context. |
| `scanpy.external.tl.sandbag`, `cyclone` | `pypairs>=3.2.0` | Wrapper enforces minimum version. |
| `scanpy.external.exporting.cellbrowser` | `cellbrowser` | Needed only for UCSC Cell Browser export. |

## Decision Rules

1. Start from the requested method, not from a desire to make every optional API importable.
2. If the method is in core `sc.pp`, `sc.tl`, or `sc.pl`, prefer its specific extra (`leiden`, `skmisc`, `scrublet`, `plotting`) over `scanpy.external` guidance.
3. If an ImportError message names a package, install that package or the matching Scanpy extra; do not install all extras to silence one missing import.
4. For reproducible projects, add only the selected extras/packages to the project's dependency file and record why each optional dependency is needed.
5. Avoid mixing conda and pip in an existing compiled scientific environment unless the user has chosen that trade-off.
