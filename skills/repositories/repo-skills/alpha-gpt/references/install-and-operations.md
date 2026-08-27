# Install And Operations Reference

## Purpose

Read this when you need a safe AlphaGPT environment, a minimal import check, or
a reminder of which services are required before running live workflows. This
reference is public runtime guidance; it avoids local construction-environment
paths and credentials.

## Source-tree install model

AlphaGPT currently provides `requirements.txt` but no `pyproject.toml`,
`setup.py`, or console-entry-point metadata. Treat it as a source checkout:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Then run commands from the checkout root, or add the checkout root to the Python
path for local validation. Do not expect `pip install -e .` to work until package
metadata is added.

## Dependency groups

| File | Use | Install by default? | Notes |
| --- | --- | --- | --- |
| `requirements.txt` | Main data pipeline, model core, strategy runner, Solana execution, dashboard | Yes for selected workflows | Includes PyTorch, pandas, SQLAlchemy, asyncpg, aiohttp, Solana SDK, Streamlit, Plotly, Postgres drivers. |
| `requirements-optional.txt` | Standalone `times.py` and `lord/experiment.py` research scripts | No | Optional experiments are outside the selected main workflow and may run long or require external data. |

## Solana compatibility pin

The broad requirement `solana>=0.30.0` may resolve to a newer Solana SDK whose
API no longer exposes `TokenAccountOpts` from `solana.rpc.types`, which is used
by `execution/trader.py`. If importing the execution layer fails with that
symbol missing, use a compatibility pin similar to:

```bash
python -m pip install "solana==0.36.12" "websockets==15.0.1"
python -m pip check
python -c "from solana.rpc.types import TokenAccountOpts; import execution.trader"
```

Keep this as a troubleshooting pin, not a guarantee that live trading is safe.
Live execution still requires an authorized wallet, RPC endpoint, network, and
funding review.

## Minimal safe checks

Use these before any live command:

```bash
python -c "import data_pipeline, model_core, execution, strategy_manager, dashboard"
# From the alpha-gpt skill directory; replace /path/to/AlphaGPT with the target checkout.
python scripts/alpha_gpt_env_check.py --repo-root /path/to/AlphaGPT --scope all
python sub-skills/factor-mining/scripts/alpha_gpt_formula_smoke.py --repo-root /path/to/AlphaGPT --formula 0,5,6
```

The bundled scripts are offline by default. They do not fetch Birdeye data, open
Postgres connections, contact Solana RPC, call Jupiter, or send transactions.

## Service prerequisites by workflow

| Workflow | Required services / credentials | Safe offline alternative |
| --- | --- | --- |
| Data ingestion | `BIRDEYE_API_KEY`, DB credentials, reachable Postgres/Timescale, network | Data-pipeline schema preview and env review. |
| Factor mining | Populated SQL `tokens`/`ohlcv` tables for full training; PyTorch CPU or optional CUDA for speed | Synthetic formula smoke and static API reference. |
| Live strategy | `best_meme_strategy.json`, DB rows, Solana RPC URL, private key, wallet funds, Jupiter network | Offline trading config checker. |
| Dashboard | Streamlit, local state/log files, DB/RPC for live panels | Dashboard fixture generator and empty-state diagnosis. |

## Artifacts produced by AlphaGPT workflows

- `best_meme_strategy.json`: formula token list or object with a `formula` key.
- `training_history.json`: training steps, average reward, best score, and optional stable-rank history.
- `portfolio_state.json`: local portfolio state keyed by token address.
- `STOP_SIGNAL`: stop-control file consumed by the live runner when it appears in the runner's configured working directory/path.
- `strategy.log`: optional log file read by the dashboard tail panel.

## Operational safety boundaries

- Do not run `execution/trader.py` as a smoke test. Its inline main block can attempt a sell path.
- Do not start `strategy_manager.runner` unless live trading has been explicitly authorized for the current wallet, funds, RPC, token universe, and slippage policy.
- Do not run `data_pipeline.run_pipeline` against a production DB as a verification step.
- Prefer a disposable database and tiny fixtures before live ingestion or trading.
- Treat dashboard `EMERGENCY STOP` as a file-write signal only; it does not cancel already submitted transactions.
