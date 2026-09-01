---
name: graph_structure_attention
description: Build graph-derived sparse attention masks for Graphically Structured Diffusion Model style recovery experiments and checks.
---

# Graph Structure Attention

Use this skill when a task gives a graphical model or factor graph and you need the GSDM-style attention contract: one token per variable, self-attention on every token, symmetrized variable dependencies, and optional factor-clique attention.

Do not use this skill to learn graph structure from data. The paper assumes a supplied graphical-model sketch and uses it to constrain a diffusion denoiser.

## Inputs

- `nodes`: ordered variable ids.
- `edges`: directed or undirected pairs of variable ids.
- `factors`: optional lists of node ids that share an undirected factor.
- Optional BCMF dimensions `m`, `n`, and `k` for the paper's matrix-factorization graph.

## Outputs

- Dense boolean mask `mask`.
- Packed sparse representation with `attendable_indices` and `valid_indices_mask`.
- Node metadata and simple mask statistics.

## Workflow

1. Build or receive an ordered node list.
2. Add self-edges for all nodes.
3. Add graph edges in both directions.
4. For each factor scope, add all pairwise co-scope edges.
5. Pack each row of the mask to a fixed-width attendable-index array.
6. Use `scripts/graph_attention.py` for deterministic construction and validation.

## CLI

```bash
python scripts/graph_attention.py --bcmf 2 2 2 --output /tmp/gsdm_graph.json
```

## Validation

```bash
python -m pytest tests
```

The tests verify BCMF node counts, expected local dependencies, absence of unrelated edges, and round-trip reconstruction from packed sparse indices.

## Limitations

The skill validates the structural mask only. It does not implement transformer layers or train a diffusion model.
