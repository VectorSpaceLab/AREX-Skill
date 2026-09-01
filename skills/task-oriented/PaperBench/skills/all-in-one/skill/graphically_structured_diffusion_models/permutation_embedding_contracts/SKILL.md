---
name: permutation_embedding_contracts
description: Check mask-preserving permutations and derive embedding groups for graphically structured diffusion models.
---

# Permutation Embedding Contracts

Use this skill when a GSDM-style model wants array or exchangeable embedding sharing. The key check is architectural: a proposed permutation is valid for exact exchangeability only when it leaves the structured attention mask unchanged.

Do not use this skill to infer symmetries from training data. It verifies candidate symmetries supplied by a paper, task specification, or caller.

## Inputs

- Ordered node ids.
- Dense boolean attention mask.
- Candidate permutation as a list where entry `i` is the destination index for original index `i`.
- Embedding mode: `independent`, `array`, or `exchangeable`.
- Optional node-to-array mapping and exchangeable group mapping.

## Outputs

- Mask-preservation verdict and diagnostic mismatch.
- Node-to-embedding group mapping.
- Summary counts for validation logs.

## Workflow

1. Validate the permutation is a bijection over all node indices.
2. Compare every mask entry against the row-and-column permuted mask.
3. Derive independent groups as one group per node.
4. Derive array groups from array ids.
5. Derive exchangeable groups only after mask preservation is true.

## CLI

```bash
python scripts/permutation_contracts.py --graph-json /tmp/gsdm_graph.json --swap-i 0 1 --output /tmp/gsdm_perm.json
```

## Validation

```bash
python -m pytest tests
```

The tests verify that full BCMF plate swaps preserve the mask while partial single-array swaps fail, including a rectangular BCMF case where array-name grouping alone would be too permissive.

## Limitations

Mask preservation is necessary for the paper's embedding-sharing theorem, but semantic validity still depends on the task distribution and human-specified invariance.
