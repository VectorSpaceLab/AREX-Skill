---
name: deberta_disentangled_attention
description: Compute and test DeBERTa style disentangled relative attention terms for bounded recovery experiments without relying on the original repository.
---

# DeBERTa Disentangled Attention

Use this skill when a recovery or implementation task needs the core DeBERTa attention mechanism: separate content-to-content, content-to-position, and position-to-content scores gathered by clipped relative-distance indices. Do not use this skill as a full Transformer replacement or as evidence of full DeBERTa model execution; it is a deterministic mechanism helper for module tests, ablations, and reduced recovery.

## Inputs

- A token sequence or scalar content features aligned with tokens.
- Positive maximum relative distance `k`.
- Optional per-token or per-distance scalar weights for deterministic proxy scoring.
- A list of active terms, normally `c2c`, `c2p`, and `p2c`.

## Outputs

- A DeBERTa-style relative-position index matrix.
- Separate score matrices for c2c, c2p, and p2c.
- A combined scaled score matrix and summary statistics.

## Workflow

1. Use `scripts/disentangled_attention.py` to build the clipped relative index matrix.
2. Compute each active attention term separately so ablations remain visible.
3. Combine terms with scaling based on the active component count.
4. In recovery, log both full and ablated scores; do not collapse c2p and p2c into one generic relative-position bias.

## Validation

Run:

```bash
python3 /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests
```

The bundled tests check relative-distance clipping, asymmetric c2p/p2c behavior, and ablation sensitivity.

## Limitations

The script uses scalar features so it can run in a bare Python environment. It preserves the DeBERTa attention contract and ablation structure, but it does not execute a pretrained neural model.

For stress tests, record the tested `k`, sequence length, clipped boundary values, and row-sum range. This makes it clear whether the proxy exercised long relative-distance clipping rather than only a three-token unit case.
