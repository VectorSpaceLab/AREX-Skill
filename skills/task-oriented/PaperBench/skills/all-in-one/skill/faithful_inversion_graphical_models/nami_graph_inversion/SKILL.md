---
name: nami_graph_inversion
description: Generate natural minimally faithful inverse graph structures from Bayesian-network DAGs using the paper's NaMI variable-elimination procedure.
---

# NaMI Graph Inversion

Use this skill when a task needs the structural inversion method from "Faithful Inversion of Generative Models for Effective Amortized Inference": converting a generative Bayesian-network DAG into inverse parent sets for an amortized inference network. Do not use it for numeric posterior inference by itself; it produces graph structure and an elimination trace, not trained neural parameters.

## Inputs

- A JSON object or Python mapping `parents` from node id to a list of directed parents in the generative BN.
- A list of `latents` that the inverse network must sample.
- A list of `observed` variables that condition the inverse network.
- `mode`, either `topological` for forward-NaMI or `reverse_topological` for reverse-NaMI.

## Outputs

- `inverse_parents`: mapping from latent variable to parent variables in the inverse graph.
- `elimination_order`: latent variables in the order simulated by variable elimination.
- `trace`: per-step frontier, fill edges, unmarked neighbors, and selected variable.
- `edge_count`: number of inverse parent edges.

## Workflow

1. Validate that the generative graph is acyclic and that all latent/observed variables exist.
2. Moralize the graph by dropping directions and connecting all co-parents.
3. Initialize the frontier with latent variables that have no upstream latent variables for the selected mode.
4. Repeatedly choose the frontier variable with the smallest min-fill score, using lexical order for ties.
5. Add fill edges among unmarked neighbors, assign those neighbors as inverse parents, mark the variable, and update the frontier.
6. Return the inverse structure and trace. Run both modes when compactness matters.

## Validation

Run:

```bash
python scripts/nami.py --example binary_tree --mode topological
python tests/test_nami.py
```

The test file uses only the Python standard library and can also be run by the Distiller skill-tree validator.

## Limitations

This skill intentionally implements the graph algorithm only. It does not train inference networks, compute analytic Gaussian posteriors, or prove global optimality among all possible minimal I-maps.
