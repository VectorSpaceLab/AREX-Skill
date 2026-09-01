---
name: minibatch_ot_coupling
description: Compute deterministic squared-cost minibatch optimal transport pairings for OT conditional flow matching recovery runs.
---

# Minibatch OT Coupling

Use this skill when implementing OT-CFM or validating whether a recovery experiment pairs source and target samples according to a minibatch optimal transport plan. Do not use the exact enumerator for large minibatches.

## Inputs
- Equal-sized source and target minibatches of numeric vectors.
- Optional comparison pairing, such as an independent or shuffled permutation.

## Outputs
- Minimum-cost permutation mapping each source index to a target index.
- Squared Euclidean transport cost for the assignment.
- Pair records that downstream CFM objective code can consume.

## Workflow
1. Build the squared Euclidean cost matrix.
2. Solve a one-to-one minimum assignment. The bundled script enumerates permutations and is intended for small deterministic tests.
3. Return paired source/target indices and costs.
4. Compare against independent pairings when validating the OT-CFM mechanism.

## Validation
Run `python tests/test_minibatch_ot.py` or the Distiller skill-tree validator with tests enabled.

## Limitations
The bundled solver is factorial in batch size and should be replaced with a Hungarian, Sinkhorn, or POT implementation for real-scale training.
