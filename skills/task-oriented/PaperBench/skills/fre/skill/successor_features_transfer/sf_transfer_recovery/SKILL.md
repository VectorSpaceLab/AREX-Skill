---
name: sf_transfer_recovery
description: Run a bounded successor-features plus GPI transfer recovery experiment for changing linear-reward RL tasks.
---

# Successor-Feature Transfer Recovery Harness

Use this skill to validate a reduced, mechanism-faithful recovery of Successor Features for Transfer in Reinforcement Learning. It should be used after successor-feature and GPI utilities exist and before claiming the paper mechanism has been recovered.

## Inputs

- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing `successor_feature_model` and `generalized_policy_improvement`.
- Soft-mode permission for a reduced/proxy experiment when full four-room or MuJoCo recovery is not feasible.

## Outputs

- `recovery/recovery_result.json` with `mean_transfer_advantage`.
- `recovery/logs/generated_data_item.json` describing the gridworld and reward weights.
- `recovery/logs/generated_skill_invocations.json` proving generated modules were imported/called.
- `recovery/logs/training_trace.json` recording exact dynamic-programming/source-policy construction traces.

## Workflow

1. Construct a small deterministic shared-dynamics gridworld with feature-bearing terminal goals.
2. Define source reward weights and held-out transfer weights.
3. Derive source policies using exact value iteration for each source reward.
4. Compute successor features for each source policy using the generated successor-feature module.
5. Reweight source successor features for each held-out reward and apply generated GPI selection.
6. Evaluate GPI and a restricted single-source baseline on each held-out reward.
7. Save numeric returns, mechanism checks, and validation-ready artifacts.

## Validation

Run:

```bash
python scripts/run_sf_transfer_recovery.py --attempt-dir <attempt_dir> --skills-root <generated_skills_root>
python tests/test_recovery_harness.py
```

## Limitations

This is a reduced/proxy recovery. It does not reproduce the paper's four-room continuous-navigation or MuJoCo experiments, but it preserves the core mechanism of shared dynamics, changing linear rewards, successor-feature reweighting, and GPI transfer.
