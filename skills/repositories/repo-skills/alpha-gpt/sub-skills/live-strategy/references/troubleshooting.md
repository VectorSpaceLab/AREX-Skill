# Live Strategy Troubleshooting

Use this guide for AlphaGPT live-loop, risk, portfolio, STOP, and execution failures. Keep offline diagnosis separate from live trading: do not call RPC, Jupiter, database sync, or trader methods unless the user explicitly authorizes those side effects.

## Quick offline triage

```bash
python scripts/alpha_gpt_trading_config_check.py --strategy-json best_meme_strategy.json
python scripts/alpha_gpt_trading_config_check.py --live --strategy-json best_meme_strategy.json
```

The checker validates files, thresholds, STOP state, and env presence only. It never prints `SOLANA_PRIVATE_KEY` and never contacts external services.

## Failure modes

| Symptom | Likely cause | Safe recovery |
| --- | --- | --- |
| `Strategy file not found! Please train model first.` | `best_meme_strategy.json` is missing from the runner's launch directory. | Generate or copy the strategy artifact through [factor-mining](../../factor-mining/SKILL.md). Validate with the checker before live use. |
| Strategy JSON loads but inference gives no usable signals. | JSON object missing `formula`, formula is empty, formula tokens are not integer ids, token ids are out of range, or RPN arity leaves the StackVM with an invalid stack. | Use the checker to validate the accepted list/object format. Route formula repair to [factor-mining](../../factor-mining/SKILL.md). |
| Missing private key error, wallet address cannot be derived, or signing fails. | `SOLANA_PRIVATE_KEY` is absent, malformed, or loaded from the wrong process environment. | For dry-run review, keep the key absent. For authorized live use, set the env var or `.env` entry without printing it. Do not paste the key into logs or chat. |
| Balance is `0.0` or wallet balance check fails. | Missing/invalid RPC URL, missing keypair, unfunded wallet, RPC failure, or wrong wallet. | Check env presence offline. Confirm wallet and funds out of band. Do not retry live sends until RPC and wallet identity are intentionally approved. |
| Jupiter quote returns `None` or logs a quote error. | Unsupported pair, route unavailable, amount too small, token not liquid, Jupiter API/rate-limit issue, or slippage too low for current market. | Treat no quote as a block. Do not raise slippage without explicit user approval. For risk checks, no sell-path quote means the token is unsafe. |
| Jupiter swap API returns no transaction. | Quote became stale, wallet public key is unavailable, Jupiter rejected the route, or API/network failed. | Get a fresh quote only if live API use is authorized. Otherwise keep this as a live-service prerequisite failure. |
| Transaction sent but not confirmed. | RPC/network instability, priority fee too low, blockhash/route expiration, wallet/funds issue, or Solana congestion. | Do not assume portfolio state is correct. Confirm on-chain status externally, then reconcile `portfolio_state.json` before restarting. |
| Sell says token balance is zero. | Wallet has no token account for the mint, wrong wallet/key, balance already sold, wrong mint, or parsed token account API incompatibility. | Verify wallet/token balance out of band. Keep local portfolio state from triggering repeated sells until reconciled. |
| Import error for `TokenAccountOpts`. | The broad `solana>=0.30` requirement can resolve to a newer Solana SDK where this API is unavailable. | Pin `solana==0.36.12` with `websockets==15.0.1`, then rerun safe import/config checks. |
| STOP signal appears stuck. | The STOP file contains `STOPPED`; the runner still treats `STOPPED` as active. Empty files and `STOP` are also active. | Delete or rename the STOP file before restart. If you need a non-stopping marker, use content other than empty/`STOP`/`STOPPED`. |
| STOP request is ignored. | The runner is not reading the expected path, or `STOP_SIGNAL_PATH` differs from the file being edited. | Check the exact STOP path in the runtime environment. Prefer the checker to inspect whether the configured path is active before launch. |
| DB/data appears empty or no tokens are mapped. | Market database is not populated, data loader cannot query the expected rows, external ingestion was not run, or DB config points to the wrong database. | Route to [data-pipeline](../../data-pipeline/SKILL.md). Do not solve empty data by forcing live trading; entries depend on feature tensors. |
| Portfolio JSON parse error. | Manual edit, truncated write, or wrong file. | Stop the loop, back up the corrupt file, repair to the `Position` schema in [live-strategy-reference.md](live-strategy-reference.md), or start with an intentionally empty state after confirming wallet reality. |
| Local portfolio and wallet disagree. | Manual trades, failed/partial transactions, stale quotes, token decimal fallback, or state file copied across wallets. | Treat on-chain wallet state as the source of truth for execution, but repair local state before letting the runner monitor/sell positions. |
| Live runner keeps entering global error sleep. | An exception inside data refresh, loader, position monitor, risk quote, or trade path is caught by the global loop. | Stop the loop, inspect logs, run offline config checks, then isolate the failing prerequisite. Do not leave a credentialed bot retrying indefinitely. |

## Common decision points

- If the user asks for a formula, training artifact, StackVM grammar, or `best_meme_strategy.json` repair, route to [factor-mining](../../factor-mining/SKILL.md).
- If the user asks why the strategy sees no tokens or no recent OHLCV rows, route to [data-pipeline](../../data-pipeline/SKILL.md).
- If the user asks about the Streamlit STOP button, portfolio visualization, log display, or dashboard data views, route to [dashboard-ops](../../dashboard-ops/SKILL.md).
- If the user asks to run live buys/sells but has not authorized wallet/funds/network/slippage, refuse live execution and offer offline preflight instead.
