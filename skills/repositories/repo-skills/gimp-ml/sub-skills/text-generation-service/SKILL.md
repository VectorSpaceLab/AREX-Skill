---
name: text-generation-service
description: "Operate the local FastAPI text-generation service and its legacy
  GIMP 2 bridge for text-to-image, text-edit, text-extend, and outpaint requests
  without assuming credentials, network access, model weights, GIMP, or Python
  2."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Text-generation service

Use this sub-skill when a task needs the GIMP-ML local service contract for
text-to-image generation or text-guided image editing. It covers the HTTP
lifecycle, the raw-image JSON protocol, pipeline selection, and the boundary
between the Python 3 service and the legacy GIMP 2 plug-ins.

## Operating boundary

- Treat the service as local-only. The observed default `gimpml.port` is
  `61482`, but validate an operator-supplied active configuration rather than
  guessing the port. The bundled inspector retains and prints only that field.
- This runtime skill is self-contained. Do not open, import, or run an original
  repository checkout to inspect the application or its configuration.
- Do not put an OpenAI key in requests, logs, fixtures, skills, or commands.
  Do not make an OpenAI request during inspection or verification.
- Do not assume a downloaded model, successful remote image URL, GIMP, or
  Python 2. A real server process, GIMP 2 bridge execution, and live OpenAI
  calls are unverified.
- The observed status implementation sets `cuda_available` to false even when
  its host might expose CUDA. This field is not proof that inference is CPU/GPU
  capable. A verification-time tiny CUDA allocation was blocked by host CUDA
  OOM, so GPU execution remains unverified.

## Route lifecycle

1. Obtain the active port from an operator-supplied JSON configuration and
   validate only `gimpml.port` with the bundled inspector.
2. For an HTTP check, use an installed application's documented launcher or an
   operator-provided service that is already running on loopback. This skill
   does not provide or start a server. If no installed launcher or running
   process is available, classify HTTP verification as **blocked**.
3. Probe `GET /status` first. It has no body and is the only route the bundled
   inspector can call. It reports `service`, `cuda_available`, `cuda_total`,
   `cuda_used`, `cuda_free`, `ram_total`, `ram_used`, `ram_free`, `cpu`, and
   `os`.
4. In an explicitly authorized downstream operation—not in this skill's safe
   inspector—a client loads a selected pipeline with
   `POST /download_load_model` using exactly `pipeline` and `model`. The
   observed success is `{"status":"Loaded."}`; `{"status":"Error!"}` is a load
   failure, not a usable model.
5. An authorized client then calls `POST /run_inference` with the exact fields
   for that pipeline and decodes returned `image` plus `image_shape` as raw
   flattened `uint8` bytes. Never use the inspector for either POST route.
6. Pass `source: "gimp2"` only for the legacy bridge. Other values select the
   observed GIMP 3/flattened output method; use `source: "gimp3"` explicitly
   in new clients.

See [the API reference](references/api-reference.md) for route tables and
[the protocol reference](references/protocol.md) for payload validation.

## Pipeline routing

- `text_to_image`: prompt-only generation. The source tool calls DALL-E 3;
  `model` is used as the quality value (`standard` or `hd` in the bridge).
- `text_edit_image`: image plus mask and prompt. The source tool calls
  DALL-E 2 image edit and resizes when the service supplies `image_shape`.
- `text_extend_image`: image, prompt, and `ext_side` (`Right`, `Bottom`,
  `Left`, or `Top`). The source tool builds a transparent extension canvas and
  calls DALL-E 2 image edit.
- `text_outpaint_image`: an RGBA image plus prompt. The source tool calls
  DALL-E 2 image edit using transparency to represent the outpaint area.

Load the same pipeline that will be sent to `/run_inference`. The observed
service caches only one model name and does not robustly reject every
pipeline/model mismatch; a repeated model name can therefore leave the wrong
pipeline object in memory. Use a distinct, meaningful model value or ask the
operator to restart the installed local application when changing pipeline
families. If the operator cannot control that process, classify reload
verification as blocked.

## Safe local verification

From this sub-skill directory, inspect the built-in evidence-only route table:

```text
python scripts/inspect_service.py --list-routes
```

Validate an explicit local fixture or operator-supplied configuration. Only
`gimpml.port` is retained and displayed; unrelated fields and values are
silently discarded:

```text
python scripts/inspect_service.py --config /path/to/operator-config.json
```

When an operator confirms a service is already running on loopback, the
inspector can issue only `GET /status` with a 0.1–5 second timeout:

```text
python scripts/inspect_service.py \
  --probe-status http://127.0.0.1:61482 --timeout 2
```

The probe requires plain HTTP, an explicit loopback host and port, and no URL
credentials, query, or fragment. It rejects non-loopback hosts; it never sends
a POST or prints response values. It checks HTTP 200, a JSON object, and all
exact expected status field names. If no operator-provided process is running,
connection failure is expected and is reported as blocked.

The independent payload tool checks base64, shape, dtype, and byte length by
reading only a local JSON fixture:

```text
python scripts/validate_image_payload.py --input payload.json --decode
```

Never use model-load or inference POSTs as a smoke test. Provider network,
credentials, quota, cost approval, and real model execution are outside this
sub-skill's verification boundary.

## Recovery rules

- Route errors: verify method, JSON content type, required field names, and
  that a load request preceded inference.
- Payload errors: validate every base64 field against its paired `*_shape`;
  reject encoded PNG/JPEG data where raw pixels are required.
- Provider errors: preserve the local failure, remove secrets from logs, and
  classify missing key, network/API response, quota, and returned-image URL
  failures separately. Never retry blindly.
- Bridge errors: check the configured localhost port and Python 2/GIMP 2
  prerequisites. Do not attempt to run the bridge from this self-contained
  inspection skill.

Detailed diagnosis is in [troubleshooting](references/troubleshooting.md),
including intentional source limitations and difficult synthetic cases.

## Evidence and limits

This operating contract is limited to source-backed observations of route
declarations, `gimpml.port`, pipeline behavior, and the GIMP 2 request/response
protocol. The bundled inspector's help, static route listing, tiny config
validation, loopback rejection, and no-server failure path are locally
verifiable without a source checkout. A successful real `/status` response,
installed application launcher, model load, OpenAI generation/edit, output URL
download, GIMP 2 execution, Python 2 compatibility, and GPU execution are not
verified here. Keep those limits explicit rather than presenting the pipeline
as locally runnable.
