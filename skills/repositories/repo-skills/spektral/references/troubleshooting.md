# Cross-Cutting Troubleshooting

Start here for install/import and route-selection problems. Use the sub-skill troubleshooting pages for API-specific fixes.

## Install or import fails

**Symptoms**
- `ModuleNotFoundError: No module named 'spektral'`
- TensorFlow, NumPy, SciPy, pandas, or scikit-learn imports fail.
- Editable install from a checkout fails before building metadata.

**Actions**
1. Prefer `pip install spektral` for user workflows.
2. For source checkouts, install from a clean source tree or wheel. If setuptools reports "Multiple top-level packages discovered in a flat-layout", remove unrelated top-level directories from the install source or use a clean clone.
3. Run `python scripts/check_install.py --show-signatures` from this skill directory to verify importability and key objects.
4. Record `spektral`, `tensorflow`, and `keras` versions when reporting compatibility issues.

## TensorFlow/Keras compatibility and GPU warnings

Spektral depends on TensorFlow. For this Spektral `1.3.1` source revision, TensorFlow/Keras 2.x is the safest compatibility target for model execution; TensorFlow `2.15.1` with Keras `2.15.0` passed the bundled CPU smoke checks. If a latest TensorFlow/Keras 3 environment fails inside `GCNConv.call()` with a mask or `None` tensor conversion error, pin to a TensorFlow/Keras 2.x stack or intentionally patch/wrap that layer path.

A CPU-only environment may still print messages such as "Could not find cuda drivers" or "GPU will not be used". Treat these as warnings when the selected workflow is CPU-only. They become blocking only if the task explicitly requires GPU behavior or a TensorFlow GPU wheel.

## Dataset downloads and caches

Built-in datasets often download on first use. The default cache root is `~/.spektral/datasets`, and `~/.spektral/config.json` can set `dataset_folder`. Networked dataset examples are not safe smoke tests unless the cache already exists and the user approved the download.

## Data mode and mask mismatches

Most difficult Spektral errors come from mixing data modes:

- `SingleLoader` requires exactly one graph.
- `DisjointLoader` returns a sparse disjoint union plus graph-id vector `i`.
- `BatchLoader` returns dense padded tensors; `mask=True` appends a mask feature to `x`.
- `MixedLoader` requires one shared dataset adjacency matrix in `dataset.a`.
- `MessagePassing` layers require sparse adjacency and only support single/disjoint style propagation.

Read `sub-skills/graph-data/references/troubleshooting.md` for loader/data fixes and `sub-skills/gnn-models/references/troubleshooting.md` for layer/model fixes.

## Version drift in older source expectations

Some Spektral 1.3.1 tests and paths assume older dependency APIs: NetworkX sparse matrix helpers with `.A`, SciPy Delaunay's `vertices` attribute, and Keras softmax/mask behavior from TensorFlow/Keras 2.x. If a user reports `csr_array`/`.A`, Delaunay `vertices`, `GlobalAttnSumPool` rank-1 softmax, or `GCNConv` mask errors, treat it as dependency-version drift before blaming graph data.

## Optional dependencies

The base package does not install every dependency used by examples. OGB examples require the external `ogb` package and OGB dataset objects. Plotting examples require plotting libraries. Treat those as optional workflow dependencies, not base import failures.

## Version drift and stale guidance

Read `references/repo-provenance.md` when the current source checkout or installed package is not `1.3.1`, when a layer signature differs, or when TensorFlow/Keras mask/build behavior differs from this skill. Refresh the skill before relying on stale mode-support or signature claims.
