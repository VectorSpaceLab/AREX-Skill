# Factor Mining API Reference

This reference records the verified AlphaGPT model-core signatures and constants relevant to factor mining. It is intentionally runtime-oriented: use it to call or reason about the code without guessing tensor shapes, token IDs, or training artifacts.

## Covered model-core files

The factor-mining operating surface is based on these model-core modules: `model_core/vocab.py`, `model_core/ops.py`, `model_core/factors.py`, `model_core/vm.py`, `model_core/backtest.py`, `model_core/alphagpt.py`, `model_core/engine.py`, `model_core/data_loader.py`, and `model_core/config.py`.

## Constants

| Constant | Verified value | Notes |
|---|---:|---|
| `FEATURE_NAMES` | `RET`, `LIQ_SCORE`, `PRESSURE`, `FOMO`, `DEV`, `LOG_VOL` | Six base formula features. |
| `operator_offset` | `6` | First operator token ID. |
| Operator names | `ADD`, `SUB`, `MUL`, `DIV`, `NEG`, `ABS`, `SIGN`, `GATE`, `JUMP`, `DECAY`, `DELAY1`, `MAX3` | Twelve operators from `OPS_CONFIG`. |
| `vocab_size` / `FORMULA_VOCAB.size` | `18` | Six features plus twelve operators. |
| `ModelConfig.MAX_FORMULA_LEN` | `12` | Number of sampled tokens per generated formula. |
| `ModelConfig.TRAIN_STEPS` | `1000` | Full engine loop length. |
| `ModelConfig.BATCH_SIZE` | `8192` | Number of formula samples per step. |
| `ModelConfig.INPUT_DIM` | `6` | Uses `FORMULA_VOCAB.feature_count`. |
| `ModelConfig.DEVICE` | CUDA if available, else CPU | Full training can be much faster on CUDA, but offline smoke checks can run on CPU. |
| `ModelConfig.DB_URL` | Built from `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_NAME` | Defaults are for local development; raw DB setup belongs to `data-pipeline`. |

Backtest-specific defaults are held by `MemeBacktest`: `trade_size = 1000.0`, `min_liq = 500000.0`, and `base_fee = 0.0060`. These are separate from strategy-level live-trading thresholds.

## Vocabulary API

### `FormulaVocab`

A frozen dataclass with fields:

- `feature_names: tuple[str, ...]`
- `operator_names: tuple[str, ...]`

Properties:

- `feature_count -> int`
- `operator_offset -> int`
- `token_names -> tuple[str, ...]`
- `size -> int`

`FORMULA_VOCAB` is constructed from `FEATURE_NAMES` and `OPS_CONFIG` and is the canonical source for token IDs.

## Operators

`OPS_CONFIG` is an ordered list of `(name, callable, arity)` tuples. Token ID is `FORMULA_VOCAB.operator_offset + index_in_OPS_CONFIG`.

Helper functions used by operators:

- `_ts_delay(x: torch.Tensor, d: int) -> torch.Tensor`: zero-padded time delay along dimension 1.
- `_op_gate(condition: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor`: chooses `x` where `condition > 0`, otherwise `y`.
- `_op_jump(x: torch.Tensor) -> torch.Tensor`: per-token z-score jump detector, `relu(z - 3.0)`.
- `_op_decay(x: torch.Tensor) -> torch.Tensor`: current value plus two lagged terms.

## Feature engineering

### `FeatureEngineer.compute_features(raw_dict)`

Static method. Expected `raw_dict` keys are:

- `open`
- `high`
- `low`
- `close`
- `volume`
- `liquidity`
- `fdv`

Each value should be a numeric torch tensor shaped `[token_count, time]` on the intended device. Returns a tensor shaped `[token_count, 6, time]` ordered as `RET`, `LIQ_SCORE`, `PRESSURE`, `FOMO`, `DEV`, `LOG_VOL`.

`FeatureEngineer.INPUT_DIM` is `6`.

### `AdvancedFactorEngineer.compute_advanced_features(self, raw_dict)`

Instance method. Uses the same `raw_dict` keys and returns `[token_count, 12, time]` with additional volatility/momentum/range/volume-trend channels. The default formula vocabulary does not include token names for the extra six channels.

Other verified feature helpers:

- `RMSNormFactor.__init__(self, d_model, eps=1e-06)`
- `RMSNormFactor.forward(self, x)`
- `MemeIndicators.liquidity_health(liquidity, fdv)`
- `MemeIndicators.buy_sell_imbalance(close, open_, high, low)`
- `MemeIndicators.fomo_acceleration(volume, window=5)`
- `MemeIndicators.pump_deviation(close, window=20)`
- `MemeIndicators.volatility_clustering(close, window=10)`
- `MemeIndicators.momentum_reversal(close, window=5)`
- `MemeIndicators.relative_strength(close, high, low, window=14)`

## StackVM execution

### `StackVM.execute(self, formula_tokens, feat_tensor)`

Inputs:

- `formula_tokens`: iterable of integer-like token IDs.
- `feat_tensor`: torch tensor shaped `[token_count, feature_count, time]`.

Returns:

- A tensor shaped `[token_count, time]` when the RPN formula is valid and leaves exactly one value on the stack.
- `None` when a token is unknown, a feature token is outside `feat_tensor.shape[1]`, the stack underflows for an operator arity, execution raises an exception, or the final stack length is not exactly one.

Runtime cleanup:

- After each operator call, if the result contains NaN or Inf, the VM applies finite replacement with `nan=0.0`, `posinf=1.0`, and `neginf=-1.0`.

## Backtest scoring

### `MemeBacktest.evaluate(self, factors, raw_data, target_ret)`

Inputs:

- `factors`: tensor shaped `[token_count, time]`; usually output from `StackVM.execute(...)`.
- `raw_data`: dictionary that must at least include `liquidity` shaped `[token_count, time]`.
- `target_ret`: tensor shaped `[token_count, time]`.

Returns:

- `(final_fitness, mean_cumulative_return)`.
- `final_fitness` is a torch scalar tensor based on median per-token score.
- `mean_cumulative_return` is a Python float.

Scoring steps:

- `signal = sigmoid(factors)`.
- Position is active when `signal > 0.85` and liquidity passes the backtest minimum.
- Turnover pays one-way base fee plus liquidity-impact slippage.
- Large negative time-step returns are penalized.
- Less than five active positions receives a `-10` activity penalty.

## Data loader

### `CryptoDataLoader.__init__(self)`

Creates a SQLAlchemy engine from `ModelConfig.DB_URL` and initializes:

- `feat_tensor = None`
- `raw_data_cache = None`
- `target_ret = None`
- `addresses = []`

### `CryptoDataLoader.load_data(self, limit_tokens=500)`

Loads up to `limit_tokens` token addresses, reads OHLCV/liquidity/FDV rows, pivots to token-by-time tensors, computes the feature tensor with `FeatureEngineer.compute_features(...)`, and prepares target returns. Raises `ValueError("No tokens found.")` when the token query is empty.

## AlphaGPT model components

### `AlphaGPT.__init__(self)` and `AlphaGPT.forward(self, idx)`

`AlphaGPT.forward(idx)` expects integer token IDs shaped `[batch, sequence_length]` and returns:

```python
logits, value, task_probs = model(idx)
```

- `logits`: next-token distribution logits over the 18-token vocabulary.
- `value`: critic scalar per batch item.
- `task_probs`: multi-task routing probabilities from the MTP head.

Important model defaults:

- `d_model = 64`
- token embedding size = `FORMULA_VOCAB.size`
- positional embedding length = `MAX_FORMULA_LEN + 1`
- two looped transformer layers
- four attention heads
- loop count per layer = 3
- RMSNorm, QK normalization, SwiGLU feed-forward, and multi-task pooling head are used.

Other verified model signatures:

- `NewtonSchulzLowRankDecay.__init__(self, named_parameters, decay_rate=0.001, num_iterations=5, target_keywords=None)`
- `NewtonSchulzLowRankDecay.step(self)`
- `StableRankMonitor.__init__(self, model, target_keywords=None)`
- `StableRankMonitor.compute(self)`
- `RMSNorm.__init__(self, d_model, eps=1e-06)`
- `RMSNorm.forward(self, x)`
- `QKNorm.__init__(self, d_model, eps=1e-06)`
- `QKNorm.forward(self, q, k)`
- `SwiGLU.__init__(self, d_in, d_ff)`
- `SwiGLU.forward(self, x)`
- `MTPHead.__init__(self, d_model, vocab_size, num_tasks=3)`
- `MTPHead.forward(self, x)`
- `LoopedTransformerLayer.__init__(self, d_model, nhead, dim_feedforward, num_loops=3, dropout=0.1)`
- `LoopedTransformerLayer.forward(self, x, mask=None, is_causal=False)`
- `LoopedTransformer.__init__(self, d_model, nhead, num_layers, dim_feedforward, num_loops=3, dropout=0.1)`
- `LoopedTransformer.forward(self, x, mask=None, is_causal=False)`

## Training engine

### `AlphaEngine.__init__(self, use_lord_regularization=True, lord_decay_rate=0.001, lord_num_iterations=5)`

Constructor behavior:

- Loads DB-backed data immediately.
- Builds `AlphaGPT` on `ModelConfig.DEVICE`.
- Creates AdamW optimizer with learning rate `1e-3`.
- Enables LoRD by default with target keywords `q_proj`, `k_proj`, `attention`, and `qk_norm`.
- Creates `StackVM` and `MemeBacktest`.
- Initializes `best_score`, `best_formula`, and `training_history`.

### `AlphaEngine.train(self)`

Runs the full formula-mining training loop for `TRAIN_STEPS` and writes:

- `best_meme_strategy.json`
- `training_history.json`

Because the constructor loads SQL data and the train method performs a large sampling loop, prefer the bundled synthetic smoke script for quick checks.
