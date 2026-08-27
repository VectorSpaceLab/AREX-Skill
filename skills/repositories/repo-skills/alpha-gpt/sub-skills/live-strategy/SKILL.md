---
name: live-strategy
description: "Operate AlphaGPT live strategy, risk, portfolio state, STOP
  control, and guarded Solana/Jupiter execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Live Strategy

Use this sub-skill when the task is about AlphaGPT's live strategy runner, risk
checks, portfolio state, STOP signal, or Solana/Jupiter execution preflight.
This is the safety-critical route: live commands can use private keys, wallet
funds, RPC endpoints, Jupiter quotes/swaps, and a database-backed signal loop.

## Do not route here for

- Creating or validating formula tokens before live use; use [factor-mining](../factor-mining/SKILL.md).
- Populating or repairing the market database; use [data-pipeline](../data-pipeline/SKILL.md).
- Streamlit visuals, dashboard fixture files, or STOP button display; use [dashboard-ops](../dashboard-ops/SKILL.md).

## Read or run

1. Read [references/live-strategy-reference.md](references/live-strategy-reference.md) for prerequisites, loop lifecycle, thresholds, portfolio state, STOP semantics, and guarded run checklist.
2. Read [references/execution-safety.md](references/execution-safety.md) for Solana/Jupiter credentials, signing, slippage, wallet funds, and transaction-safety gates.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for missing strategy JSON, missing private key, RPC/Jupiter failures, dependency pins, STOP-signal problems, and empty data.
4. Run [scripts/alpha_gpt_trading_config_check.py](scripts/alpha_gpt_trading_config_check.py) before any live run. It is offline and never contacts RPC, Jupiter, Postgres, or the network.
5. Use the root [environment checker](../../scripts/alpha_gpt_env_check.py) with `--scope live` for broader import/env checks.

## Non-negotiable guardrail

Never start the live runner, call `SolanaTrader.buy`, call `SolanaTrader.sell`,
or run transaction-capable native scripts unless the user has explicitly
authorized live trading for the current wallet, funds, network, token universe,
and slippage policy. Offline validation is not live-trading approval.

## Safe default workflow

1. Validate `best_meme_strategy.json` with the checker; it may be a bare token list or an object with a `formula` key.
2. Confirm formula tokens are in range `0..17` and route malformed formulas to factor-mining.
3. Check whether `STOP_SIGNAL` or a custom `STOP_SIGNAL_PATH` is already active.
4. Review thresholds before authorizing live operation: max positions, entry amount, stop loss, take profit, trailing stop, buy threshold, and sell threshold.
5. Confirm DB rows exist and are fresh enough for `CryptoDataLoader.load_data()`; route empty DB issues to data-pipeline.
6. Confirm Solana/Jupiter credentials and wallet risk only after the offline checks pass.
7. Treat native live commands as last-mile operations, not verification defaults.

## Core runtime facts

- `StrategyRunner.run_loop(self)` periodically syncs data, loads tensors, monitors positions, scans entries, and sleeps between cycles.
- `RiskEngine.check_safety(self, token_address, liquidity_usd)` rejects low liquidity and checks a Jupiter sell quote.
- `PortfolioManager.add_position(self, token, symbol, price, amount, cost_sol)` persists position state to `portfolio_state.json`.
- `SolanaTrader.buy(self, token_address: str, amount_sol: float, slippage_bps=500)` and `sell(self, token_address: str, percentage=1.0, slippage_bps=500)` are live transaction-capable methods.
- `JupiterAggregator.get_quote(self, input_mint, output_mint, amount_integer, slippage_bps=None)` contacts Jupiter's quote API.
- `execution/trader.py` contains an inline native test that can attempt a sell; do not use it as a smoke test.

## Quick route map

| User intent | Read/run | Notes |
| --- | --- | --- |
| "Can I safely start the bot?" | [scripts/alpha_gpt_trading_config_check.py](scripts/alpha_gpt_trading_config_check.py) then [references/live-strategy-reference.md](references/live-strategy-reference.md) | Offline preflight first, explicit live approval second. |
| "How do buy/sell and quotes work?" | [references/execution-safety.md](references/execution-safety.md) | Explains quote, swap transaction, signing, and confirmation flow. |
| "Why did the runner exit at startup?" | [references/troubleshooting.md](references/troubleshooting.md) | Usually missing strategy file or STOP signal. |
| "Why did no trade happen?" | [references/troubleshooting.md](references/troubleshooting.md) | Check thresholds, DB tensors, risk quote, balance, and position limits. |
| "Where did positions go?" | [references/live-strategy-reference.md](references/live-strategy-reference.md) | Covers `portfolio_state.json` shape and persistence. |

## Verification stance

Native live strategy and execution candidates are skipped by default because they
need credentials, network, database state, wallet funds, and explicit trading
authorization. Use the bundled checker and static route review for ordinary
verification.
