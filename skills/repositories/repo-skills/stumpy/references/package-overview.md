# STUMPY Package Overview

Read this for a compact map of STUMPY capabilities before choosing a sub-skill.

## What STUMPY does

STUMPY computes matrix profiles for time-series data and then uses them for motif discovery, discord/anomaly discovery, shapelet-style matching, semantic segmentation, snippets, chains, streaming updates, approximate profiles, multidimensional motif discovery, distributed execution, and optional GPU acceleration.

## Installation choices

Public installation options:

```bash
python -m pip install stumpy
conda install -c conda-forge stumpy
uv add stumpy
pixi add stumpy
```

Core package dependencies are NumPy, SciPy, and Numba. Dask distributed workflows need `dask` and `distributed`. Pandas and polars series/dataframes are accepted by selected APIs/tests but are not required for plain NumPy workflows. Ray and CUDA are optional.

## Data conventions

- Use numeric floating-point arrays; `float64` is the safest baseline.
- One-dimensional workflows use shape `(n,)`.
- Multidimensional workflows use shape `(d, n)`: rows are dimensions, columns are time.
- Window size `m` is the subsequence length and must be at least 3.
- Profiles often return arrays containing both distances and indices. Cast distance columns to `float` before numeric checks.
- First calls can include Numba JIT compilation overhead; run a tiny warm-up before timing.

## Capability map

| Task family | Main APIs | Skill route |
| --- | --- | --- |
| Exact 1-D matrix profile | `stump`, `aamp`, `mass` | `sub-skills/matrix-profile-basics/SKILL.md` |
| Multidimensional profile/subspace | `mstump`, `maamp`, `subspace`, `mdl`, `mmotifs` | `sub-skills/multidimensional-profiles/SKILL.md` |
| Motifs/anomalies/segmentation | `motifs`, `match`, `ostinato`, `mpdist`, `snippets`, `atsc`, `allc`, `fluss`, `floss` | `sub-skills/motifs-anomalies-segmentation/SKILL.md` |
| Approximate/streaming/pan | `scrump`, `scraamp`, `stumpi`, `aampi`, `stimp`, `aamp_stimp` | `sub-skills/approximate-streaming-pan/SKILL.md` |
| Distributed/GPU acceleration | `stumped`, `mstumped`, `mpdisted`, `stimped`, `gpu_stump`, `gpu_mpdist`, `gpu_stimp` | `sub-skills/distributed-gpu-acceleration/SKILL.md` |

## Distance-model families

Normalized/z-normalized family:

- exact profiles: `stump`, `mstump`;
- approximate and streaming: `scrump`, `stumpi`, `stimp`;
- downstream: `motifs`, `match`, `mpdist`, `ostinato`, `fluss`, `floss` by default.

Non-normalized/p-norm family:

- exact profiles: `aamp`, `maamp`;
- approximate and streaming: `scraamp`, `aampi`, `aamp_stimp`;
- downstream: `aamp_motifs`, `aamp_match`, `aampdist`, `aamp_ostinato`, `aampdist_snippets`.

Keep the family consistent unless the user explicitly wants to compare normalized and non-normalized behavior.

## Optional backend status

This skill was verified for core CPU and Dask LocalCluster use. GPU APIs are documented and routed, but CUDA must be proven in the target runtime before use. A target environment with visible GPUs can still fail `numba.cuda.is_available()` because of driver, container passthrough, or Numba runtime constraints.

Ray support is present in selected distributed code paths but is treated as optional/experimental. Prefer Dask for default distributed examples unless the user explicitly asks for Ray.

## Quick smoke

Run a broad no-network smoke:

```bash
python scripts/stumpy_quickstart.py
```

Run detailed environment/backend checks:

```bash
python scripts/stumpy_check_env.py --check all
```
