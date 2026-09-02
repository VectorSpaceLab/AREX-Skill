---
name: pgd_adversarial_training_loop
description: Run a deterministic PGD adversarial training loop that updates model parameters on adversarial examples and logs loss traces.
---

# PGD Adversarial Training Loop

## When To Use
Use this skill for the outer minimization step in a Madry-style robust optimization recovery. It is designed for bounded experiments where the model can generate adversarial examples with the current parameters and then update parameters on those examples.

Do not use it to claim robust training if no PGD examples are generated or no trainable parameters change.

## Inputs
- Training examples and labels.
- A trainable model with parameter gradients.
- PGD attack configuration: epsilon, step size, steps, restarts, and seed.
- Optimizer configuration: learning rate and epochs.

## Outputs
- Updated model parameters.
- Training trace with `loss_before`, `loss_after`, `params_before`, and `params_after`.
- Mechanism checks for PGD generation and optimizer execution.

## Workflow
1. Generate PGD adversarial examples using the current model.
2. Compute adversarial loss and parameter gradients.
3. Apply a gradient-descent update to model weights and bias.
4. Re-evaluate adversarial loss after the update.
5. Save trace fields that prove parameters changed and loss was measured before and after.

## Validation
Run:

```bash
python scripts/adversarial_train.py --self-test
python tests/test_adversarial_train.py
```

## Limitations
The included script is a deterministic reduced proxy using a tiny logistic classifier. Full MNIST/CIFAR recovery requires a real deep-learning runtime and dataset.
