# Training And Formula Workflow

This reference covers AlphaGPT's model-core workflow: raw market tensors become six base features, a formula-token sequence is interpreted as reverse Polish notation (RPN), the resulting factor signal is scored by a meme-token backtest, and the AlphaGPT generator is trained to produce better formulas.

## Ownership boundaries

- This sub-skill starts after OHLCV/liquidity/FDV rows are already available to the model loader.
- If the task is to fetch Birdeye/DexScreener data, create SQL tables, or diagnose raw DB population, route to `data-pipeline`.
- If the task is to load a trained formula in a live bot, risk-check a signal, or trade through Solana/Jupiter, route to `live-strategy`.

## Formula vocabulary

`FormulaVocab` combines six feature tokens followed by twelve operator tokens. The verified size is 18 and the operator offset is 6.

### Feature tokens

Feature tensors are shaped `[token_count, feature_count, time]` for the default engine. `FeatureEngineer.compute_features(raw_dict)` returns `[token_count, 6, time]`.

| ID | Token | Raw inputs | Meaning | Normalization in default engineer |
|---:|---|---|---|---|
| 0 | `RET` | `close` | Log return: `log(close / roll(close, 1))` | Robust median/MAD clamp to `[-5, 5]` |
| 1 | `LIQ_SCORE` | `liquidity`, `fdv` | Liquidity-to-FDV health, scaled and clamped to `[0, 1]` | Not robust-normalized |
| 2 | `PRESSURE` | `open`, `high`, `low`, `close` | Buy/sell imbalance from candle body over high-low range | Not robust-normalized |
| 3 | `FOMO` | `volume` | Volume-change acceleration, clamped to `[-5, 5]` before normalization | Robust median/MAD clamp |
| 4 | `DEV` | `close` | Pump deviation from a rolling moving average | Robust median/MAD clamp |
| 5 | `LOG_VOL` | `volume` | `log1p(volume)` | Robust median/MAD clamp |

`AdvancedFactorEngineer.compute_advanced_features(raw_dict)` returns twelve channels: the six base concepts plus volatility clustering, momentum reversal, relative strength, high-low range, close position, and volume trend. The verified token vocabulary still names only the six base features; do not treat advanced feature channels 6-11 as valid formula tokens unless the code is extended with a matching vocabulary.

### Operator tokens

Operators execute over tensors shaped `[token_count, time]`. The StackVM pops the required number of operands, reverses them back to source order, applies the operator, replaces NaN/Inf with finite values, and pushes the result.

| ID | Token | Arity | Semantics |
|---:|---|---:|---|
| 6 | `ADD` | 2 | `x + y` |
| 7 | `SUB` | 2 | `x - y` |
| 8 | `MUL` | 2 | `x * y` |
| 9 | `DIV` | 2 | `x / (y + 1e-6)` |
| 10 | `NEG` | 1 | `-x` |
| 11 | `ABS` | 1 | `abs(x)` |
| 12 | `SIGN` | 1 | `sign(x)` |
| 13 | `GATE` | 3 | `condition > 0` selects `x`, otherwise `y` |
| 14 | `JUMP` | 1 | ReLU of a per-token z-score above 3 |
| 15 | `DECAY` | 1 | `x + 0.8 * delay1(x) + 0.6 * delay2(x)` |
| 16 | `DELAY1` | 1 | One-step time delay with zeros padded at the start |
| 17 | `MAX3` | 1 | Max of current, one-step delayed, and two-step delayed values |

## RPN examples

Formula tokens are reverse Polish notation: operands appear before the operator that consumes them.

| Human formula | Token names | Token IDs | Stack result |
|---|---|---|---|
| `RET + LOG_VOL` | `RET LOG_VOL ADD` | `[0, 5, 6]` | Adds return and log-volume features. |
| `abs(LIQ_SCORE - DEV)` | `LIQ_SCORE DEV SUB ABS` | `[1, 4, 7, 11]` | Subtracts deviation from liquidity score, then takes absolute value. |
| `DECAY(FOMO)` | `FOMO DECAY` | `[3, 15]` | Smooths recent volume acceleration with lagged values. |
| `PRESSURE > 0 ? RET : LOG_VOL` | `PRESSURE RET LOG_VOL GATE` | `[2, 0, 5, 13]` | Uses pressure as the condition for a gated choice. |
| `MAX3(SIGN(RET * PRESSURE))` | `RET PRESSURE MUL SIGN MAX3` | `[0, 2, 8, 12, 17]` | Multiplies, signs, then keeps a rolling max over current/two lags. |

A valid formula must leave exactly one tensor on the stack. Underflow, unknown token IDs, a feature ID that is outside the supplied feature tensor, or leftover stack entries cause `StackVM.execute(...)` to return `None`.

## Formula JSON artifacts

### `best_meme_strategy.json`

The training engine writes the best formula to `best_meme_strategy.json` in the current process working directory. The current engine writes a bare JSON list of integer token IDs:

```json
[0, 5, 6]
```

The live strategy runner is backward-compatible with either a bare list or an object containing a `formula` key:

```json
{"formula": [0, 5, 6]}
```

Keep the list length at or below `MAX_FORMULA_LEN` (12 by default). Token IDs must be integers in `[0, 17]` for the verified default vocabulary.

### `training_history.json`

The training engine also writes a history object with array fields:

```json
{
  "step": [0],
  "avg_reward": [-1.23],
  "best_score": [0.42],
  "stable_rank": [3.14]
}
```

`stable_rank` is appended only when LoRD regularization is enabled and the current step matches the rank-monitor logging interval.

## Training and backtest sequence

1. `CryptoDataLoader.load_data(limit_tokens=500)` reads token addresses from the `tokens` table, loads OHLCV/liquidity/FDV rows from the `ohlcv` table, pivots columns to tensors, forward-fills then zero-fills missing values, computes the six-feature tensor, and builds `target_ret = log(open[t+2] / open[t+1])` with the final two time steps set to zero.
2. `AlphaEngine.__init__(use_lord_regularization=True, lord_decay_rate=0.001, lord_num_iterations=5)` constructs the loader, `AlphaGPT` model, AdamW optimizer, optional Newton-Schulz LoRD regularizer, `StackVM`, and `MemeBacktest`.
3. Each training step starts from a one-token input, samples up to `MAX_FORMULA_LEN` tokens from the model, and evaluates each sampled sequence against the loaded feature tensor.
4. Reward assignment is intentionally harsh: invalid formulas receive `-5.0`; factors with `std < 1e-4` receive `-2.0`; valid non-constant factors are passed to `MemeBacktest.evaluate(...)`.
5. Rewards are normalized into advantages, policy-gradient loss is applied to the sampled log probabilities, AdamW steps the model, and LoRD low-rank decay steps selected attention/QK parameters when enabled.
6. The engine tracks average reward, best score, and optional stable rank. At completion it writes `best_meme_strategy.json` and `training_history.json` in the process working directory.

## Backtest scoring behavior

`MemeBacktest.evaluate(factors, raw_data, target_ret)` converts factor logits to `sigmoid` signals and enters a position only when `signal > 0.85` and liquidity is above the backtest minimum. It subtracts one-way base fee plus liquidity-impact slippage, penalizes large drawdown time steps, and sets scores to `-10` for formulas that create fewer than five active positions. The returned tuple is `(final_fitness, mean_cumulative_return)`, where `final_fitness` is a tensor median score and `mean_cumulative_return` is a Python float.

The backtest is a formula-mining reward proxy, not a guarantee that a formula is safe for live trading. Live use requires separate risk, liquidity, wallet, and execution checks.

## Safe local validation

Use the bundled helper for deterministic grammar and tensor-shape checks:

```bash
python scripts/alpha_gpt_formula_smoke.py --formula "RET LOG_VOL ADD" --list-vocab
```

The helper uses synthetic tensors by default. It does not read SQL, call APIs, touch wallets, run Solana RPC, or write strategy artifacts.
