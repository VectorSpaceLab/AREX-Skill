# CLI Troubleshooting

Use this guide to diagnose Unsloth CLI failures without reopening repository files. Prefer safe checks first: `unsloth --help`, command-specific `--help`, and `unsloth train --dry-run`.

## Fast diagnosis table

| Symptom | Likely cause | Fix |
|---|---|---|
| `Refusing to run Unsloth inside System32` | On Windows, current directory is `System32` or a child directory. | `cd` to a normal project directory and rerun. |
| `Error: Config file not found: ...` | `--config` path does not exist. | Create the file, fix the path, or remove `--config` to use defaults plus CLI flags. |
| `Error: provide --model or set model in --config` | Real `train` run has no model. | Add root `model:` or pass `--model`. Validate with `--dry-run`. |
| `Error: provide --dataset or --local-dataset` | Real `train` run has no dataset source. | Add `data.dataset`, `data.local_dataset`, `--dataset`, or repeated `--local-dataset`. |
| `Cannot do full finetuning on a LoRA adapter` | `training_type: full` with a directory containing `adapter_config.json`. | Use `training_type: lora` or choose a base model for full finetuning. |
| `--repo-id required when using --push-to-hub` | Export push requested without destination. | Add `--repo-id username/model-name` or remove `--push-to-hub`. |
| `Invalid format` in export | `--format` is not supported. | Use `merged-16bit`, `merged-4bit`, `gguf`, or `lora`. |
| `Missing option '--model' / '-hf' / '--hf-repo'` from `studio run` | No model given after legacy alias preprocessing. | Pass `--model`, `-hf`, `--hf-repo`, exact legacy `-m VALUE`, or exact legacy `-hfr VALUE`. |
| `--model embeds variant ... but --gguf-variant ... was also provided` | `org/repo:variant` conflicts with explicit variant. | Keep one source of truth or make both variants match. |
| `--secure requires the Cloudflare tunnel` | `--secure` combined with `--no-cloudflare`. | Remove `--no-cloudflare` or use `--no-secure`. |
| Parent `unsloth studio --secure run ...` rejected | Plain-server option placed before a subcommand. | Move the flag after subcommand: `unsloth studio run --secure ...`. |
| Llama-server flag eaten or misparsed | One-character legacy aliases can cluster with pass-through flags in old command forms. | Use current `--model`/`-hf`/`--frontend`, keep llama-server flags after managed options, and avoid using `-f` except exact legacy frontend. |
| `-np8` behaves like a port error | Attached parallel alias was not canonicalized, or invocation was not the `unsloth` console script. | Use `-np 8` or `--parallel 8`; attached rewrite only runs for `unsloth`/`unsloth.exe` and stops after `--`. |
| Connect cannot find Studio | No running server found at `UNSLOTH_STUDIO_URL` or default loopback. | Start `unsloth studio`/`unsloth run`, or set `UNSLOTH_STUDIO_URL` to the intended server. |
| Connect remote server asks for API key | Automatic minting only works for verified loopback Studio. | Pass `--api-key` or set `UNSLOTH_API_KEY`; the key is remembered per server. |
| `codex` connect rejects model as non-GGUF | Codex needs llama-server `/v1/responses` streaming. | Load or request a GGUF model; try a `-GGUF` model id/variant. |

## System32 guard

On Windows, the top-level callback refuses to run from `System32` because relative paths and generated files would land in a protected/system directory and cause confusing errors. This guard applies before subcommands. Always change into a user project/work directory first.

## Config and dry-run issues

`train --dry-run` is the safest validation tool because it loads the config, applies overrides, prints resolved YAML, and exits before backend training work.

If dry-run fails:

1. Confirm the config file exists and is YAML/JSON.
2. Confirm nested fields are under the right section: `data`, `training`, `lora`, or `logging`.
3. Confirm enum fields use valid values: `training_type` is `lora` or `full`; `format_type` is `auto`, `alpaca`, `chatml`, or `sharegpt`; `gradient_checkpointing` is `unsloth`, `true`, or `none`.
4. Remove secrets from the config and inject them through `HF_TOKEN`, `WANDB_API_KEY`, or CLI flags for private runs.
5. For real training, add both a model and a dataset source; dry-run itself does not require them.

## Model/dataset failures after dry-run

If dry-run succeeds but real training fails:

- Missing model errors mean the resolved root `model` is empty; add it or pass `--model`.
- Missing dataset errors mean neither `data.dataset` nor `data.local_dataset` resolved; add one source.
- A local model directory with `adapter_config.json` is treated as a LoRA adapter. Do not pair it with `training_type: full`.
- Model load, dataset load, model preparation, and training start failures come from the Studio backend; route backend-depth investigation to `../core-training/SKILL.md`.

## Token precedence and secrets

For `train`, `--hf-token` reads `HF_TOKEN` and `--wandb-token` reads `WANDB_API_KEY`. CLI/env values override config values. If the wrong account/token is used, inspect shell environment first, then explicit flags, then config fields.

For `connect`, `--api-key` reads `UNSLOTH_API_KEY`. Explicit/saved remote keys are remembered per server. Auto-minted local keys are replayed only after loopback identity verification.

## Studio exposure flags

Defaults are conservative for binding and explicit for tools:

- `unsloth studio` and `unsloth run` default `--host` to `127.0.0.1`.
- `--cloudflare` defaults on, but it only matters when exposure requires a tunnel.
- `--secure` forces `--host 127.0.0.1`, requires Cloudflare, and prints tunnel SDK URLs when available.
- `--no-secure` or hidden legacy `--not-secure` permits the raw bind behavior.
- Server-side tools default on for every bind; use `--disable-tools` to force them off.
- `--yes` remains accepted for backward compatibility but no longer skips a tool-policy prompt because the resolver does not prompt.

If `unsloth studio --enable-tools run ...`, `--secure`, `--no-cloudflare`, `--parallel`, or `--verbose` is rejected before a subcommand, move the flag after `run` so it reaches the subcommand.

## Pass-through and short aliases

`unsloth studio run` and `unsloth run` use `allow_extra_args` and `ignore_unknown_options`; unknown options pass to llama-server. This is intentional for GGUF tuning flags.

Rules to avoid parser surprises:

- Use `--model`, `-hf`, or `--hf-repo` for the model.
- Exact legacy `-m VALUE` and `-hfr VALUE` still work, but do not use clustered strings starting with those aliases unless they are intended llama-server flags.
- Use `--frontend` for Studio run frontend paths; exact legacy `-f VALUE` still works, but clustered `-fa`, `-fit`, `-fitt`, and `-fitc` are llama-server flags and must remain pass-through.
- Use `--parallel 8`, `--n-parallel 8`, `-np 8`, or attached `-np8` only from the real `unsloth` console script. Prefer spaced form when generating commands.
- Put raw positional/tail tokens after `--` if they must not be canonicalized or legacy-promoted.

## Connect side effects

`unsloth connect` can write config files for the target agent and cache Studio API keys. Use `--no-launch` first to print commands and review effects.

Side effects to explain to users:

- `claude` may update settings to disable the attribution header for better local KV-cache reuse and unsets conflicting Anthropic auth env vars during launch.
- `codex` writes an `unsloth_api` provider/profile and exports `UNSLOTH_STUDIO_AUTH_TOKEN` during launch.
- `openclaw` and `opencode` write provider config entries containing the Studio base URL and key.
- `hermes` writes a custom provider config and exports `UNSLOTH_API_KEY` during launch.

If a user does not want config files changed, use `--no-launch` and manually adapt the printed environment/command instead of launching immediately.
