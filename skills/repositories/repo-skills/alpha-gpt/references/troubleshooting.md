# AlphaGPT Cross-Cutting Troubleshooting

## When to read

Read this when an issue spans more than one AlphaGPT workflow: installation,
source imports, dependency pinning, missing credentials, unsafe live operations,
or service availability. For workflow-specific failures, follow the nearest
sub-skill troubleshooting page.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `pip install -e .` fails or no AlphaGPT distribution metadata exists | The repository is a source tree without package metadata. | Install `requirements.txt`, run commands from the checkout root, or add the checkout root to the Python path for local validation. |
| `ModuleNotFoundError: model_core` or `data_pipeline` | Python cannot see the checkout root. | Run from the checkout root or set a checkout-specific import path in the environment being used. Do not hard-code private paths in durable scripts. |
| `ImportError: cannot import name 'TokenAccountOpts' from solana.rpc.types` | A newer `solana` wheel removed or moved the API used by `execution/trader.py`. | Pin a compatible Solana stack such as `solana==0.36.12` with `websockets==15.0.1`, then run `python -m pip check` and import `execution.trader`. |
| `pip check` reports `websockets` conflicts | Solana and Streamlit constraints are not aligned, or unrelated system-site packages leaked into the env. | Use a clean venv/conda env and resolve the Solana/Streamlit pin together; avoid system-site environments for production. |
| `torch.cuda.is_available()` differs from expectations | Host driver/runtime/wheel mismatch, or CUDA is optional for the selected smoke. | Use CPU synthetic checks for formula correctness. Only debug CUDA when full training performance is in scope. |

## Credential and service gates

| Gate | Required by | Do not proceed when |
| --- | --- | --- |
| `BIRDEYE_API_KEY` | Data ingestion | The task would fetch market data but no key/tier/network is confirmed. |
| DB credentials / Postgres | Data ingestion, training, dashboard market panel | The target DB is production and the user did not authorize writes; use schema preview first. |
| `QUICKNODE_RPC_URL` | Live strategy, dashboard wallet balance | The task only needs offline validation; avoid RPC calls. |
| `SOLANA_PRIVATE_KEY` | Live buy/sell execution | The user has not explicitly authorized wallet use and funds/slippage/token universe. |
| `best_meme_strategy.json` | Live runner, dashboard strategy display | It is missing, malformed, or contains invalid token IDs; validate through factor-mining first. |

## Safety stop conditions

Stop and ask for explicit authorization before you:

- run a command that may submit a Solana transaction
- run a loop that can buy or sell tokens
- write to a non-disposable database
- use a private key, API key, or paid API quota
- launch a long training run or optional research experiment
- infer that a dashboard STOP button cancels already-submitted transactions

## Useful offline helpers

- Root env checker: [../scripts/alpha_gpt_env_check.py](../scripts/alpha_gpt_env_check.py)
- Data schema preview: [../sub-skills/data-pipeline/scripts/alpha_gpt_schema_preview.py](../sub-skills/data-pipeline/scripts/alpha_gpt_schema_preview.py)
- Formula smoke: [../sub-skills/factor-mining/scripts/alpha_gpt_formula_smoke.py](../sub-skills/factor-mining/scripts/alpha_gpt_formula_smoke.py)
- Trading config checker: [../sub-skills/live-strategy/scripts/alpha_gpt_trading_config_check.py](../sub-skills/live-strategy/scripts/alpha_gpt_trading_config_check.py)
- Dashboard fixture generator: [../sub-skills/dashboard-ops/scripts/alpha_gpt_dashboard_fixture.py](../sub-skills/dashboard-ops/scripts/alpha_gpt_dashboard_fixture.py)

These helpers are designed for no-network preflight and should run before any
native command that touches live APIs, databases, wallets, or Streamlit servers.
