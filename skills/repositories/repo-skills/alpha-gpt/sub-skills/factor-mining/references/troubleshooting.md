# Factor Mining Troubleshooting

Use this reference to diagnose common failures in AlphaGPT formula mining without accidentally running database, network, wallet, or live-trading flows.

## `StackVM.execute(...)` returns `None`

Likely causes:

| Symptom | Cause | Fix |
|---|---|---|
| Formula starts with an operator, such as `ADD RET LOG_VOL` | RPN stack underflow; binary operators need two prior operands | Use RPN order: `RET LOG_VOL ADD`. |
| Formula leaves more than one stack value, such as `RET LOG_VOL` | No operator consumed the two operands | Add an operator or remove the extra operand. |
| Unknown integer token, such as `18` or `99` | Valid token IDs are `0..17` for the default vocabulary | Decode with `FORMULA_VOCAB.token_names` or run the smoke helper with `--list-vocab`. |
| Feature token is outside the supplied feature dimension | The VM rejects feature IDs `>= feat_tensor.shape[1]` | Use `FeatureEngineer.compute_features(...)` for six base features, or extend vocabulary and tensor shape together. |
| `GATE` fails | `GATE` has arity 3: `condition x y GATE` | Example: `PRESSURE RET LOG_VOL GATE`. |
| Full training emits many invalid rewards | Sampling is unconstrained and many length-12 token sequences are not valid RPN formulas | This is expected; invalid formulas receive `-5.0` and the policy learns from rewards. |

Safe check:

```bash
python scripts/alpha_gpt_formula_smoke.py --formula "RET LOG_VOL ADD" --list-vocab
```

The helper returns nonzero for a requested invalid formula.

## Constant signal penalties

The training loop rejects formulas whose executed factor has very low variation:

```python
if res.std() < 1e-4:
    rewards[i] = -2.0
```

Common constant-producing formulas include subtracting a feature from itself, saturating all values through a sign/gate pattern, or using a mostly zero delayed/jump signal on a tiny fixture.

Fixes:

- Prefer formulas that combine at least two independently varying features.
- Inspect both raw factor standard deviation and `sigmoid(factor)` activity.
- Remember that grammar-valid is not reward-valid: a valid VM result can still be a poor or inactive factor.

## NaN or Inf in factor results

The VM guards operator outputs with finite replacement:

- NaN becomes `0.0`
- positive Inf becomes `1.0`
- negative Inf becomes `-1.0`

This keeps training from crashing but can hide a broken formula or bad input tensor. Frequent cleanup usually means:

- raw OHLCV/liquidity/FDV tensors contain zeros, missing values, or extreme values;
- `DIV` is using a near-zero denominator despite the `+1e-6` guard;
- robust normalization is receiving all-constant or heavily missing series;
- advanced features are being used without matching vocabulary assumptions.

Fixes:

- Check raw tensor shapes and finite values before feature computation.
- Use the default `FeatureEngineer` for formulas unless the vocabulary has been extended.
- Treat finite replacement as a safety guard, not proof that the factor is meaningful.

## Empty database or no token rows

`CryptoDataLoader.load_data(limit_tokens=500)` queries token addresses first. If no rows are found, it raises:

```text
ValueError: No tokens found.
```

This is not a model or formula failure. Route raw database population, SQL schema setup, Birdeye/DexScreener ingestion, and API-key/database connectivity issues to `data-pipeline`.

Factor-mining recovery steps:

1. Do not run the training engine repeatedly against an empty DB.
2. Confirm that the downstream environment has populated `tokens` and `ohlcv` rows with columns needed by the loader: `time`, `address`, `open`, `high`, `low`, `close`, `volume`, `liquidity`, and `fdv`.
3. Once data exists, run a small loader check before launching full training.
4. For pure formula grammar work, use the bundled synthetic smoke helper instead of SQL.

## Full training is slow or appears stuck

Expected workload:

- `TRAIN_STEPS = 1000`
- `BATCH_SIZE = 8192`
- `MAX_FORMULA_LEN = 12`
- each sampled sequence is interpreted by Python-level StackVM logic and then backtested

CPU can run tiny synthetic checks, but practical full training is expensive. CUDA is optional for smoke verification but useful for real training throughput. A progress bar should advance through the configured training steps; if it does not, inspect DB query time, tensor sizes, and device memory before assuming the model is broken.

Safer alternatives:

- Use `scripts/alpha_gpt_formula_smoke.py` for grammar/tensor checks.
- Reduce constants only in a disposable experiment, not as a documented repo default.
- Run full training from the directory where strategy/history JSON outputs should be written.

## Strategy JSON missing or wrong shape

`best_meme_strategy.json` is produced by `AlphaEngine.train()` and consumed by the live strategy runner. The current engine writes a bare list of token IDs, while the runner also accepts an object containing `formula` for compatibility.

Valid examples:

```json
[0, 5, 6]
```

```json
{"formula": [0, 5, 6]}
```

Invalid examples:

- token names instead of IDs in the JSON file;
- IDs outside `0..17`;
- a list that is valid JSON but invalid RPN;
- a formula longer than `MAX_FORMULA_LEN`.

Live use of this file belongs to `live-strategy`; this sub-skill only validates formula semantics and training output shape.

## Solana dependency errors are usually irrelevant here

A verified inspection found that a newer Solana Python SDK line can break imports used by the execution layer, while a compatible pin around `solana==0.36.12` with `websockets==15.0.1` preserved execution imports and Streamlit compatibility.

For factor mining:

- Solana RPC, Jupiter quote/swap APIs, wallet private keys, and token-account imports are not needed for `FeatureEngineer`, `StackVM`, `MemeBacktest`, `AlphaGPT`, or the synthetic formula smoke helper.
- Do not troubleshoot formula failures by changing wallet or RPC configuration.
- Route Solana/Jupiter import, signing, transaction, slippage, or wallet issues to `live-strategy`.

## Package/import confusion

AlphaGPT is a source tree with import roots such as `model_core`, not a packaged distribution with package metadata. If a later environment cannot import `model_core`, ensure the source root containing `model_core/` is on `PYTHONPATH` or run commands from the source root. Do not hard-code construction-machine paths into scripts or skill files.

The bundled formula smoke helper is self-contained and does not require importing `model_core` unless `--repo-root` is explicitly supplied for comparison against a checkout.
