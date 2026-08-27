# Mellea troubleshooting

Use this as the cross-cutting triage map. Preserve the original traceback and
classify the problem before changing code.

## Install and import

- **`ModuleNotFoundError: mellea`**: install the distribution into the Python
  interpreter that will run the program, then rerun `python -c "import mellea"`.
  Do not assume an activated shell and editor use the same interpreter.
- **Optional backend import error**: install only the matching extra (`hf`,
  `litellm`, `watsonx`, `tools`, `server`, `cli`, or `telemetry`). A successful
  base import does not prove that optional backends are usable.
- **Dependency resolver conflict**: inspect the package's declared extra and
  Python version first. Avoid mixing unrelated dev, notebook, and backend
  variants in a production environment; create a fresh isolated environment
  when a conflict is not reversible.

## API and output contracts

- **Schema parses but answer is wrong**: type annotations enforce shape, not
  facts or task-specific meaning. Add a requirement, deterministic verifier, or
  evaluation route; do not add a parser-only workaround.
- **Validation loops or empty output**: inspect the formatter, requirement,
  sampling strategy, raw provider response, and budget. Use a dummy backend to
  reproduce control flow and do not claim provider quality from that test.
- **Await/stream misuse**: identify whether the result is a lazy thunk,
  awaitable, or async iterator. Use one consumer per stream and await the
  correct result before reading `.value` or final validation.
- **Context contamination**: choose `SimpleContext` for independent calls and
  `ChatContext` only for deliberate history. Reset or clone sessions when
  branching conversations.

## Provider, service, and data boundaries

- **Connection refused or 401/403**: verify the provider service, base URL,
  model name, and credential environment separately. Do not paste secrets into
  code or use a live provider for a unit test.
- **Model/checkpoint not found**: distinguish a package import from checkpoint
  availability. Verify the exact model identifier, tokenizer/adapter match,
  local cache or Hub access, and disk/VRAM before changing Mellea code.
- **Malformed multimodal payload**: use the backend's supported image/audio
  block type and validate media encoding. If a backend cannot accept the
  modality, route to a compatible backend instead of silently dropping content.
- **Server request rejected**: compare the request schema and response format
  with the serving route's reference; inspect model routing and supported
  structured-output features.

## Tools, evaluation, and telemetry

- **Tool call denied or malformed**: run the static tool auditor, validate the
  declared schema, and inspect the execution policy. Never bypass a deny rule
  by embedding shell code in a prompt.
- **Evaluation result is unstable**: separate deterministic assertions from
  LLM-judge or qualitative results; control sampling budget and record the
  provider/model used for each trial.
- **Telemetry exporter or span failure**: install the telemetry extra, disable
  exporters during unit tests, and verify that start and end hooks are paired.
  A completion-only hook cannot anchor a span.
- **Missing usage metadata**: inspect the backend post-processing path and the
  generation metadata contract; do not add duplicate direct metric calls when
  the plugin lifecycle already records metrics.

## Hardware and safety

`torch.cuda.is_available()` is not full model verification. If CUDA is
available but an allocation or model load fails, classify it as device memory
pressure, inspect competing processes, reduce model/context/precision, or use a
compatible fallback. Never claim a CUDA generation route is verified from a CPU
import or a device-availability flag alone.

Do not run training, model downloads, provider calls, shell execution, MCP
servers, long-running HTTP services, or telemetry exporters as part of a
parser/import smoke check. Route those actions to the owning sub-skill with
explicit prerequisites and a user-approved execution boundary.
