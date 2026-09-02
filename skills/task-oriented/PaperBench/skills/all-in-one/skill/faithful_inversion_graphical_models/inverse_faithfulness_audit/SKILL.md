---
name: inverse_faithfulness_audit
description: Audit inverse Bayesian-network structures for naturalness, local I-map consistency, and edge-minimality evidence using d-separation checks.
---

# Inverse Faithfulness Audit

Use this skill when a generated inverse graph needs structural validation against a generative Bayesian network. It is designed for small recovery graphs, regression tests, and mechanism evidence. It is not a full theorem prover for arbitrary large graphical models.

## Inputs

- Generative `parents` mapping for the original BN.
- `inverse_parents` mapping from latent factor variable to inverse parents.
- Lists of `latents` and `observed` variables.
- `mode`: `topological` or `reverse_topological`.

## Outputs

- `ok`, `natural_ok`, `local_imap_ok`, and `minimality_ok`.
- `issues`: a list of failed checks with variable and conditioning-set details.
- `checked_edges`: number of inverse edges audited for edge-removal evidence.

## Workflow

1. Validate that all inverse factor variables are latent variables.
2. Check naturalness relative to generative ancestors and descendants.
3. Enumerate local Markov assertions induced by the inverse graph and verify each with d-separation in the generative graph.
4. For every inverse edge, remove that parent from the local conditioning set and confirm the removed parent would not be d-separated from the child in the generative graph.
5. Treat any issue as a request to refine the graph inversion or factor contract.

## Validation

Run:

```bash
python tests/test_audit.py
```

The tests use only standard-library imports.

## Limitations

The audit checks singleton local Markov assertions and edge-removal witnesses. That is sufficient for reduced recovery evidence and regression tests, while the paper's proof remains the authority for NaMI's general correctness.
