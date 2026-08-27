# Studio Workflows

This reference distills Unsloth Studio install/launch/runtime behavior for future agents. It is self-contained and intentionally avoids depending on the source checkout.

## When to Use Studio

- Use Studio for local web UI workflows, local API serving, provider-backed chat, GGUF/llama.cpp inference, chat/RAG/data recipe UI flows, API endpoint integration, and runtime setup/debugging.
- Use `../core-training/SKILL.md` for code-first `FastLanguageModel`, `FastModel`, trainer, LoRA, RL, and dataset code tasks.
- Use `../model-export/SKILL.md` for detailed save/merge/export/GGUF conversion planning.
- Use `../cli-workflows/SKILL.md` for full non-Studio CLI syntax and command catalogs.

## Install, Update, and Uninstall

Public Studio install entry points are shell/Powershell installers. They create or update a Studio-managed runtime with Python packages, backend assets, frontend build, launcher shims, auth/storage roots, and llama.cpp support.

| Task | macOS/Linux/WSL | Windows PowerShell | Notes |
| --- | --- | --- | --- |
| Install or update Studio | `curl -fsSL https://unsloth.ai/install.sh | sh` | `irm https://unsloth.ai/install.ps1 | iex` | Same public command updates an existing install. |
| Launch after install | `unsloth studio -p 8888` | `unsloth studio -p 8888` | Defaults to loopback. |
| Developer/local install | clone repo, then `./install.sh --local` | clone repo, then `.\install.ps1 --local` | Use only when intentionally using a checkout. Runtime skill should not require a checkout. |
| Isolated Studio root | `UNSLOTH_STUDIO_HOME=/abs/path <install command>` | `$env:UNSLOTH_STUDIO_HOME='C:\path'; <install command>` | Use same env var again at launch. |
| Skip PyTorch for GGUF-only mode | `UNSLOTH_NO_TORCH=1` with installer | `$env:UNSLOTH_NO_TORCH=1` with installer | Useful on CPU/GGUF-only hosts. |
| Pin Python | `UNSLOTH_PYTHON=3.12` with installer | `$env:UNSLOTH_PYTHON='3.12'` with installer | Installer chooses compatible runtime. |
| Cap native CPU pools | `UNSLOTH_CPU_THREADS=8 unsloth studio` | `$env:UNSLOTH_CPU_THREADS='8'; unsloth studio` | Must be a positive integer. |
| Full uninstall | public uninstall script | public uninstall script | Mutates machine; ask before running. |

Treat install/update/uninstall scripts as reference-only unless the user explicitly asks to mutate their machine. They can download, remove, or modify user-level application files.

## Studio Storage Roots

Studio resolves its root in this order:

1. `UNSLOTH_STUDIO_HOME`
2. `STUDIO_HOME`
3. installer-managed `unsloth_studio` virtual environment inference
4. default `~/.unsloth/studio`

Important derived locations:

- `studio.db` stores chat settings, providers metadata, runs, and app data.
- `auth/auth.db` stores auth state and API key metadata/hashes.
- `rag/rag.db` and `rag/uploads/` store RAG indexes and uploaded source documents.
- `cache/` stores Studio-managed downloads and caches.
- `exports/` and `outputs/` store generated artifacts.
- `llama.cpp/` is exported through `UNSLOTH_LLAMA_CPP_PATH` for custom roots.
- `runs/` is the TensorBoard/training-run root.

Keep the same root during setup and launch. A launch with a different root can appear as missing setup, missing API keys, missing models, missing frontend assets, or stale llama.cpp.

## Plain Studio Launch

Default launch:

```bash
unsloth studio -p 8888
```

Key behavior:

- Default host is `127.0.0.1`, not `0.0.0.0`.
- Default port is `8888`; if occupied, the runtime can auto-select a nearby free port and report it.
- `--frontend <path>` points to a built frontend `dist`; omit for normal packaged installs.
- `--api-only` starts only the backend API, useful for desktop/Tauri-managed frontend or API-only tests.
- `--parallel N` sets llama-server parallel decode slots for plain server launches. The accepted range is 1..64; plain Studio defaults to 1.
- `--verbose` restores per-request access logs that are otherwise deduplicated for high-frequency polling.
- `--enable-tools` and `--disable-tools` force server-side tool policy on/off for every request. With no flag, tools are enabled and per-chat/request UI settings are honored.

Typer option placement matters: parent options for `unsloth studio` do not automatically apply to subcommands. Put subcommand flags after the subcommand, for example `unsloth studio run --parallel 8`, not `unsloth studio --parallel 8 run`.

## Safe Remote Access Choices

Prefer secure remote launch:

```bash
unsloth studio --secure -p 8888
```

`--secure` behavior:

- Requires Cloudflare tunnel support.
- Forces the raw server bind back to `127.0.0.1`.
- Starts a free `https://*.trycloudflare.com` quick tunnel.
- Fails closed if the tunnel cannot start; it does not silently expose a raw port.
- Prints both the HTTPS tunnel URL and the loopback URL for local use.

Raw network bind:

```bash
unsloth studio -H 0.0.0.0 -p 8888
```

Raw bind behavior:

- Binds the HTTP server on all interfaces.
- `--cloudflare` is on by default for `0.0.0.0` launches and may also print a Cloudflare link.
- The raw `http://host:port` remains reachable from the network; use only on trusted networks or behind your own firewall/tunnel.
- Pass `--disable-tools` when exposing Studio to users or networks that should not have server-side code/tool execution.

Do not combine `--secure` with `--no-cloudflare`; the runtime rejects the combination.

## One-Line Model Serving

Use `unsloth studio run` to start Studio, load a model, and create/print an API key for the session:

```bash
unsloth studio run --model unsloth/Qwen3-1.7B-GGUF --gguf-variant UD-Q4_K_XL
```

Common options:

| Option | Meaning |
| --- | --- |
| `--model`, `-hf`, `--hf-repo` | Model path or Hugging Face repo. Supports `org/repo:variant` GGUF shorthand. |
| `--gguf-variant` | GGUF quant variant when the repo has multiple files. |
| `--max-seq-length`, `--context-length` | Runtime context tokens. `0` means GGUF model default; hub models use a default runtime value. |
| `--load-in-4bit` / `--no-load-in-4bit` | Transformer backend quantization toggle for non-GGUF model loads. |
| `--parallel`, `-np` | llama-server parallel decode slots for GGUF. `studio run` defaults to 4. |
| `--tensor-parallel` | Multi-GPU GGUF tensor split mode. Best for dense models; MoE often benefits less. |
| `--enable-tools` / `--disable-tools` | Force server-side tools on/off for every request. |
| `--secure` | HTTPS tunnel only, raw server loopback. |
| `-H 0.0.0.0` | Raw network bind. Warn before using. |
| unknown llama-server flags | Passed through for GGUF only, after Studio's auto-set flags. |

Managed llama-server flags are rejected because Studio owns them: model identity, host/port/path/API prefix/reuse-port, auth/TLS, llama-server UI flags, model-autoload flags, server mode switches such as embedding/rerank, `--tools`, and parallel slots. Allowed pass-through examples include `-c`, `--ctx-size`, `-ngl`, `--flash-attn`, `--jinja`, `--chat-template-file`, `--cache-type-k`, `--cache-type-v`, sampling settings, thread counts, and compatible speculative-decoding knobs.

For GGUF vision/multimodal loads, Studio can auto-detect companion `mmproj` files unless pass-through args disable it with last-wins `--no-mmproj` or `--no-mmproj-auto`. If a companion is manually involved, keep the selected GGUF and companion together and avoid passing Studio-managed `--mmproj` flags through raw extras.

## Connect Coding Agents

Use `unsloth connect` when a coding agent should use Studio's OpenAI-compatible endpoints.

Core behavior:

- Finds a running Studio server at `UNSLOTH_STUDIO_URL` or the default local URL.
- For a verified local loopback server, can mint and cache an API key automatically.
- For remote/non-loopback servers, requires an explicit API key through `--api-key` or `UNSLOTH_API_KEY` and remembers it per exact server base URL.
- Lists loaded models from `/v1/models`; if `--model` is requested and not loaded, asks Studio to load it through `/api/inference/load`.
- For Codex, requires a GGUF model served by llama-server because Codex streams through `/v1/responses`.

Codex integration writes/updates a Codex provider profile named `unsloth_api` with base URL `<studio>/v1`, an env key for the Studio token, and the current model/context window. Claude Code integration disables its attribution header when possible because that header breaks llama.cpp KV-cache reuse and can slow local inference significantly.

## Runtime Workflow Checklist

1. Run the bundled safe preflight script first when diagnosing: `python scripts/studio_preflight.py --host 127.0.0.1 --port 8888`.
2. Confirm package CLI exists: `unsloth --help`, `unsloth studio --help`, and if needed `unsloth studio run --help`.
3. Confirm storage root choice and whether `UNSLOTH_STUDIO_HOME` must be preserved.
4. Choose access mode: loopback, `--secure`, or raw `-H 0.0.0.0`.
5. Decide tool policy explicitly when exposing beyond loopback.
6. For model serving, prefer `unsloth studio run --model ...` and move llama.cpp tuning flags after `run`.
7. For agent integration, use `unsloth connect` and verify `/v1/models` reports the intended loaded model.
8. If setup is missing or frontend assets are absent, advise `unsloth studio setup` or the public installer/update command before destructive cleanup.
