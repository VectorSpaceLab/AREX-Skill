---
name: deep_ritz_training_recovery
description: Run bounded Deep Ritz optimization and emit auditable recovery artifacts for variational PDE experiments.
---

# Deep Ritz Training Recovery

## When To Use

Use this skill after residual-network, stochastic-sampling, and variational-loss skills exist. It is for bounded recovery experiments that must prove the Deep Ritz mechanism executed without reading an original repository.

## Inputs

- Attempt directory.
- Generated skills root.
- Runtime handoff JSON.
- Module plan target.
- Recovery settings: dimension, width, blocks, steps, batch sizes, beta, learning rate, seed.

## Outputs

- `recovery/logs/training_trace.json` with loss, error, parameter snapshots, and optimizer evidence.
- `recovery/recovery_result.json` with metric and mechanism checks.
- Generated-skill invocation logs.

## Workflow

1. Import or call the generated network, sampler, and loss helpers.
2. Prefer PyTorch autograd if available.
3. Run fresh stochastic quadrature samples for each optimizer step.
4. Record parameter changes with `params_before` and `params_after`.
5. Evaluate relative L2 error on a fixed validation batch.
6. Mark reduced/proxy recovery honestly when the full paper budget is infeasible.

## Validation

Run:

```bash
python tests/test_training_recovery.py
```

## Limitations

The default harness is intentionally reduced and bounded. It validates mechanism fidelity, not the paper's full 50,000-step accuracy target.
