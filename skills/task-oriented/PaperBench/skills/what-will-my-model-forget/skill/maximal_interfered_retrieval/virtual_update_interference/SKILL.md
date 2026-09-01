---
name: virtual_update_interference
description: Rank replay candidates by loss increase under a virtual incoming-batch update for MIR selection.
---

# Virtual Update Interference

Use this skill when a recovery harness or implementation needs the core MIR selector. It computes a one-step virtual update from the incoming batch, evaluates candidate memory examples before and after that virtual update, and selects the examples with the greatest predicted loss increase.

## Inputs
- Current linear model parameters or an adapter exposing equivalent loss and gradient behavior.
- Incoming batch examples with features and binary labels.
- Candidate memory examples with features, labels, and optional best historical losses.
- Learning rate, replay budget, and scoring variant `smi_1` or `smi_2`.

## Outputs
- Virtual parameters.
- Candidate score records with current loss, virtual loss, and MIR score.
- Top-k selected replay candidates ordered by descending interference.

## Workflow
1. Clone the current parameters so the real model is not mutated.
2. Compute the average logistic-loss gradient on the incoming batch.
3. Apply one virtual SGD step to produce `theta_v`.
4. Score each candidate with `loss(theta_v) - loss(theta)` for `smi_1`.
5. For `smi_2`, subtract `min(current_loss, best_loss)`.
6. Sort by descending score, tie-breaking by stable example id.

## Validation
Run the included tests or `validate_skill_tree.py --run-tests`. They verify non-mutation, ranking of a harmed candidate, empty candidate behavior, and `smi_2` historical-loss handling.

## Limitations
The bundled script is a deterministic standard-library logistic-regression implementation for small recovery experiments. Larger neural systems should preserve the same contract with framework-specific models.
