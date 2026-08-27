# Dask, Large Arrays, and RAPIDS

Scanpy has selective Dask-backed array support. Treat it as method-specific support for large arrays, not as a guarantee that every Scanpy or `scanpy.external` function can run lazily or distributed.

## Dask Extras

| Need | Install guidance | Scope |
|---|---|---|
| Dask-backed AnnData arrays | `scanpy[dask]` | Adds `anndata[dask]` and `dask[array]`. |
| PCA with Dask-ML paths | `scanpy[dask-ml]` | Adds `dask-ml` and `scanpy[dask]`. |

Do not recommend Dask extras for ordinary in-memory datasets. Use them when the user already has Dask arrays/Zarr-backed data or explicitly asks for larger-than-memory workflows.

## Evidence-Backed Supported Areas

| Area | Evidence-backed behavior | Caveats |
|---|---|---|
| `sc.pp.log1p` | Can preserve Dask-backed `.X`; materialized results can match in-memory tests. | Downstream methods may still materialize. |
| `sc.pp.normalize_total` | Can preserve Dask-backed `.X`; results can match in-memory tests. | Some options force computation depending on input and required totals. |
| `sc.pp.filter_cells` / `sc.pp.filter_genes` | Work on Dask arrays and AnnData with Dask `.X`; count vectors can remain Dask-backed. | Shape-changing AnnData filtering eventually needs concrete indexing decisions. |
| `sc.pp.highly_variable_genes` | Has Dask coverage including Seurat v3 variants. | Seurat v3 flavors still require `scanpy[skmisc]`; feature-axis chunking is restricted. |
| `sc.pp.pca` | Has dense Dask and selected sparse-in-Dask support. | Sparse Dask has CSR/chunking restrictions; Dask-ML may be required for some dense paths. |
| `sc.pp.calculate_qc_metrics` | Some Dask cases are tested. | CSC-backed Dask and feature-axis chunking can raise errors; some numba-related paths are not Dask-ready. |
| `scanpy.preprocessing._distributed.materialize_as_ndarray` | Internal helper computes Dask arrays to NumPy arrays. | Its existence is a warning: some Scanpy paths intentionally materialize distributed values. |

## Common Dask Failure Rules

- Dask arrays chunked along the feature axis are often rejected; prefer chunking along observations with full feature chunks for supported methods.
- Sparse Dask inputs should use CSR-like blocks for supported paths; CSC sparse blocks are frequently rejected.
- In-place `out` style modification is not supported for Dask arrays in low-level scaling helpers.
- Some computations intentionally materialize intermediate arrays; verify memory before promising end-to-end laziness.
- External wrappers such as MAGIC, PHATE, Scanorama, MNN, BBKNN, Palantir, TriMap, SAM, Wishbone, and Harmony time-series generally call upstream libraries that may not understand Dask arrays. Convert or subset before using them unless their upstream docs explicitly support Dask.

## Dask PCA Constraints

Use these guardrails before advising `sc.pp.pca` on Dask arrays:

| Input | Practical guidance |
|---|---|
| Dense Dask array | `scanpy[dask-ml]` may be needed for Dask-ML PCA/TruncatedSVD/IncrementalPCA paths. |
| Sparse Dask array | Prefer CSR-like chunks, not CSC; feature-axis chunking is commonly rejected. |
| `zero_center=False` with sparse Dask | Some sparse-in-Dask paths are not implemented; test a small slice first. |
| Very large dense data | Consider covariance-based or incremental paths, but still plan memory for reductions and output embeddings. |

## RAPIDS/GPU Guidance

Scanpy's installation docs point GPU users to `rapids-singlecell`, which mirrors parts of the Scanpy API for accelerated preprocessing, neighbors, embedding, and clustering. RAPIDS is separate from Scanpy optional extras.

Scanpy also exposes a cuML-backed `RapidsKNNTransformer` neighbor backend in source. It imports `cuml.neighbors.NearestNeighbors`, converts input to contiguous `float32`, and returns a distance-mode k-neighbors graph. Use it only when the environment already has a compatible CUDA/RAPIDS/cuML stack.

| User request | Guidance |
|---|---|
| "Make Scanpy use my GPU" | Explain that core Scanpy is CPU-first and recommend evaluating `rapids-singlecell` for GPU-backed workflows. |
| "Install a Scanpy GPU extra" | Clarify that there is no Scanpy RAPIDS/GPU extra in the optional-dependencies table. |
| "Use GPU for neighbors/UMAP/clustering" | Prefer `rapids-singlecell`; if using Scanpy's RAPIDS KNN backend directly, verify `cuml`, CUDA, CuPy, and driver compatibility first. |
| "Compare CPU and GPU results" | Keep Scanpy CPU code as the reference and run RAPIDS-specific code separately, noting numerical and algorithmic differences. |

## Practical Large-Data Workflow

1. Confirm storage and array type: in-memory NumPy/SciPy, backed AnnData, Zarr, Dask dense, or Dask sparse.
2. Choose the smallest optional install: `scanpy[dask]` for Dask arrays, `scanpy[dask-ml]` only when a Dask-ML PCA path is needed.
3. Check chunking before calling methods: avoid feature-axis chunking when the method rejects it.
4. Run preprocessing methods with documented Dask support first: filtering, normalization, log1p, HVG, selected PCA.
5. Materialize or export a reduced representation before using external wrappers that expect NumPy/SciPy arrays.
6. For GPU acceleration, plan a separate RAPIDS implementation instead of trying to force Scanpy external wrappers onto GPU arrays.
