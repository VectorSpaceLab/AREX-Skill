---
name: factor-mining
description: "Operate AlphaGPT factor-token mining, formula execution, feature
  engineering, backtest scoring, and training artifacts safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Factor Mining

Use this sub-skill when the task is about AlphaGPT's factor-token language,
formula validation, synthetic factor execution, model-core training loop, LoRD
regularization in the AlphaGPT model, or interpreting `best_meme_strategy.json`
and `training_history.json`.

## Do not route here for

- Raw token/OHLCV database population; use [data-pipeline](../data-pipeline/SKILL.md).
- Live consumption of a mined formula by the runner, wallet execution, risk controls, or portfolio state; use [live-strategy](../live-strategy/SKILL.md).
- Dashboard display and monitoring; use [dashboard-ops](../dashboard-ops/SKILL.md).
- Standalone `times.py` or `lord/experiment.py` research unless the user explicitly selects optional experiments; see [../../references/experiments-and-exclusions.md](../../references/experiments-and-exclusions.md).

## Read or run

1. Read [references/training-and-formulas.md](references/training-and-formulas.md) for the formula vocabulary, RPN examples, feature/operator tables, training sequence, and JSON artifacts.
2. Read [references/api-reference.md](references/api-reference.md) for verified signatures, constants, tensor contracts, and class responsibilities.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when `StackVM.execute(...)` returns `None`, factors are constant, DB rows are missing, training is slow, or GPU/backend expectations are unclear.
4. Run [scripts/alpha_gpt_formula_smoke.py](scripts/alpha_gpt_formula_smoke.py) for a safe deterministic formula smoke that uses synthetic tensors and no database, API keys, Solana RPC, or trading paths.
5. Use the root [environment checker](../../scripts/alpha_gpt_env_check.py) with `--scope factor` for import checks.

## Safe default workflow

1. Start with the vocabulary: six feature tokens followed by twelve operators, verified size `18` and operator offset `6`.
2. Validate the formula as reverse Polish notation before using it in training or live strategy.
3. Use synthetic tensors to confirm stack behavior and finite outputs.
4. Confirm full training prerequisites only after the formula path is understood: populated SQL tables, PyTorch runtime, and acceptable output directory for `best_meme_strategy.json` and `training_history.json`.
5. Treat CUDA as a performance/backend detail, not proof that the formula grammar is valid.
6. Do not run the full `AlphaEngine.train()` loop as a quick smoke check; it expects DB data, samples large batches, may run long, and writes artifacts.

## Core runtime facts

- `FeatureEngineer.compute_features(raw_dict)` returns `[token_count, 6, time]` for raw `open`, `high`, `low`, `close`, `volume`, `liquidity`, and `fdv` tensors.
- `AdvancedFactorEngineer.compute_advanced_features(self, raw_dict)` returns twelve channels, but the verified formula vocabulary still exposes only the six base feature tokens.
- `StackVM.execute(self, formula_tokens, feat_tensor)` returns a single factor tensor or `None` when the RPN stack is invalid.
- `MemeBacktest.evaluate(self, factors, raw_data, target_ret)` converts factor logits to sigmoid signals and scores median risk-adjusted performance.
- `AlphaEngine.__init__(self, use_lord_regularization=True, lord_decay_rate=0.001, lord_num_iterations=5)` wires the loader, model, optimizer, StackVM, and backtester.
- `AlphaEngine.train(self)` writes `best_meme_strategy.json` and `training_history.json` in the process working directory.

## Quick route map

| User intent | Read/run | Notes |
| --- | --- | --- |
| "What do token IDs mean?" | [references/training-and-formulas.md](references/training-and-formulas.md) | Includes feature/operator table and RPN examples. |
| "Does this formula execute?" | [scripts/alpha_gpt_formula_smoke.py](scripts/alpha_gpt_formula_smoke.py) | Uses synthetic tensors; accepts token IDs or names. |
| "Why did the VM return None?" | [references/troubleshooting.md](references/troubleshooting.md) | Stack underflow, bad IDs, leftover operands, and feature mismatch. |
| "How does training produce best_meme_strategy.json?" | [references/training-and-formulas.md](references/training-and-formulas.md) | Covers DB-backed loader, rewards, LoRD, and outputs. |
| "What are the API signatures?" | [references/api-reference.md](references/api-reference.md) | Verified signatures and config constants. |

## Verification stance

The bundled formula smoke is the default assertion-backed validation path. Full
native `model_core/engine.py` training is a DB-dependent, long-running candidate
and should remain skipped unless the user supplies a populated fixture database
or explicitly authorizes a training run.
