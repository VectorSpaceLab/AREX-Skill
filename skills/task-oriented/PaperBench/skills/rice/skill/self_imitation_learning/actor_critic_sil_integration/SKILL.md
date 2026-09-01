---
name: actor_critic_sil_integration
description: Run a bounded actor-critic Self-Imitation Learning update and log trainable parameter evidence.
---

# Actor-Critic SIL Integration

Use this skill when integrating SIL with an actor-critic learner or when building a reduced recovery that must execute the paper's optimizer mechanism. It complements ordinary A2C/PPO updates by applying replay-based positive-advantage imitation updates.

Do not claim this skill reproduces full Atari or MuJoCo training unless the caller uses a real environment, policy network, and training budget.

## Inputs
- Replay records with `action` and `return` fields.
- Initial trainable proxy parameters or a caller-provided actor-critic model.
- Learning rate, number of updates, and value-loss coefficient.

## Outputs
- Training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, action probabilities, value estimates, and optimizer-step flags.
- Mechanism evidence for reduced recovery.

## Workflow
1. Read replay records produced from completed trajectories.
2. Compute selected-action probability and value estimates from trainable parameters.
3. Apply SIL positive-advantage policy and value gradients.
4. Record before/after losses and parameter changes.
5. Mark reduced/full runtime booleans honestly.

## Validation
Run:

```bash
python tests/test_scalar_sil_training.py
```

The test checks that a high-return action receives higher probability and that SIL loss decreases after training.

## Limitations
- The included script is a deterministic scalar proxy for recovery evidence, not a replacement for full A2C/PPO implementations.
- It intentionally uses only the Python standard library to avoid mutating shared environments.

## Bounded Optimizer Sensitivity
Reduced recovery should log the learning rate and update count because very small update budgets may show only tiny probability movement even when parameters change. Acceptance should require parameter-change evidence and a positive loss decrease.
