---
name: dpo_reduced_training_harness
description: Run a bounded scalar DPO optimization that records loss, parameter changes, preference accuracy, and mechanism checks for reduced recovery.
---

# DPO Reduced Training Harness

Use this skill when full language-model DPO training is blocked but soft-mode recovery permits a mechanism-faithful reduced experiment. The harness must still construct preference examples, compute the DPO log-ratio loss against a fixed reference, update trainable policy parameters, and record executable evidence.

## Inputs

- Preference examples following the DPO preference data contract.
- Initial scalar policy log-probability parameters for chosen and rejected responses.
- Fixed reference chosen/rejected log probabilities.
- `beta`, learning rate, and number of optimizer steps.

## Outputs

- A training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, and preference accuracy.
- Mechanism checks for data construction, DPO loss computation, fixed reference use, and optimizer execution.
- JSON suitable for inclusion in recovery artifacts.

## Workflow

1. Normalize or validate the preference items.
2. Initialize trainable chosen/rejected policy score parameters.
3. Compute initial DPO loss and margins.
4. Apply analytic gradient descent on `-log sigmoid(beta * margin)` where `margin = (policy_chosen-policy_rejected) - reference_logratio`.
5. Keep reference scores fixed.
6. Record before/after losses, parameters, margins, and accuracy.
7. Mark full model booleans false unless a real model was loaded outside this reduced harness.

## Validation

Run:

```bash
python scripts/reduced_dpo_train.py --self-test
python tests/test_reduced_dpo_train.py
```

## Limitations

This is not a full language model. It is an approved soft-mode proxy only when full model training is blocked and the recovery result clearly declares reduced training.