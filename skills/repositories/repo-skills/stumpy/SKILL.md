---
name: stumpy
description: "Use the STUMPY time-series matrix-profile package for exact,
  approximate, streaming, multidimensional, motif, segmentation, distributed,
  and optional GPU workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# STUMPY repo skill

Use this skill when a task asks for STUMPY, matrix profiles, motif/discord discovery, MPdist, snippets, time-series chains, semantic segmentation, streaming matrix profiles, pan matrix profiles, or STUMPY Dask/GPU execution.

STUMPY is a Python package for time-series data mining around the matrix profile. It exposes CPU, distributed, and optional CUDA APIs for exact and approximate matrix profiles plus downstream analysis workflows.

## First checks

Install the public package in the target environment when it is absent:

```bash
python -m pip install stumpy
# or: conda install -c conda-forge stumpy
```

For distributed Dask workflows, also install Dask Distributed if the environment did not include it:

```bash
python -m pip install dask distributed
```

Run the bundled environment check before relying on optional backends:

```bash
python scripts/stumpy_check_env.py --check all
```

## Route by task

- **Exact 1-D matrix profile, distance profile, self-join, AB-join, dtype/window issues:** read `sub-skills/matrix-profile-basics/SKILL.md`.
- **Multidimensional input, row-as-dimension layout, `mstump`, `maamp`, `subspace`, `mdl`, multidimensional motifs:** read `sub-skills/multidimensional-profiles/SKILL.md`.
- **Motifs, query matching, discords/anomalies, consensus motifs, MPdist, snippets, chains, FLUSS/FLOSS segmentation, shapelets:** read `sub-skills/motifs-anomalies-segmentation/SKILL.md`.
- **Approximate/anytime profiles, streaming updates, online segmentation, pan matrix profile/window-size exploration:** read `sub-skills/approximate-streaming-pan/SKILL.md`.
- **Dask, Ray, CUDA, GPU-STUMP, multi-GPU, backend diagnostics, or acceleration fallbacks:** read `sub-skills/distributed-gpu-acceleration/SKILL.md`.

## Common decisions

1. **Normalize or not:** use normalized APIs (`stump`, `mstump`, `scrump`, `stumpi`, `stimp`, `motifs`, `match`) for shape similarity after z-normalization. Use non-normalized families (`aamp`, `maamp`, `scraamp`, `aampi`, `aamp_stimp`, `aamp_motifs`, `aamp_match`) when absolute amplitudes and offsets matter.
2. **Self-join or AB-join:** self-joins search within one time series and should keep `ignore_trivial=True`. AB-joins compare two series and should use `ignore_trivial=False`.
3. **One-dimensional or multidimensional:** one-dimensional APIs accept shape `(n,)`; multidimensional workflows expect rows as dimensions and columns as time, shape `(d, n)`.
4. **Exact, approximate, streaming, or accelerated:** exact CPU APIs are the clearest baseline. Use approximate/streaming objects for latency or online data. Add Dask/Ray/CUDA only after the owner workflow is selected.
5. **Matrix-profile output:** distance and index columns may share an object-dtype array. Cast distance columns to `float` before numeric validation.

## Shared references and scripts

- `references/package-overview.md` summarizes package capabilities, data assumptions, and dependency choices.
- `references/troubleshooting.md` covers cross-cutting install/import, dependency, Numba, data, and routing failures.
- `references/repo-provenance.md` records the source snapshot for refresh decisions.
- `references/repo-routing-metadata.json` contains structured router import metadata.
- `scripts/stumpy_check_env.py` checks imports, versions, Dask, and optional CUDA visibility.
- `scripts/stumpy_quickstart.py` runs a short synthetic no-network tour across core STUMPY workflows.

## Do not do these

- Do not tell future users to open this source checkout's original docs, tests, notebooks, or scripts. Use the bundled references/scripts in this skill.
- Do not claim CUDA support from `import stumpy` alone; require `numba.cuda.is_available()` and a backend smoke in the target runtime.
- Do not flatten multidimensional data silently. Preserve the STUMPY convention that rows are dimensions and columns are time.
- Do not mix normalized and non-normalized API families without explaining the distance-model change.
- Do not import this skill into the live repo-skills library for this run; production was requested as non-imported output.
