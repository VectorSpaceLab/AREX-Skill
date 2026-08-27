---
name: external-integrations
description: "Use Scanpy optional integrations, scanpy.external wrappers,
  Dask-backed arrays, and GPU/RAPIDS handoffs without over-installing optional
  dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Scanpy External Integrations

Use this sub-skill when a task involves optional dependency extras, `scanpy.external`, Dask-backed arrays, RAPIDS/GPU acceleration, external exporting, or integration/imputation/demultiplexing/trajectory wrappers outside Scanpy's core preprocessing and tool APIs.

## Route By Need

- **Optional extras planning**: Read [references/optional-dependencies.md](references/optional-dependencies.md) before recommending installs; choose the narrow extra or upstream package for the requested feature and do not suggest installing every extra.
- **External wrapper selection**: Read [references/external-api-map.md](references/external-api-map.md) to map `scanpy.external.pp`, `scanpy.external.tl`, `scanpy.external.pl`, and `scanpy.external.exporting` methods to prerequisites, outputs, and moved APIs.
- **Dask or large arrays**: Read [references/dask-and-rapids.md](references/dask-and-rapids.md) before promising distributed support; Scanpy supports selected Dask-backed preprocessing paths, not every algorithm or external package.
- **GPU acceleration**: Route GPU requests to [references/dask-and-rapids.md](references/dask-and-rapids.md); GPU workflows are usually delegated to `rapids-singlecell`, while Scanpy's RAPIDS neighbor backend requires a compatible cuML stack.
- **Import/install failures**: Use [references/troubleshooting.md](references/troubleshooting.md) plus `scripts/check_scanpy_optional_deps.py` to diagnose missing optional packages without installing or importing heavy dependencies.

## Safe Helper

Run the bundled checker from this sub-skill directory when you need a machine-readable optional-dependency inventory:

```console
python scripts/check_scanpy_optional_deps.py --feature scanorama --feature magic --json
python scripts/check_scanpy_optional_deps.py --list-features
```

The helper uses `importlib.util.find_spec` and package metadata only. It has no network, install, import-heavy, or package-mutation side effects.

## Boundaries

- Prefer core Scanpy guidance for ordinary normalization, PCA, neighbors, clustering, plotting, and AnnData handling unless the task explicitly needs optional integrations, Dask-backed arrays, or GPU handoffs.
- Prefer `sc.pp.harmony_integrate`, `sc.pp.scrublet`, and `sc.pp.scrublet_simulate_doublets` for moved APIs; legacy `scanpy.external.pp` aliases are deprecated compatibility routes.
- Keep install advice minimal: `scanpy[leiden]`, `scanpy[skmisc]`, `scanpy[plotting]`, `scanpy[magic]`, `scanpy[scanorama]`, `scanpy[bbknn]`, `scanpy[dask]`, `scanpy[dask-ml]`, and `scanpy[scrublet]` are targeted choices for specific features.
- For wrappers without Scanpy extras, recommend the named upstream package only for that method, such as `mnnpy`, `phate`, `palantir`, `trimap`, `sc-sam`, `phenograph`, `harmonyTS`, `wishbone`, `pypairs`, or `cellbrowser`.
- Do not recommend broad optional extras, development/test dependency groups, source checkout scripts, or original repository paths for runtime use.
