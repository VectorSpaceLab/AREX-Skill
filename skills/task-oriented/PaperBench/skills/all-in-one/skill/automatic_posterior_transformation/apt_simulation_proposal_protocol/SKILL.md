---
name: apt_simulation_proposal_protocol
description: Run APT-style sequential simulator proposal rounds with auditable prior, proposal, observation, and update records for likelihood-free inference recovery.
---

# APT Simulation Proposal Protocol

Use this skill when you need to set up or audit a bounded Automatic Posterior Transformation recovery experiment that draws simulator parameters from a prior or adaptive proposal and records which proposal generated each simulation. Do not use it as a posterior-density trainer by itself; pair it with an APT transformation or atomic-loss skill for training.

## Inputs

- A prior distribution with a name, parameters, sampler, log density, and optional support check.
- A simulator callable or deterministic simulator specification.
- Observed data `x_o`.
- A current posterior estimate at `x_o` for proposal updates.
- Round count, simulations per round, and deterministic seed.

## Outputs

- Round records with `round_index`, `theta`, `x`, `proposal_name`, `proposal_parameters`, and `seed`.
- Proposal update records linking `proposal_r` to `proposal_{r+1}`.
- Source metadata showing the simulator and proposal parameters used for each item.

## Workflow

1. Start with `proposal_1 = prior`.
2. For each round, draw parameters from the current proposal and run the simulator.
3. Preserve the proposal parameters inside every simulation record.
4. Train or update the posterior estimator using APT loss outside this skill.
5. Construct the next proposal from the posterior estimate at `x_o`.
6. If the prior has bounded support, reject or clip out-of-support proposal samples and record the policy.

## Deterministic Helper

The script `scripts/sequential_protocol.py` provides a scalar Gaussian helper for reduced recovery:

```bash
python scripts/sequential_protocol.py --output /tmp/protocol.json
```

It simulates a first round from a broad prior and a second round from a posterior-derived proposal. The helper is intentionally small; its purpose is to validate proposal provenance and sequential update mechanics, not to reproduce paper-scale neural training.

## Validation

Run:

```bash
python tests/test_sequential_protocol.py
```

The tests verify first-round prior use, second-round proposal use, deterministic records, and valid support handling.

## Limitations

- The helper supports scalar Gaussian examples only.
- It does not implement MDN, MAF, CNN, or RNN density estimators.
- It does not claim full paper recovery unless combined with executable APT loss and evaluation evidence.
