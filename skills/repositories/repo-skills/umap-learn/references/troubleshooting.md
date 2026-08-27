# Cross-Cutting UMAP Troubleshooting

Use this for install/import, optional dependency, performance, and routing
failures that span multiple sub-skills.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'umap'` | Distribution not installed in the active Python | Install `pip install umap-learn`; verify with `python -c "import umap; print(umap.__version__)"`. |
| Installed `umap-learn` but wrong package imports | Environment/path confusion or another `umap` package shadowing imports | Run `scripts/check_umap_environment.py --json`; inspect active Python and package metadata in your target environment. |
| `ImportError` from `umap.plot` | Optional plot extra missing | Install `pip install "umap-learn[plot]"` or use plain `mapper.embedding_` plotting fallback. |
| `ParametricUMAP` import/construct raises TensorFlow error | Optional TensorFlow/Keras stack missing | Install `pip install "umap-learn[parametric_umap]"`; run the parametric stack checker before training. |
| UMAP uses all cores or is slower than expected | Numba/PyNNDescent parallelism or reproducibility settings | Set `random_state` for reproducibility knowing it forces `n_jobs=1`; leave `random_state=None` for speed; tune `n_neighbors` and sample first. |
| Memory pressure | Large dense arrays, high-dimensional data, plotting large embeddings, or too many neighbours | Keep sparse data sparse, sample first, use `low_memory=True`, reduce `n_neighbors`, and avoid large plotting until embedding quality is checked. |
| Results differ across runs | Stochastic optimization | Set `random_state` and `transform_seed`; record that deterministic settings reduce parallelism. |
| User asks for GPU UMAP | Base `umap-learn` has no verified CUDA workflow | State that base package is CPU-oriented. If user means neural ParametricUMAP, route to parametric-umap and verify TensorFlow device support. |
| Task mixes labels, plotting, and transform errors | Multiple capability surfaces are involved | Start with core-embedding for fit/transform correctness, then route to supervised-density for labels and plotting-diagnostics for rendering. |
| Skill may be stale for a checkout | Commit, package version, dirty state, or evidence paths changed | Read `references/repo-provenance.md`; if current repo differs materially, run a refresh workflow. |

## Triage Order

1. Prove base import: `python scripts/check_umap_environment.py --json`.
2. Prove core fit on toy data: `python sub-skills/core-embedding/scripts/umap_core_smoke.py --json`.
3. Identify whether the failing task uses optional extras: plotting or ParametricUMAP.
4. Check data shapes and labels before tuning parameters.
5. Validate scientific claims with downstream metrics, not only the 2D plot.

## Optional Extra Policy

Missing optional extras do not invalidate base UMAP. They should be handled with
clear install guidance and fallback plans:

- Plotting fallback: use `mapper.embedding_` and a plotting library available in
  the target environment.
- Parametric fallback: use standard `UMAP.transform` unless a neural encoder is
  genuinely required.
- TBB fallback: proceed without TBB unless profiling proves it is needed.
