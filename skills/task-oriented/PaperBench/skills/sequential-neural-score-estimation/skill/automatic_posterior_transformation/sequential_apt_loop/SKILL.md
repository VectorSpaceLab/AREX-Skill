---
name: sequential_apt_loop
description: Run a bounded sequential APT proxy loop that updates proposals after corrected atomic training.
---

# Sequential APT Loop

Use this skill when a recovery needs to demonstrate the sequential part of Automatic Posterior Transformation under a bounded simulator. It should not be represented as full paper reproduction unless the original benchmark and neural density estimator stack are available.

## Inputs
- Observed scalar datum, simulator noise, round count, and simulations per round.
- Prior and initial proposal parameters.
- Atomic training helper implementing proposal-corrected loss.

## Outputs
- Per-round proposal and posterior estimate logs.
- Final posterior mean estimate and absolute error against the analytic Gaussian posterior.
- Training trace with parameter movement and loss values.

## Workflow
1. Begin with the prior as the initial proposal.
2. Generate deterministic low-discrepancy simulator samples around each proposal.
3. Train the atomic score model on accumulated atom sets.
4. Estimate the posterior mean at the observation from corrected atom probabilities.
5. Update the next proposal toward that posterior estimate and repeat.

## Validation
Run `python scripts/sequential_proxy.py --self-test`. The test checks that the final proposal moves toward the analytic posterior and that an optimizer step was executed.

## Limitations
The script uses a one-dimensional Gaussian simulator as a mechanism-faithful proxy, not the paper's full two-moons or SLCP benchmarks.
