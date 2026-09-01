---
name: sample_factory_pbt_self_play
description: Specify Sample Factory-style multi-policy self-play assignments and population-based exploit/mutate decisions.
---

# Sample Factory PBT Self-Play

Use this skill when planning or auditing Sample Factory-style self-play experiments with multiple policies and population-based training.

Do not use it for single-policy throughput recovery unless the recovery explicitly validates self-play or population management.

## Inputs
- Policy ids and hyperparameters.
- Episode agent ids and available policy ids.
- Policy scores or win rates.
- Replacement threshold and mutation factors.

## Outputs
- Episode policy-assignment log.
- Ranked population summary.
- Exploit/mutate decisions.
- Mutated hyperparameters clipped to bounds.

## Workflow
1. Assign each agent in an episode to a policy id while keeping rollout workers policy-agnostic.
2. Rank policies by win rate or task score at the mutation interval.
3. Mark weak policies below a threshold fraction of the best policy for replacement.
4. Copy hyperparameters from the best policy to replaced policies.
5. Apply deterministic or seeded multiplicative mutations within configured bounds.
6. Record decisions separately from environment rewards and model updates.

## Validation
Run:

```bash
python scripts/pbt_self_play.py
python tests/test_pbt_self_play.py
```

## Limitations
This skill models population-control decisions. It does not train policies or simulate VizDoom matches.
