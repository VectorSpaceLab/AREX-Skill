# DeepAnalyze cross-cutting troubleshooting

Use the route-specific sub-skill first when possible. This root page only covers the recurring failure patterns that appear across DeepAnalyze workflows.

## Import or path errors

**Symptoms**
- `ModuleNotFoundError` for `deepanalyze`, `main`, `backend_app`, or the CLI/Jupyter modules.
- The environment checker cannot find the checkout.

**Likely causes**
- You are not pointing at a DeepAnalyze checkout.
- The current working directory is wrong for the module you are importing.
- The private inspection environment does not contain the expected packages.

**Fix**
- Run the bundled environment checker from a checkout.
- For API work, use the `API/` working directory when importing the server modules.
- For WebUI v2, use the `demo/chat_v2/` working directory when importing the backend app.

## API client / server mismatches

**Symptoms**
- `/health` works but `/v1/chat/completions` fails.
- `file_ids` appear to be ignored.
- `thread_id` restarts the workspace unexpectedly.
- A client only checks one of `message.files` or `generated_files`.

**Fix**
- Put `file_ids` on the latest user message.
- Put `thread_id` only on the latest user message when continuing.
- Keep the full conversation history across turns.
- Check both `message.files` and response-level `generated_files`.

## Port conflicts

**Symptoms**
- Browser UI, API server, file server, or mock vLLM cannot bind.
- The checker says a default port is already in use.

**Ports to remember**
- `8000`: model endpoint / mock vLLM
- `8100`: file server
- `8200`: DeepAnalyze API server
- `4000`: browser UI frontend

**Fix**
- Confirm which surface is already listening before changing a port.
- Keep the model endpoint and the DeepAnalyze API server aligned on the same base URL.

## Graphics and PDF export issues

**Symptoms**
- Charts show missing Chinese glyphs or wrong minus signs.
- PDF export falls back to Markdown or fails.

**Likely causes**
- `pypandoc`, `pandoc`, or `xelatex` is missing.
- A suitable CJK font is missing.

**Fix**
- Use Markdown as the fallback artifact when PDF prerequisites are incomplete.
- Set a CJK font if the report contains Chinese text.

## Model-serving and GPU issues

**Symptoms**
- vLLM does not start.
- Quantization or tokenizer tag extension fails.
- Memory is too tight for the selected context length.

**Likely causes**
- The GPU memory bucket and command template do not match.
- The checkpoint path is wrong.
- Optional CUDA extras were not installed.

**Fix**
- Route to `model-serving` for the memory table and dry-run command builders.
- Do not assume CPU importability proves GPU readiness.
- Use the dry-run scripts before attempting mutation.

## Training and benchmark issues

**Symptoms**
- Training scripts fail on placeholders.
- Benchmark scripts cannot find data or overwrite assumptions.
- Resume behavior uses the wrong slug or result path.

**Fix**
- Route to `training-and-evaluation` and render the command plan first.
- Replace every placeholder with a concrete model path, data path, and output path.
- Use a stable model slug for benchmark output naming.

## When to stop and route elsewhere

- If the issue is specifically about OpenAI-compatible file/chat semantics, use `api-and-clients`.
- If the issue is about CLI, browser UI, or Jupyter setup, use `interactive-frontends`.
- If the issue is about model serving or quantization, use `model-serving`.
- If the issue is about SFT, RL, or benchmark planning, use `training-and-evaluation`.
