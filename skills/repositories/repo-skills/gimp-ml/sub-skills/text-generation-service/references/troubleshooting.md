# Troubleshooting and safe recovery

Use this guide to classify a failure before changing a request or retrying.
Keep all logs free of API keys, authorization headers, full provider URLs with
sensitive query data, and raw user images.

## Route misuse

**Symptom:** 404, method-not-allowed, JSON decode, or missing-key failure.

**Checks:** Use `GET /status` exactly; use `POST` with a JSON body for the two
POST routes; send `Content-Type: application/json`; use the exact lower-case
paths `/download_load_model` and `/run_inference`. Load a pipeline before
inference and include `pipeline`, `model`, `text`, and `source` where required.
The service has no documented form-data or multipart route.

**Recovery:** If an operator-provided loopback process is already running,
probe it with `python scripts/inspect_service.py --probe-status
http://127.0.0.1:PORT --timeout 2`. The inspector sends only `GET /status` and
rejects non-loopback hosts. If no installed launcher or running process is
available, record the route check as blocked rather than starting source code.
Then inspect any image request locally with the payload validator. Do not use
the debug branch that omits `pipeline` as a substitute for a normal inference
response: it returns only an `image` field and is not the documented bridge
contract.

## Model/pipeline mismatch

**Symptom:** `Loaded.` is returned but inference has no expected method, or a
pipeline change behaves as the previous operation.

**Cause:** The cache compares only `model_name`; the same model value can skip
constructor selection even when `pipeline` changed. Unknown pipeline strings
also do not create a model before the response is marked loaded.

**Recovery:** Use a unique pipeline-specific `model` value for each family or
ask the operator to restart the installed application, then issue load and
inference again only under the caller's normal authorization. If the process
cannot be controlled, classify this check as blocked. Treat `Loaded.` as
constructor/cache status only. Never work around this by adding a credential
or making repeated provider calls.

## Base64, shape, and dtype mismatch

**Symptom:** reshape error, layer write error, truncated output, or a visually
corrupt layer.

**Checks:** Decode each `image` and `mask` value locally; confirm standard
base64, positive integer `*_shape`, `uint8`, and
`len(decoded) == product(shape)`. Check that output allocation uses width and
height in the order expected by the bridge (`image_shape[1]`, then
`image_shape[0]`). Do not send encoded PNG/JPEG files as raw pixel buffers.
Use `--field mask` or `--all` with `validate_image_payload.py`.

**Recovery:** Re-export the pixel region as contiguous raw bytes, preserve
channels, and regenerate the paired shape. For outpaint, provide four
channels because the source indexes alpha. For edit, keep image and mask
shapes compatible before any provider call.

## Missing key and network/API errors

**Symptom:** SDK authentication failure, 401/403, timeout, DNS failure,
provider error, or missing image URL.

**Checks:** Confirm only through a secret manager or local operator policy;
do not print the key. Separate missing credential, network reachability,
provider HTTP/API response, quota, and output URL download categories. The
source uses one OpenAI generations operation for text-to-image and DALL-E 2
`images.edit` for the other three, followed by a separate image download.

**Recovery:** Stop by default. A live call requires explicit authorization,
network permission, valid credentials, quota, and cost approval, none of
which are part of this skill's verification. For a no-network check, validate
the bundled static route contract or raw-image fixture only. Never add a real
key to an operator configuration or fixture.

## Local port conflict or unreachable service

**Symptom:** GIMP reports connection refused, an installed launcher cannot
bind, or status returns from an unexpected process.

**Checks:** Validate only `gimpml.port` from the operator-supplied active
configuration:

```text
python scripts/inspect_service.py --config /path/to/operator-config.json
```

Confirm the bridge uses the same loopback port and inspect the listener using
the operator's normal local process tools. A port conflict is not an OpenAI
failure. The bundled inspector never starts or stops a process.

**Recovery:** Stop a conflicting process only with operator approval, or use
the installed application's supported configuration procedure to select an
approved free loopback port for all cooperating processes. Never expose the
service beyond loopback. If no supported launcher or operator-provided process
exists, classify live status verification as blocked.

## GIMP 2 / Python 2 bridge constraints

**Symptom:** Plug-in import fails, `urllib2`/`gimpfu` is missing, or the layer
cannot be created.

**Checks:** The bridge is Python 2 code and depends on GIMP 2's embedded
`gimp`, `gimpfu`, `gimpenums`, GTK-era modules, and pixel-region APIs. The
verified environment has no GIMP and no Python 2; bridge execution therefore
remains unverified. Confirm the bridge's Python 2 runtime and GIMP 2 host
separately.

**Recovery:** Do not port or execute the bridge during self-contained protocol
inspection. Verify only its recorded request sequence and use the inspector's
loopback-only `/status` probe or local protocol fixtures for safe checks. If
the bridge runs in an operator-provided environment, it calls load, calls
inference, decodes raw bytes, and mutates or opens GIMP images; each effect
needs a real GIMP 2 test environment.

## Verification limits

Locally verifiable from this runtime subtree: inspector help, built-in static
route listing, port-only validation of a tiny operator-supplied configuration,
non-loopback rejection, the blocked no-server path, and raw-image protocol
fixtures. The exact route and field contracts are source-backed evidence, not a claim
that every installed deployment has identical behavior. Unverified: an installed
application launcher, successful real `/status`, server bind, model
construction with live dependencies, GPU execution, all OpenAI calls and
downloads, and GIMP 2/Python 2 behavior. Do not upgrade any unverified item to
a success claim.

## Difficult synthetic cases

1. Send a text-edit fixture with valid base64 for `image` but a mask whose
   decoded length is one byte short of `product(mask_shape)`. The client-side
   validator must reject it before any route or provider call.
2. Give the inspector an operator configuration containing `gimpml.port`,
   nested credential-looking fields, and a sentinel value. Assert that it
   prints only the port and generic privacy statement, never the credential
   names or sentinel. Then target a non-loopback URL and assert rejection
   occurs before any socket connection.
