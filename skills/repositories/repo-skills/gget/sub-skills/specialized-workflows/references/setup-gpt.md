# Optional setup and legacy GPT

Evidence: `gget_setup.py`, `gget_gpt.py`, `docs/src/en/setup.md`,
`docs/src/en/gpt.md`, `tests/test_gpt.py`, and the live signature report.

## `gget.setup`

Live signature:

```text
setup(module: str, verbose: bool = True, out: str | None = None) -> None
```

Supported module values are exactly `alphafold`, `cellxgene`, `elm`, `gpt`, and
`cbio`; an unknown value raises `ValueError`. The function performs external
side effects:

| module | Action and boundary |
|---|---|
| `gpt` | Installs `openai<=0.28.1`, preferring `uv pip` when available, then Python pip; imports `openai` to verify. |
| `cellxgene` | Installs `cellxgene-census`; current Python compatibility may be limited. |
| `elm` | Uses curl with retries/timeouts to download four ELM files. With no `out`, writes into gget's package data directory so `gget.elm` can use them. With `out`, creates a custom folder and writes an independent copy that `gget.elm` will not automatically read. |
| `alphafold` | Warns that the module is unmaintained, rejects Windows, checks OpenMM, installs dependencies, clones/patches AlphaFold into a temporary area, and downloads large model parameters (the docs call out roughly 4 GB). |
| `cbio` | Installs `bravado` and verifies its import. |

`verbose=False` suppresses progress logging but does not make the operation
safe or side-effect free. A `setup` call may change the active environment,
create package data, use pip/uv/curl/git, consume substantial network/storage,
and fail after partial changes. Use a dedicated environment, check Python/OS,
installer availability, disk space, and approval before invoking. Do not run it
as a preflight in a no-network or read-only environment.

For a read-only preflight, inspect install state without `gget.setup`:

```bash
python - <<'PY'
import importlib.util, shutil, sys
print({
    "python": sys.version,
    "uv": shutil.which("uv"),
    "pip": shutil.which("pip"),
    "curl": shutil.which("curl"),
    "git": shutil.which("git"),
    "openai_importable": importlib.util.find_spec("openai") is not None,
})
PY
```

This command does not install or contact a service.

## `gget.gpt`

Live signature:

```text
gpt(prompt: str, api_key: str, model: str = 'gpt-3.5-turbo',
temperature: float = 1, top_p: float = 1, stop: str | None = None,
max_tokens: int = 200, presence_penalty: float = 0,
frequency_penalty: float = 0, logit_bias: dict | None = None,
out: str | None = None, verbose: bool = True) -> str | None
```

The function warns that it is no longer actively maintained, imports `openai`,
assigns `openai.api_key = api_key`, and calls the old
`openai.ChatCompletion.create` endpoint with a single user message. It passes
model, temperature, top-p, `n=1`, `stream=False`, stop, max tokens, presence
and frequency penalties; when `logit_bias` is not `None`, it passes that too.
The test fixture asserts this exact call shape for the default case.

On success, it reads `response['choices'][0]['message']['content']`, logs
`response['usage']['total_tokens']` when verbose, writes the text to `out` if
provided, and returns the text plus a trailing newline. Without `out`, it does
not create a file. If `openai` cannot import, it logs setup guidance and
returns `None`.

The API key is a required argument; this wrapper does not read an environment
variable itself. Keep the key in a secret manager or in process memory rather
than source code, shell history, or output files. Prompts may incur cost and
must not contain secrets or regulated data. `temperature` is documented as
0–2 and penalties as -2–2; validate these values before spending a request.
Because current OpenAI clients may remove `ChatCompletion`, a package/version
check is mandatory. Prefer a maintained client/workflow for new integrations;
use this entry point only for compatibility with an existing gget pipeline.
