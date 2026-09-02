---
name: sample_factory_appo_update
description: Compute reduced APPO update evidence with PPO clipping and V-trace-style value correction for asynchronous policy lag.
---

# Sample Factory APPO Update

Use this skill when a recovery needs deterministic evidence that asynchronous trajectory data is corrected with the paper's APPO mechanisms: PPO clipping plus V-trace-style truncated-importance value targets.

Do not use the reduced scalar optimizer as proof of full neural-network training.

## Inputs
- Rewards, discounts, values, and bootstrap value.
- Behavior and target log probabilities.
- PPO clip threshold.
- V-trace rho and c truncation thresholds.
- Optional scalar policy parameter and learning rate for a tiny optimizer step.

## Outputs
- Importance ratios and clipped ratios.
- Corrected value targets.
- Policy loss and value loss.
- Optimizer trace with parameter and loss before/after.

## Workflow
1. Compute importance ratios from target minus behavior log probabilities.
2. Clip ratios for PPO surrogate loss.
3. Compute temporal-difference deltas and apply truncated rho/c weights.
4. Build value targets by backward recursion from the bootstrap value.
5. Compute policy and value losses.
6. For reduced recovery, update a scalar parameter with a deterministic gradient step and record `params_before` and `params_after`.

## Validation
Run:

```bash
python scripts/appo_update.py
python tests/test_appo_update.py
```

## Limitations
This skill validates the algorithmic contract, not production-scale GPU training or recurrent policies.
