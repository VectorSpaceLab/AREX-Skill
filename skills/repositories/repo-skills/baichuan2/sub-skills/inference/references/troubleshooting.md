# Baichuan2 inference troubleshooting

Use this guide for failures in Python chat/base inference, the CLI helper, the Streamlit web helper, or the OpenAI-compatible API helper.

## Model weights, network, and cache

Symptoms:

- `OSError` or `RepositoryNotFoundError` while calling `from_pretrained(...)`.
- Download stalls, TLS/proxy failures, or timeouts.
- Local model directory is missing `config.json`, tokenizer files, generation config, or weight shards.

Actions:

1. Confirm the model id or local path points to a Baichuan2 Chat checkpoint for chat/CLI/web/API, or a Baichuan2 Base checkpoint for `generate(...)` workflows.
2. If using Hugging Face, confirm network access and any required authentication or license acceptance.
3. Pre-download weights in a connected environment and point `--model` to the local directory.
4. Keep the same model id/path for tokenizer, model, and `GenerationConfig.from_pretrained(...)`; mixing Chat and Base directories can produce confusing runtime errors.
5. Use `--dry-run` on bundled scripts first. Dry-run confirms launch configuration but does not verify model availability.

## `trust_remote_code` and remote-model assumptions

Symptoms:

- Errors about missing custom model classes.
- `ValueError` requesting `trust_remote_code=True`.
- Loaded model lacks `chat` or behaves like a generic causal LM.

Actions:

1. Baichuan2 Hugging Face checkpoints normally rely on custom remote code; keep `trust_remote_code=True` unless a local security review provides an alternative.
2. Only use remote code from a model source you trust. For locked-down environments, mirror the model artifacts internally and review the custom Python code before allowing it.
3. If you pass `--no-trust-remote-code`, expect Baichuan2 Chat helpers to fail unless your local model directory is already compatible with the installed Transformers classes.
4. Check that the checkpoint is a Chat model before using `model.chat(...)`. Base models are handled with `model.generate(...)`.

## GPU memory pressure and dtype choice

Symptoms:

- CUDA out-of-memory during `from_pretrained(...)` or first generation.
- Slow sharded loading or unexpected CPU offload.
- dtype errors such as unsupported bfloat16 operations on older GPUs.

Actions:

1. Start with a 7B Chat model if the 13B Chat model does not fit.
2. Restrict or choose GPUs with `CUDA_VISIBLE_DEVICES=0,1` before launch.
3. Use `--dtype float16` for broad CUDA compatibility; use `--dtype bfloat16` on Ampere-class GPUs such as A100 when supported.
4. Keep `--device-map auto` for multi-GPU placement unless you have a specific placement plan.
5. Reduce conversation history length; each retained turn increases prompt tokens and KV-cache memory.
6. Quantized loading and CPU-only fallback are deployment topics; route those requests to the deployment sub-skill.

## CLI multiline input and editor concerns

Symptoms:

- Entering `vim` in the CLI fails because `vim` is not installed.
- The terminal hangs in an editor the user does not know how to exit.
- Multiline input does not return expected text.

Actions:

1. Use regular single-line prompts unless multiline input is needed.
2. Configure an editor explicitly: `python scripts/chat_cli.py --editor nano` or `--editor "code --wait"`.
3. Disable editor support with `--disable-editor` on restricted hosts.
4. The commands `vim` and `multiline` are only CLI commands for collecting a prompt; they are not sent to the model.
5. `clear` resets chat history; `stream` toggles streaming; `exit` or `quit` ends the session.

## Streamlit launch issues

Symptoms:

- `streamlit: command not found`.
- Browser cannot reach the UI.
- Script arguments are parsed by Streamlit instead of the Baichuan2 helper.
- UI starts but model loading repeats unexpectedly.

Actions:

1. Install Streamlit in the active environment: `python -m pip install streamlit`.
2. Run help checks: `streamlit --help` and `python scripts/chat_web_demo.py --help`.
3. Configure host/port with Streamlit flags, not helper flags:

   ```bash
   streamlit run scripts/chat_web_demo.py --server.address 0.0.0.0 --server.port 8501 -- --model baichuan-inc/Baichuan2-13B-Chat
   ```

4. Put helper arguments after `--` so Streamlit passes them to the script.
5. If remote browser access fails, check firewall/SSH tunnel rules and prefer `--server.address 127.0.0.1` plus port forwarding for local-only access.
6. The app uses `st.cache_resource` for the model; changing model/dtype arguments requires restarting the Streamlit process.

## API streaming-not-supported behavior

Symptoms:

- An OpenAI client receives HTTP 400 when `stream=True`.
- Client code expects server-sent events or incremental deltas.

Actions:

1. Set `stream=False` or omit the `stream` field.
2. Use the CLI or Streamlit helpers when interactive streaming is required.
3. If API streaming is required for production, implement a separate server route that wraps `model.chat(..., stream=True)` and emits server-sent events. Do not assume the bundled demo server provides this behavior.

## API host/port and connectivity

Symptoms:

- `Address already in use` at startup.
- Client cannot connect to `/v1/chat/completions`.
- Server binds to all interfaces unintentionally.

Actions:

1. Choose an unused port: `python scripts/run_openai_api.py --port 8001`.
2. Use `--host 127.0.0.1` for local-only testing; use `--host 0.0.0.0` only on trusted networks or behind controlled access.
3. Check readiness with `curl http://127.0.0.1:8000/health`.
4. The helper is a demo server. Add authentication, TLS, process supervision, and request limits before any exposed deployment.

## Chat versus Base confusion

Symptoms:

- `AttributeError: ... has no attribute chat`.
- CLI/web/API helper loads a Base checkpoint and fails at generation.
- Base generation output includes the prompt and continuation rather than assistant-style messages.

Actions:

1. Use `baichuan-inc/Baichuan2-*-Chat` with `model.chat(...)`, the CLI, Streamlit, or API helper.
2. Use `baichuan-inc/Baichuan2-*-Base` with tokenizer plus `model.generate(...)`.
3. Keep chat histories as `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]` for Chat models.
4. For Base models, craft a plain prompt string and decode the generated token sequence.
