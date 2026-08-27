# AlphaGPT Live Strategy Reference

This reference covers AlphaGPT's live strategy loop and local state. It is intentionally operational but guarded: live trading requires explicit user authorization and the execution-safety checks in [execution-safety.md](execution-safety.md).

## Prerequisites

Before considering a live run, confirm all of the following:

- The AlphaGPT source tree is available to the runtime. It is not packaged as a Python distribution, so run from a copy of the source tree or otherwise make the import roots importable: `data_pipeline`, `model_core`, `strategy_manager`, and `execution`.
- Core dependencies from the main requirements are installed. Safe inspection verified the live-strategy import path with `solana==0.36.12` and `websockets==15.0.1`; newer `solana` releases can remove APIs used by the trader adapter.
- A populated market database exists for `CryptoDataLoader.load_data(limit_tokens=300)`. If database ingestion or schema setup is the issue, route to [data-pipeline](../../data-pipeline/SKILL.md).
- A valid `best_meme_strategy.json` exists in the working directory from which the strategy runner will be launched. If the formula needs to be trained or repaired, route to [factor-mining](../../factor-mining/SKILL.md).
- Wallet, RPC, funds, and trading authorization are present only for an intentional live run. For details, read [execution-safety.md](execution-safety.md).
- Any existing `portfolio_state.json` has been reviewed or backed up before switching between dry-run, paper-review, and live trading contexts.
- The STOP signal file is absent when starting a new live loop unless the goal is to verify that the loop exits immediately.

Use the bundled offline checker before live use:

```bash
python scripts/alpha_gpt_trading_config_check.py --help
python scripts/alpha_gpt_trading_config_check.py --strategy-json best_meme_strategy.json
python scripts/alpha_gpt_trading_config_check.py --live --strategy-json best_meme_strategy.json
```

The checker never calls RPC, Jupiter, Solana, Postgres, or the AlphaGPT runner.

## Strategy JSON accepted by `StrategyRunner`

`StrategyRunner.__init__` opens `best_meme_strategy.json` and accepts either of these shapes:

```json
[0, 1, 6]
```

or:

```json
{"formula": [0, 1, 6]}
```

The list is an RPN-style formula token sequence consumed by `StackVM.execute(self, formula_tokens, feat_tensor)`. The live runner accepts a raw JSON list directly; if the top-level value is an object, it reads the object's `formula` field. Missing files stop the runner at startup. Missing or malformed `formula` values can make inference return no signal and should be fixed before any live attempt.

The source vocabulary uses integer token ids. A concise live-run validation map is:

| Token ids | Meaning |
| --- | --- |
| `0..5` | Feature inputs: `RET`, `LIQ_SCORE`, `PRESSURE`, `FOMO`, `DEV`, `LOG_VOL` |
| `6..17` | Operators: `ADD`, `SUB`, `MUL`, `DIV`, `NEG`, `ABS`, `SIGN`, `GATE`, `JUMP`, `DECAY`, `DELAY1`, `MAX3` |

For full formula grammar and training workflow details, use [factor-mining](../../factor-mining/SKILL.md).

## Loop lifecycle

`StrategyRunner.run_loop(self)` is an asynchronous live loop. Its high-level lifecycle is:

1. Construction creates `DataManager`, `PortfolioManager`, `RiskEngine`, `SolanaTrader`, `StackVM`, and `CryptoDataLoader` instances; initializes `token_map`; reads the STOP signal path from `STOP_SIGNAL_PATH` or defaults to `STOP_SIGNAL`; loads `best_meme_strategy.json`.
2. `initialize()` opens data resources and reads wallet SOL balance through the trader's RPC client. This is a live-service operation and should not be used as an offline smoke test.
3. Each `run_loop()` cycle checks the STOP signal before major actions.
4. Every 15 minutes it calls `DataManager.pipeline_sync_daily()` to refresh market data. This can call external data services and database writes.
5. It loads the latest feature tensor with `CryptoDataLoader.load_data(limit_tokens=300)` and builds an address-to-tensor-index map.
6. It calls `monitor_positions()` to evaluate stop loss, take profit, trailing stop, and AI-exit conditions for current positions.
7. If open positions are below the configured maximum, it calls `scan_for_entries()`; otherwise it skips entry scanning.
8. It sleeps so normal cycles run about once per minute; global loop exceptions are logged and followed by a 30-second sleep.
9. `shutdown()` closes data, trader, and risk resources.

Do not treat this lifecycle as a recommended command sequence. It describes what the code does after live trading has already been authorized.

## Strategy constants and thresholds

AlphaGPT's live strategy constants are embedded in `StrategyConfig`:

| Constant | Default | Operational meaning |
| --- | ---: | --- |
| `MAX_OPEN_POSITIONS` | `3` | Do not scan for new entries after three open positions. |
| `ENTRY_AMOUNT_SOL` | `2.0` | Fixed SOL size requested for each new entry before wallet-balance safety margin. |
| `STOP_LOSS_PCT` | `-0.05` | Sell 100% when current price is at or below -5% PnL. |
| `TAKE_PROFIT_Target1` | `0.10` | First profit target at +10% PnL. |
| `TP_Target1_Ratio` | `0.5` | Sell 50% at the first profit target and mark the remaining position as `is_moonbag`. |
| `TRAILING_ACTIVATION` | `0.05` | Enable trailing-stop logic after max gain exceeds +5%. |
| `TRAILING_DROP` | `0.03` | Sell 100% when drawdown from highest price exceeds 3% after activation. |
| `BUY_THRESHOLD` | `0.85` | Minimum sigmoid score for entry scanning. |
| `SELL_THRESHOLD` | `0.45` | AI-exit threshold for non-moonbag positions. |

The `RiskEngine` also enforces a hard liquidity floor of `5000` USD in `check_safety(self, token_address, liquidity_usd)` before probing a Jupiter sell-path quote.

## `portfolio_state.json`

`PortfolioManager` stores local position state in `portfolio_state.json` by default. The file is a JSON object keyed by token address. Each value maps to a `Position` record with these fields:

| Field | Meaning |
| --- | --- |
| `token_address` | Token mint address used by the strategy. |
| `symbol` | Display label; the runner currently derives a short `Meme_` label from the token address for new positions. |
| `entry_price` | Entry price in SOL per token as estimated from the buy quote. |
| `entry_time` | Unix timestamp when the position was recorded. |
| `amount_held` | Current token units tracked locally. |
| `initial_cost_sol` | SOL amount committed at entry. |
| `highest_price` | Highest observed price since entry, used for trailing-stop drawdown. |
| `is_moonbag` | Whether the first take-profit sale has happened. Defaults to `false` when omitted by older state files. |

State updates happen after buys, sells, price updates, partial sells, and position closes. This local state is not a substitute for on-chain balances; `SolanaTrader.sell` still queries token accounts before selling. Before restarting after manual trades, inspect for mismatches between local `amount_held` and wallet reality.

## STOP signal semantics

The runner checks a STOP signal before data refresh, position monitoring, entry scanning, and buy/sell execution.

- Signal path: `STOP_SIGNAL_PATH` environment variable, or `STOP_SIGNAL` if unset.
- Active contents: an existing file whose stripped uppercase content is empty, `STOP`, or `STOPPED`.
- When active, `_handle_stop_signal()` logs the stop request, writes `STOPPED` to the same file when possible, and returns `True` so the current operation exits or the loop breaks.
- Important: `STOPPED` remains an active stop value. Delete or rename the STOP file before restarting a live loop.
- If the STOP file cannot be read, the runner treats that as a stop request.

Dashboard-triggered STOP controls route to [dashboard-ops](../../dashboard-ops/SKILL.md). For live-loop recovery, always inspect and intentionally clear the STOP file rather than assuming a previous stop was consumed.

## Risk sizing and safety checks

The risk path is deliberately simple:

- `RiskEngine.calculate_position_size(wallet_balance_sol)` returns the fixed `ENTRY_AMOUNT_SOL` only when wallet balance is at least `ENTRY_AMOUNT_SOL + 0.1`; otherwise it returns `0.0` and entries are skipped.
- `RiskEngine.check_safety(self, token_address, liquidity_usd)` rejects tokens with liquidity below `5000` USD.
- The same safety check asks Jupiter for a sell-path quote from the token to SOL for a small raw amount with `slippage_bps=1000`. No quote or any exception returns `False`.
- `scan_for_entries()` skips existing positions, applies `BUY_THRESHOLD`, checks risk, then calls `_execute_buy()` only while open positions are below `MAX_OPEN_POSITIONS`.
- `monitor_positions()` can sell for stop loss, first take profit, trailing stop, or AI score below `SELL_THRESHOLD`.

These checks are not a full risk engine. They do not verify rug-pull authority, transfer taxes beyond quote failure, wallet-level exposure, priority fees, MEV, RPC reliability, or price-impact limits. Add external controls before authorizing real funds.

## Guarded live-run checklist

Use this checklist only after the user has explicitly authorized live trading:

1. Confirm the intended wallet, funds at risk, network, token universe, and maximum slippage.
2. Run the offline checker in normal mode, then live mode if credentials should be present:
   ```bash
   python scripts/alpha_gpt_trading_config_check.py --strategy-json best_meme_strategy.json
   python scripts/alpha_gpt_trading_config_check.py --live --strategy-json best_meme_strategy.json
   ```
3. Confirm `best_meme_strategy.json` is valid and was produced by the factor-mining workflow.
4. Confirm data ingestion has populated enough rows for `CryptoDataLoader.load_data(limit_tokens=300)`; otherwise route to [data-pipeline](../../data-pipeline/SKILL.md).
5. Inspect or back up `portfolio_state.json` if it exists.
6. Delete any active STOP signal if the intention is to run; create the STOP signal only when intentionally stopping.
7. Reconfirm that `QUICKNODE_RPC_URL` and `SOLANA_PRIVATE_KEY` are set without printing, logging, or committing their values.
8. Start with limited funds and monitor RPC/Jupiter responses and wallet balances externally.
9. Stop with the STOP file or an authorized dashboard STOP control; then confirm shutdown and close resources.
