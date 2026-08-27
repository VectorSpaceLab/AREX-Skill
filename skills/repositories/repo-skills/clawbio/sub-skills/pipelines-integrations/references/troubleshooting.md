# Integration troubleshooting

Use the smallest boundary that proves the issue. An import check proves only
that Python can load a module. A `--help` check proves only that a parser can
start. Neither proves credentials, a webhook, a WebSocket, an MCP handshake,
a provider request, a Nextflow backend, a container image, a reference, or a
successful pipeline.

## Diagnostics first

Run the bundled checker without starting services:

```bash
# Run from the generated ClawBio skill root.
python sub-skills/pipelines-integrations/scripts/check_integrations.py --help
python sub-skills/pipelines-integrations/scripts/check_integrations.py
```

The checker reports importability for optional Python modules and availability
of `python3`, `java`, `nextflow`, and common container/adapter binaries. With
`--pipeline-help`, it may invoke a selected wrapper's `--help`; it still never
starts Nextflow because help exits before execution. It intentionally does not
load `.env`, contact providers, inspect tokens, start a service, pull an image,
or download data. Missing packages/binaries are reported as diagnostics, not
silently installed.

## MCP

### `clawbio mcp` says MCP is missing

Install the optional extra with `pip install 'clawbio[mcp]'` or the equivalent
package-manager command. Keep the MCP dependency below 2 for the current
FastMCP import path. A plain `import clawbio.mcp_server` is expected to work
without MCP installed because the SDK is optional.

### `mcp.server.fastmcp` is absent

Check the installed MCP version. MCP 2.x removed the current binding path; use
`mcp>=1.9,<2` as declared by the package. This is a service-readiness failure,
not a ClawBio catalog or skill failure.

### A local file is refused

That is the intended safe default. Use demo mode, or restart the MCP process
with `CLAWBIO_MCP_ALLOW_LOCAL_FILES=1` only after confirming the client and
operator are trusted to expose local data. The setting applies to input/output
paths and should never be added to a shared/global service configuration.

### A skill is "agent-readable only"

`describe_skill` can serve spec-only entries; `run_skill` cannot execute them.
Select a catalog entry marked runnable or use the core/domain operating skill to
explain the contract. Do not infer a script from a directory name.

## Bots, web, and providers

### Adapter exits before starting

Missing platform token, LLM key, Discord channel configuration, WhatsApp phone
number id, or other required environment is intentional fail-fast behavior.
Set secrets in a protected runtime environment, not source or chat. For
WhatsApp, also configure the app-signature value; missing or invalid
signature verification rejects POSTs by design.

### Bot receives the wrong user's file

Stop and treat as a security defect. File/session stores must be addressed by
the exact authenticated identity (`chat_id`, `channel_id`, or phone). Empty
identity must return no file. Check `scoped_get` and the adapter's audit logs,
without logging genome content or tokens. Never repair this by selecting the
first store item.

### Upload or save fails

Check the extension allowlist, size limit, temporary-file expiry, basename
sanitization, protected filenames, destination confinement, and existing-output
policy. HTML/Markdown/PDF uploads are excluded from guarded genetic-file paths
because active content can act as prompt injection. Use a new explicit local
output directory and preserve the source file until the run is verified.

### FLock returns no route

`FlockRouter` requires the `openai` package and `FLOCK_API_KEY`; its endpoint is
remote. `route_query_safe` converts API/import/runtime errors to a null skill.
Do not treat null as a route, and do not retry by sending patient data to a
third-party provider without explicit authorization. Use local keyword/intent
routing or ask for a clear skill.

### Robotary imports but is unreachable

`robotary.server` importability only builds a FastAPI app and a catalog. A live
port also needs FastAPI/Uvicorn/static files and suitable network binding. The
script binds `0.0.0.0:5112`; protect it before exposing it outside a trusted
host. The static webchat is an OpenClaw bridge client and needs a configured,
authenticated WebSocket gateway; it is not a standalone backend.

## Nextflow and wrappers

### `--check` fails before Nextflow

Read the structured error code, message, fix, and details. Common causes are a
missing/old Java or Nextflow, missing backend, invalid samplesheet, missing
local FASTQ/reference/resource, conflicting reference flags, untrusted/missing
config, output inside the source tree, disallowed remote URI, or invalid
pipeline version/profile. Correct the input or environment and rerun the exact
check. Do not bypass preflight.

### `--check` passes but the run cannot start

Some checks intentionally defer final engine/version or external runtime
behavior. Confirm the selected backend daemon/image, network/DNS/registry,
Nextflow cache, Java options, site profile, licenses, and available disk/RAM.
A check does not pull containers or references and does not guarantee an
institutional profile works.

### Demo fails offline or while pulling

All three nf-core wrappers use upstream public test profiles; demo data and
references are not necessarily bundled. Demo needs network and may fail on
container registry, GitHub, DNS, TLS, or proxy problems. For offline execution,
use a real local samplesheet and local references where the wrapper supports
it; do not claim demo is offline. On a transient pull failure, preserve the
output and logs and retry the same documented command after the network/cache
is healthy.

### Remote input is rejected

This is `REMOTE_INPUT_NOT_ALLOWED` under local-first policy. If the operator
explicitly authorizes network fetching, add the exact wrapper-supported
`--allow-remote-inputs`, record that genetic data/references cross the network,
and ensure the environment supports the URI. Do not confuse a remote work-dir
or public iGenomes mirror with permission to send user reads elsewhere.

### Config or flag is ignored

Use one of the exact aliases `-c`, `--config`, or `--nextflow-config`; the CLI
normalizes them and forwards each config to all three nf-core wrappers. Confirm
that the file exists. Use the wrapper's help to verify its flag. Pipeline
snake_case flags are canonicalized only for these three registered wrappers;
unknown flags and runner-managed `--input`, `--output`, and `--demo` remain
blocked. A Nextflow config is executable Groovy and may be rejected or warned
when it tries to become an unreviewed params source.

### Container/profile failure

Check the actual backend and profile composition. Docker/Podman require a
running/usable daemon and image access; Singularity/Apptainer require image
cache/runtime; Conda/Mamba may need package-channel network or warm caches;
GPU/ARM/Wave require compatible hardware/services. A binary on `PATH` is only a
necessary condition. Use the wrapper's structured error and logs for the
specific fix rather than changing resource labels blindly.

### Timeout, memory, or disk exhaustion

Large sequencing runs can exceed the default wrapper wall-clock cap, scratch
space, RAM, container cache, or published-output space. Increase the exact
`--timeout-hours` or use `0` only when an external scheduler controls runtime;
choose a larger/faster filesystem; use a trusted resource config; and estimate
reference/intermediate sizes before rerun. A killed Nextflow process may leave
containers running; inspect the backend after timeout. Do not delete logs or
resume metadata before diagnosing.

### `--resume` is rejected

The wrapper found a drift in source/version, profile, step/preset/aligner,
parameters, samplesheet/reference checksum, work directory, or demo/real mode.
Use the original command and recorded bundle to restore compatibility, or use a
fresh output directory for a changed analysis. Never force resume by editing the
manifest or deleting provenance; that invalidates the audit trail.

### Run succeeded but no useful handoff

Inspect the wrapper's `result.json` and confirmed files. `handoff_available` may
be false when there is no combined h5ad/counts/expected output, or when only
ambiguous per-sample files exist. For rnaseq, missing metadata/formula/contrast
means an opt-in DE handoff is not launched. For Sarek, callers/resources and
annotation outputs must be confirmed before clinical/domain follow-up. Send
ordinary bundle inspection to [core-runner](../../core-runner/SKILL.md), and do
not invent a downstream command from a filename guess.
