---
name: motifs-anomalies-segmentation
description: "Route matrix-profile results into motif discovery, query matching,
  discords/anomalies, consensus motifs, MPdist, snippets, chains, shapelets, and
  semantic segmentation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Motifs, anomalies, and segmentation

Use this sub-skill when the matrix profile already exists, or when you already know the query or comparison series and need analysis rather than profile construction.

## Route here for
- motif extraction from a 1-D profile
- query matching against a raw series
- discords / anomalies from profile peaks
- consensus motifs across a list of series
- MPdist and snippets for similarity and summarization
- chains from left / right nearest-neighbor indices
- FLUSS / FLOSS semantic segmentation
- shapelet candidate ranking from class-vs-class profile contrasts

## Route away when
- you still need the base 1-D profile computation -> `matrix-profile-basics`
- you need multidimensional profile construction or subspace choice -> `multidimensional-profiles`
- you need online, anytime, or pan updates -> `approximate-streaming-pan`
- you need Dask / GPU / Ray acceleration setup -> `distributed-gpu-acceleration`

## What the APIs consume
- raw series + 1-D profile -> `motifs`
- raw query + raw series -> `match`
- list of raw series -> `ostinato`
- precomputed multidimensional profile / index arrays -> `mmotifs` handoff only
- raw pair of series -> `mpdist`
- raw series -> `snippets`
- left / right index columns -> `atsc`, `allc`
- nearest-neighbor index column -> `fluss`
- full 4-column matrix profile + raw series -> `floss`

## Workflow
1. Start from the smallest stable input you already have.
2. Use `references/workflows.md` for the exact path.
3. Use `scripts/motif_segmentation_smoke.py --help` for the bundled no-network smoke path.
4. If the failure is really about profile creation, dimensionality, or acceleration, hand off to the owning sub-skill.

## Validation cues
- low profile values are motif candidates
- high profile values are discord / anomaly candidates
- `normalize=False` must stay consistent across the upstream profile and the downstream analysis call
- `atsc`, `allc`, and `fluss` are index-driven; do not pass profile distances where indices are required

## Bundled references
- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
