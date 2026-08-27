# Troubleshooting serving and CLI

Start with read-only evidence. Do not turn a missing dependency or malformed
input into an accidental server, provider call, rewrite, training run, or remote
upload.

```bash
uv run python scripts/check_cli_surface.py --mode static
uv run python scripts/check_cli_surface.py --mode help --target root
uv run python scripts/check_cli_surface.py --mode help --target serve
```

The checker never starts a server. Preserve the original error, command, Mellea
version, selected extra, backend route, and whether any file or remote side
effect already occurred.

## Installation and command discovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| `m: command not found` | Active environment does not expose the package entry point | Use `uv run m --help`; run the static checker; add `mellea[cli]` to the active project rather than using a global executable |
| Import error says the `m` CLI requires extra dependencies | Typer is absent | `uv add "mellea[cli]"`, then rerun help only |
| `m serve` says extra dependencies are required or names FastAPI/Uvicorn | `server` extra is absent | `uv add "mellea[server]"`; do not probe by launching the server |
| `m alora` fails on Transformers, PEFT, TRL, datasets, Torch, or Hub imports | Hugging Face stack is absent or incompatible | Add `mellea[hf]`; render `m alora ... --help`; verify device and version compatibility before training |
| Root help imports a backend or fails on a heavy optional package | Wrong/stale installation or path shadowing | Compare `uv run which m`, installed package version, and static module locations; remove a local `cli.py`/`cli` shadow only after confirming it is unintended |
| Help differs from this skill | Installed release is not `0.8.0.dev0` | Treat installed help and metadata as authoritative, and update the operating plan rather than forcing old flags |

The `server` extra includes `cli`, but neither one installs all providers. Route
provider extras and credentials to `backends-and-models`.

## Startup and socket failures

### App file or callback failure

Symptoms include file-not-found, an import traceback before Uvicorn starts, no
`serve` attribute, or an incompatible callback signature.

1. Confirm the explicit app path names a readable Python file.
2. Compile without executing top-level code:

   ```bash
   uv run python -m py_compile app.py
   ```

3. Review top-level imports and initialization for model downloads, missing
   optional packages, provider calls, or local-module shadowing.
4. Confirm a callable named `serve` accepts the required keyword names `input`,
   `requirements`, and `model_options`.
5. Do not import the app merely for inspection if its top-level code is not
   trusted or is side-effectful.

### Address already in use

Inspect listeners without binding:

```bash
ss -ltnp '( sport = :8080 )' 2>/dev/null || true
```

Stop the known stale process through its supervisor, or choose an approved free
port and update the client base URL. Do not kill an unknown PID. If the bind is
permission-denied rather than occupied, use an unprivileged port and review host
policy.

### Starts on an unexpected interface or port

The current defaults are `0.0.0.0:8080`, while older material may say 8000.
Specify `--host 127.0.0.1 --port 8080` explicitly. A client base URL for the
OpenAI SDK ends in `/v1`; raw curl posts to `/v1/chat/completions`.

### Health passes but generation fails

`GET /health` is process liveness only. Verify the selected route, provider
service, credential source, model availability, and one bounded request. Do not
expand health into an expensive generation loop. Backend diagnosis belongs to
`backends-and-models`.

## HTTP request and schema failures

### 400 `invalid_request_error`

Check the response's `error.param` and message. Common causes:

- missing required `model` or `messages`;
- invalid role or multimodal content discriminator;
- `temperature` outside 0-2 or `top_p` outside 0-1;
- `n < 1` at schema validation, or unsupported `n > 1` at the endpoint;
- missing `json_schema` object for `response_format.type=json_schema`;
- app-raised `ValueError` for an unknown model route or invalid input.

An empty `messages` list currently passes the wire schema. Validate and reject it
inside the app with a sanitized `ValueError`.

### Bad `json_schema`

Use this recovery order:

1. Require a top-level `type: object` and a non-empty `properties` object.
2. Put the bare schema under `json_schema.schema`, with a sibling
   `json_schema.name`.
3. Give ordinary properties and array items an explicit supported `type`.
4. Replace external `$ref` with a local `$defs` or `definitions` reference.
5. Remove recursive references, tuple arrays, and unsupported constraints.
6. Do not combine named properties with schema-valued
   `additionalProperties`.
7. Test one valid and one invalid instance before a model call.

`strict` is accepted but ignored. `json_object` is not enforced. A valid schema
still has no effect unless the callback declares `format` and forwards it to
Mellea generation.

### 500 `server_error`

The client intentionally receives no internal exception text. Check protected
server logs and separate:

- callback returned an object without the expected output value/metadata;
- callback indexing or type error;
- backend initialization or generation failure;
- provider timeout, authentication, quota, capacity, or unavailable model;
- unsupported backend/model option forwarded from an unknown request field.

Filter unknown `model_options`. Reproduce with one local, bounded request. Do not
log request credentials or full multimodal payloads.

### Model field is echoed but the wrong backend ran

This is expected unless the application implements routing. `model` is metadata,
not an automatic switch. Inspect the fixed server-side route table, reject an
unknown alias, and keep backend construction out of client data.

### Browser fails while curl works

The built-in app does not add CORS policy. Add a narrow allowed-origin policy at
a controlled wrapper/gateway. Do not enable every origin on an unauthenticated
endpoint.

## Streaming failures

| Symptom | Cause | Recovery |
|---|---|---|
| Stream arrives as one large content chunk | Callback returned an already-computed result | For streaming requests, return an uncomputed thunk from async generation with `await_result=False` or equivalent |
| No incremental chunks despite an uncomputed thunk | Backend does not support true async streaming, or a proxy buffers SSE | Verify backend capability; disable proxy buffering; preserve `text/event-stream`; use `curl -N` |
| Usage is null in final SSE chunk | Client omitted `stream_options.include_usage`, or backend metadata is unavailable | Send `{"include_usage":true}` under `stream_options`; verify generation usage metadata |
| HTTP status is 200 but an error appears midstream | Failure occurred after headers were sent | Parse every SSE event through `[DONE]`; inspect protected logs; treat an `error` event as failure |
| Stream error reveals sensitive detail | Current stream error payload includes exception text | Sanitize exceptions at the app/backend boundary and avoid secrets in raised messages |
| Tool deltas cannot be reassembled | Client ignores per-call `index` or assumes one chunk per fragment | Reassemble by `index`; route execution and authorization to `tools-and-agents` |

A false `stream` value is not forwarded to `model_options`; a true value is.
Do not infer streaming mode from key presence alone without checking its value.

## `m decompose` recovery

### Option or path errors

- Use `--input-file`, not `--prompt-file`.
- Create `--out-dir` before the command.
- Use a new, valid `--out-name`; existing per-job directories cause a write
  failure.
- Keep each input-file job on one non-empty line. Blank-only files fail.
- Use only valid non-keyword Python identifiers for repeated `--input-var`.
- For `--backend openai`, provide both endpoint and API key; keep the key out of
  generated or committed files.

### Backend/parsing failure

The decomposition pipeline makes multiple dependent LLM calls and parses tagged
model output. A small or incompatible model may omit expected tags, truncate
responses, create duplicate tags, or create circular dependencies. Before
retrying:

1. preserve logs with `--log-mode debug` only if they do not expose secrets;
2. confirm endpoint/model compatibility and increase timeout deliberately;
3. use a capable model and bounded prompt;
4. make constraints and subtask boundaries explicit;
5. remove the stale output directory only after preserving useful diagnostics.

Directories created by the failing invocation are normally cleaned up, but
pre-existing output and provider side effects are outside that rollback.

### Generated program fails

Review the selected template output, generated validators, imports, environment
variables, route, and model ID. `latest` means `v3` in this release. That
template currently hard-codes `mistral-small3.2:latest` for generated execution
instead of reproducing the decomposition backend/model. The current
`--enable-script-run` flag also does not make v3 expose the documented runtime
CLI. Inspect and edit the generated program rather than assuming either route or
runtime options. Generated Python is untrusted and makes additional model calls.

## `m eval` recovery

### No evaluations load and no result appears

The input loader uses regular JSON parsing. Supply one JSON object or a JSON
array; line-delimited JSON objects are not accepted as input despite the help
wording. Each object requires `id`, `source`, `name`, `instructions`, and a
non-empty `examples` list. Each useful example needs at least one user message.

The runner catches file-loading errors and can return without raising when no
evaluations load. Treat the absence of the expected result file as failure even
if the shell status appears successful.

### Judge route is unexpected

`--judge-backend` defaults to the generator backend, but omitted
`--judge-model` uses the package default model rather than necessarily copying
an explicit generator model. Specify both judge fields when comparison requires
a known route. For judge validity, score semantics, and sampling, use
`sampling-and-evaluation`.

### Output or score surprises

Use exactly `json` or `jsonl` for `--output-format`; other strings are not
strictly rejected and can produce misleading extensions/serialization. A judge
output without a parseable `score` fails as zero. Provider errors can be skipped
because continue-on-error defaults true. Compare expected total inputs with the
result summary, not only pass rate.

## `m fix genslots` recovery

Always begin with:

```bash
uv run m fix genslots PATH --dry-run
```

The migration is line-based. Review every match, ensure version control or a
backup, and compile/test the target after a non-dry run. It skips only `.git`,
`.venv`, `node_modules`, and `__pycache__`; other generated, vendor, environment,
or build directories may be scanned. Narrow `PATH` rather than assuming all
dependency folders are excluded.

If an unintended rewrite happened, restore from version control or backup; do
not attempt repeated automatic replacements. A second dry run should report no
old references after a successful migration.

## `m alora` recovery and stop conditions

Stop before execution unless model, dataset, output path, device, compute/disk
budget, credentials, destination, and remote-write approval are explicit.

- **Invalid JSONL:** validate every non-empty row has appropriate `item` and
  `label` values. The current loader substitutes empty strings for missing keys,
  which can silently produce poor training data.
- **Invalid prompt config:** `--promptfile` is JSON and must contain
  `invocation_prompt`.
- **Invalid adapter/device:** use `alora` or `lora`, and `auto`, `cpu`, `cuda`,
  or `mps`. Current code treats any adapter value other than exactly `alora` as
  standard LoRA, so validate before launch.
- **Insufficient memory:** choose a smaller model or an approved machine with
  more memory. CPU fallback is slower and should not be automatic when budget
  matters.
- **MPS trouble:** MPS requires a compatible PyTorch; older versions may force
  CPU behavior.
- **Dangerous output path:** use a new dedicated parent. Training cleanup can
  delete `README.md` in the output parent.
- **Missing Hub token:** authenticate with the approved Hugging Face mechanism
  before upload; never paste a token into arguments or logs.
- **Intrinsic upload assertion:** require existing weights, existing `io.yaml`,
  `OWNER/REPO` naming, a supported base-model path, and private upload. Stage a
  copy because packaging mutates the weights directory by copying `io.yaml` and
  may delete `README.md`.
- **README command waits or uses the wrong route:** it is intentionally
  interactive, uses the default Mellea session without backend-selection flags,
  and uploads only after confirmation. The accepted `--io-yaml` value is not
  consumed in this release. Do not pipe an automatic `yes` into it.

On quota, capacity, network, or Hub failure, first determine whether a remote
repository or partial local output was already created. Do not blindly rerun an
upload or training job. Reconcile the destination and checkpoint, then obtain a
new explicit retry decision.
