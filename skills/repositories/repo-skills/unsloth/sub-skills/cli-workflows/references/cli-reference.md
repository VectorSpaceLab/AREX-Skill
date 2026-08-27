# Unsloth CLI Reference

The console entry point is `unsloth = unsloth_cli:app`. The app help is `Command-line interface for Unsloth training, inference, and export.` It is a Typer application, so `-h` and `--help` are equivalent.

## Command map

| Command | Purpose | Safe preflight |
|---|---|---|
| `unsloth --version` | Print installed Unsloth version. | Safe; no model load. |
| `unsloth train` | Launch training through the Studio training backend. | Use `--dry-run` first. |
| `unsloth inference MODEL PROMPT` | Run one prompt and stream a single answer. | `--help` only is download-free. |
| `unsloth chat [MODEL]` | Start an interactive chat loop; can choose a trained model if omitted. | `--help` only is download-free. |
| `unsloth export CHECKPOINT OUTPUT_DIR` | Export a checkpoint to merged, GGUF, or LoRA formats. | `--help` and argument validation are safe; real export loads checkpoint. |
| `unsloth list-checkpoints` | Scan an outputs directory for checkpoints. | Safe if it only scans local files. |
| `unsloth studio` | Launch the plain Studio server. | `--help` is safe; real launch starts server. |
| `unsloth studio run` | Start Studio, load a model, print API key and SDK examples. | `--help` is safe; real run starts server and loads model. |
| `unsloth run` | Top-level alias for `unsloth studio run`. | Same behavior as `studio run`. |
| `unsloth connect` | Connect a coding agent to a running Studio server. | Use `--no-launch` to print env/command first. |

## `train`

Use `train` when the user wants CLI-driven finetuning from YAML/JSON plus overrides.

Typical safe plan:

```bash
unsloth train --config config.yaml --dry-run
unsloth train --config config.yaml
```

Important flags:

| Flag | Notes |
|---|---|
| `--config`, `-c` | YAML or JSON config. CLI flags override config values. |
| `--model` | Base model id/path; required for real training. |
| `--dataset` | Hugging Face dataset id or supported dataset source. |
| `--local-dataset` | Repeatable local dataset path/list entry. |
| `--training-type lora\|full` | LoRA is default; full finetuning rejects LoRA adapter directories. |
| `--load-in-4bit/--no-load-in-4bit` | Used for LoRA model load; full finetuning forces non-4bit load. |
| `--hf-token` | Also reads `HF_TOKEN`; CLI/env value wins over config logging token. |
| `--wandb-token` | Also reads `WANDB_API_KEY`; CLI/env value wins over config logging token. |
| `--dry-run` | Emits resolved config YAML and exits before model/dataset loading. |

The `train` command validates these before expensive backend work: config file existence, presence of `model`, presence of `dataset` or `local_dataset`, and LoRA adapter/full-finetune mismatch.

## `inference`

`inference` runs one prompt and exits:

```bash
unsloth inference unsloth/Qwen3-1.7B "Explain LoRA in one sentence"
```

Common flags: `--temperature`, `--top-p`, `--top-k`, `--max-new-tokens`, `--repetition-penalty`, `--system-prompt`, `--max-seq-length`, `--load-in-4bit/--no-load-in-4bit`, `--think/--no-think`, `--verbose/-v`, and `--no-server`.

By default it tries a running Studio server first so the model can stay warm. Use `--no-server` to force in-process loading.

## `chat`

`chat` keeps a model loaded for an interactive session:

```bash
unsloth chat unsloth/Qwen3-1.7B --max-new-tokens 512
```

Interactive commands are `/exit`, `/reset`, `/think`, `/compare`, and `/help`. `--compare` needs a LoRA adapter because it compares base vs tuned behavior. It is unavailable for GGUF models and non-LoRA models.

If `MODEL` is omitted, the CLI scans trained outputs and prompts the user to pick a model. For non-interactive automation, pass a model explicitly.

## `export` and `list-checkpoints`

List checkpoints:

```bash
unsloth list-checkpoints --outputs-dir ./outputs
```

Export a checkpoint:

```bash
unsloth export ./outputs/run/checkpoint-100 ./exports/run --format merged-16bit
unsloth export ./outputs/run/checkpoint-100 ./exports/run-gguf --format gguf --quantization q4_k_m
unsloth export ./outputs/run/checkpoint-100 ./exports/adapter --format lora
```

Supported formats are `merged-16bit`, `merged-4bit`, `gguf`, and `lora`. Supported GGUF quantizations are `q4_k_m`, `q5_k_m`, `q8_0`, and `f16`. `--push-to-hub` requires `--repo-id`; token can come from `--hf-token` or `HF_TOKEN`.

For deeper export format selection and backend behavior, route to `../model-export/SKILL.md`.

## `studio` plain server

`unsloth studio` launches the Studio server without preloading a model.

Common flags:

| Flag | Default | Notes |
|---|---:|---|
| `--port`, `-p` | `8888` | Server port. |
| `--host`, `-H` | `127.0.0.1` | Loopback by default. |
| `--frontend`, `-f` | unset | Plain server keeps `-f`; it has no llama-server pass-through tail. |
| `--api-only` | `false` | Serve API without frontend. |
| `--parallel`, `--n-parallel` | `1` | Plain server parallel decode slots. |
| `--cloudflare/--no-cloudflare` | on | Auto-create tunnel when bound to `0.0.0.0`. |
| `--secure/--no-secure` | off | Secure mode requires Cloudflare and forces loopback bind. |
| `--verbose`, `-v` | off | Enables per-request access logs. |
| `--enable-tools/--disable-tools` | unset | Unset leaves server-side tools on by default. |

Parent options that apply only to the plain server must come before no subcommand. If the user writes `unsloth studio --secure run ...`, the CLI rejects it and tells them to place the flag after `run`.

## `studio run` and top-level `run`

`unsloth run` is registered as a top-level alias for `unsloth studio run`. Use it for a one-liner local API server that starts Studio, loads a model, creates an API key, and prints OpenAI/Anthropic-compatible examples.

Examples:

```bash
unsloth run --model unsloth/Qwen3-1.7B-GGUF --gguf-variant UD-Q4_K_XL
unsloth studio run --model unsloth/Qwen3-1.7B-GGUF:UD-Q4_K_XL --parallel 8
unsloth run --model ./model.gguf --host 127.0.0.1 --port 8888 --disable-tools
unsloth run --model unsloth/Qwen3-27B-GGUF --gguf-variant Q8_0 --tensor-parallel
```

Primary managed flags:

| Flag | Default | Notes |
|---|---:|---|
| `--model`, `-hf`, `--hf-repo` | required | Model path or HF repo; supports `org/repo:variant`. |
| `--gguf-variant` | unset | Quant variant; conflicts if it disagrees with embedded `repo:variant`. |
| `--max-seq-length`, `--context-length` | `0` | `0` means model default for GGUF and `2048` for hub models. |
| `--load-in-4bit/--no-load-in-4bit` | on | Applies to non-GGUF model loading. |
| `--api-key-name` | `cli` | Label for generated API key. |
| `--parallel`, `--n-parallel`, `-np` | `4` | Parallel decode slots for llama-server. |
| `--cloudflare/--no-cloudflare` | on | Tunnel behavior for public binds. |
| `--secure/--no-secure` | off | Requires Cloudflare, forces host to `127.0.0.1`, and uses tunnel URL in SDK examples. |
| `--enable-tools/--disable-tools` | unset | Tools default on for every bind; explicit flag wins. |
| `--yes`, `-y` | off | Backward compatible; tool policy no longer prompts. |
| `--tensor-parallel/--no-tensor-parallel` | off | Split GGUF across GPUs by tensor instead of layer. |
| `--verbose`, `-v` | off | Enables Studio access logs and forwards `--log-verbose` to llama-server unless already present. |

`studio run` accepts unknown options and passes them through to llama-server for GGUF loads. Examples include `-c`, `-ngl`, `--jinja`, `--flash-attn`, `-t`, `--top-k`, and `--seed`. Studio rejects managed or unsafe llama-server flags such as model identity, network, auth/TLS, single-model UI, and parallel-slot flags; use the Studio-managed flags instead.

Short-alias rules:

- `-hf` remains a supported model alias and does not cluster like one-character shorts.
- Legacy exact `-m VALUE`, `-m=VALUE`, `-hfr VALUE`, and `-hfr=VALUE` still promote to `--model`.
- Legacy exact `-f VALUE` still promotes to `--frontend` for `studio run`, but `-f` is not an official run option because it would consume llama-server flags like `-fa` and `-fit`.
- Clustered llama-server flags such as `-mg`, `-md`, `-fa`, `-fitt`, and `-sm` must pass through unchanged.
- Attached `-np8` is rewritten to `-np 8` only when invoked via the real `unsloth` or `unsloth.exe` console script; rewriting stops at `--`.

## `connect`

`unsloth connect` targets a running Studio server and has subcommands for coding agents:

```bash
unsloth connect claude --model <loaded-or-loadable-model> --no-launch
unsloth connect codex --model <gguf-model> --no-launch
unsloth connect openclaw --model <model> --no-launch
unsloth connect opencode --model <model> --no-launch
unsloth connect hermes --model <model> --no-launch
```

Shared options:

| Option | Notes |
|---|---|
| `--model`, `-m` | Defaults to an already loaded Studio model; may load a requested model. |
| `--api-key` | Also reads `UNSLOTH_API_KEY`; remote servers need an explicit or saved key. |
| `--launch/--no-launch` | `--no-launch` prints environment/config command instead of starting the agent. |

Connection behavior:

- If no server is found, it suggests starting `unsloth studio` or setting `UNSLOTH_STUDIO_URL`.
- Local loopback Studio can mint and cache an API key after identity verification.
- Remote or unverified Studio requires a provided/saved API key.
- `codex` requires a GGUF model because Codex streams through the `/v1/responses` llama-server path.
- Agent commands accept pass-through arguments after their own options and forward them to the launched tool.

Connect side effects by target:

| Target | Side effects |
|---|---|
| `claude` | May update Claude settings to disable attribution header for KV-cache reuse; unsets conflicting Anthropic auth env vars for launch. |
| `codex` | Updates Codex config/profile for an `unsloth_api` provider and sets `UNSLOTH_STUDIO_AUTH_TOKEN` for launch. |
| `openclaw` | Updates OpenClaw provider config with base URL and key. |
| `opencode` | Updates OpenCode provider config with base URL and key. |
| `hermes` | Updates Hermes custom provider config and sets `UNSLOTH_API_KEY` for launch. |

Use `--no-launch` first whenever the user needs to review config or environment changes before running an external agent.
