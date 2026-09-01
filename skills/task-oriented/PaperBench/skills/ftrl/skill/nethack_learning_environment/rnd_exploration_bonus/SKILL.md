---
name: rnd_exploration_bonus
description: Compute Random Network Distillation novelty bonuses and simple predictor updates for symbolic state features.
---

# Rnd Exploration Bonus

## When To Use
Use this skill when reconstructing or testing the NetHack Learning Environment paper mechanisms in a bounded recovery setting. It is appropriate for symbolic NLE-style observations, task/action contracts, exploration bonuses, trainable baseline proxies, or validation harnesses depending on the module name.

## Inputs
- JSON-compatible records produced by upstream NLE recovery modules.
- Tiny deterministic fixtures for smoke tests or reduced recovery.
- Paper-derived target metadata when the module contributes to recovery evidence.

## Outputs
- Compact Python dictionaries or scalar values that can be serialized into Distiller recovery logs.
- Explicit errors for malformed input instead of silent fallback behavior.

## Workflow
1. Confirm the input contract before computing downstream values.
2. Preserve the paper mechanism named in the module document rather than copying repository layout.
3. Use the script in `scripts/` for deterministic behavior and record outputs in recovery logs.
4. During recovery, do not read the original NLE repository; rely on paper/module/skill artifacts only.

## Validation
Run `python -m pytest tests` from this skill directory, or validate through the Distiller `validate_skill_tree.py --run-tests` command. The tests use only the Python standard library and deterministic fixtures.

## Limitations
This skill supports reduced/proxy recovery. It does not claim to reproduce full distributed IMPALA training or a compiled NetHack simulator by itself.
