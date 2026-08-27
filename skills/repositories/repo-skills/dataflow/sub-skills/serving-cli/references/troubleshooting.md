# Troubleshooting

## `dataflow` import or `--help` fails immediately

Symptoms:

- `ModuleNotFoundError: No module named 'colorlog'`
- `ModuleNotFoundError: No module named 'colorama'`
- `ModuleNotFoundError: No module named 'appdirs'`

Likely cause:

- the base installation is incomplete, so the CLI cannot even import its logger or path helpers.

Fix:

- repair the base install before debugging a backend
- do not assume the failure is specific to the command you tried

## `dataflow env` fails in a pipe or background job

Symptom:

- `env failed: [Errno 25] Inappropriate ioctl for device`

Likely cause:

- the environment helper calls `os.get_terminal_size()` and expects a real terminal

Fix:

- run it in a TTY
- or use a non-interactive diagnostic helper instead of piping the command

## API key errors

### `APILLMServing_request`, `LiteLLMServing`, `APIVLMServing_openai`, `LightRAGServing`

- Expect `DF_API_KEY` by default.
- If the environment variable is missing, the constructor raises immediately.

### `PerspectiveAPIServing`

- Requires `GOOGLE_API_KEY`.

### `APIGoogleVertexAIServing`

- Requires `GOOGLE_APPLICATION_CREDENTIALS` to point to a real file.
- Optional project / location overrides come from `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`.

## Timeouts and keepalive

### `APILLMServing_request`

- `connect_timeout` controls how long it waits to connect.
- `read_timeout` controls how long it waits for the response body.
- A `ConnectTimeout` becomes a `RuntimeError`.
- A `ReadTimeout` or a `ConnectionError` whose text says `read timed out` becomes a warning and returns `None`.
- Other connection errors usually become `RuntimeError`.
- The client can tolerate server-side keepalive bytes as long as the final JSON response arrives before the read timeout expires.

### Practical guidance

- If the server queues requests or emits keepalives slowly, raise `read_timeout`.
- If the server is unreachable, check the URL and the network path first.
- Do not confuse connection failure with slow inference.

## Optional dependency warnings

- `vllm` missing: install the vLLM extra or a compatible local serving stack.
- `sglang` missing: install the SGLang extra.
- `litellm` missing: install the LiteLLM extra.
- `sentence_transformers` missing: install the vectors / embedding extra.
- `lightrag-hku` missing: install the RAG extra.
- `openai` missing: install the OpenAI client.
- Google Vertex packages missing: install the Google Cloud AI Platform / BigQuery / GenAI stack.

## Local model download surprises

- `LocalModelLLMServing_vllm`, `LocalModelLLMServing_sglang`, `LocalVLMServing_vllm`, and `LocalModelLALMServing_vllm` download from Hugging Face if `hf_model_name_or_path` is not a local path.
- That download is a real network side effect.
- If you need offline behavior, point the constructor at a real local directory.

## `chat` finds no model

- Ensure the current directory contains a trained adapter directory with `adapter_config.json` and adapter weights.
- Or ensure `<cache>/.cache/saves` contains a recent `text2model_cache_*` or `pdf2model_cache_*` directory.
- Or pass `--model` explicitly.
- For base-model chat, make sure `llamafactory-cli` is installed and on `PATH`.

## `webui` path or launch failures

- `--webui-path` must resolve to a backend directory or a directory that contains `backend/`.
- `webui` installs backend dependencies into the current environment, so a missing package can fail after the download step.
- If `uvicorn` exits early, inspect the backend logs rather than the wrapper alone.

## `APIGoogleVertexAIServing` batch issues

- Batch mode needs the BigQuery client plus the Google GenAI client.
- If batch mode is enabled but the credentials or clients are missing, the constructor may succeed while batch submission fails later.
- `batch_wait=False` returns a batch job name instead of waiting for results.

## `LightRAGServing` setup issues

- Use `await LightRAGServing.create(...)` instead of the raw constructor when you need a ready-to-query instance.
- Make sure document inputs are readable plain-text files.
- If document loading fails, check file permissions and the `document_list` entries first.
