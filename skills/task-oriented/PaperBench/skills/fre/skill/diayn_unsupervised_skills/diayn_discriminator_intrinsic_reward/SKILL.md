---
name: diayn_discriminator_intrinsic_reward
description: Compute DIAYN discriminator log-probabilities, cross-entropy diagnostics, and intrinsic rewards from skill-conditioned state predictions.
---

# DIAYN Discriminator Intrinsic Reward

Use this skill when implementing or validating the DIAYN reward term `log q_phi(z|s) - log p(z)`. It is appropriate for tiny deterministic fixtures, reduced recovery experiments, and full implementations that need stable reward diagnostics. Do not use it to add downstream task rewards.

## Inputs

- A batch of discriminator logits or scores shaped as `batch x num_skills`.
- True sampled skill ids for each row.
- A fixed `log_prior`, usually `-log(num_skills)` for a uniform prior.

## Outputs

- Stable log-softmax values.
- Selected `log q_phi(z|s)` values.
- Intrinsic reward values.
- Mean reward, cross-entropy loss, and accuracy.

## Workflow

1. Validate batch and label dimensions.
2. Convert logits to log probabilities with a max-subtracted log-softmax.
3. Select log probability for the true skill on each transition.
4. Compute pseudo-reward by subtracting `log_prior`.
5. Report loss and accuracy for discriminator training diagnostics.

## Validation

Run `python scripts/diayn_reward.py --demo`. Tests verify that confident correct logits produce higher rewards and valid discriminator metrics.

## Limitations

This skill computes the reward and discriminator diagnostics only. It does not update neural network weights; pair it with a policy or discriminator optimizer in a larger recovery harness.
