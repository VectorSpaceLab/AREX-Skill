# Troubleshooting

All examples are synthetic. Keep requests, logs, and screenshots free of PHI.

## 1) Missing extras or command not found

**Symptoms**

- `openmed` or `openmed-mcp` is not on `PATH`.
- An import fails for `openmed.service`, `openmed.mcp`, or an adapter family.
- A connector works in one environment but not another.

**Likely cause**

The selected environment does not include the optional extra for that surface.
Some adapter families are intentionally optional and should remain unavailable
when their dependencies are not installed.

**What to try**

- Run the bundled probe script to see which CLI probes and imports pass.
- Use the console script if it exists; otherwise fall back to module execution.
- Install only the extras that the task really needs.
- Keep dependency-light registry discovery working even when optional connectors
  are absent.

## 2) REST service rejects browser or proxy requests

**Symptoms**

- A browser request gets blocked before reaching the app.
- The service returns a trusted-host or CORS rejection.
- A reverse proxy works for one host but not another.

**Likely cause**

The host allowlist or CORS origin list is incomplete, or the proxy is sending a
Host header that is not in the trusted list.

**What to try**

- Add the exact browser origin to the CORS allowlist.
- Add every forwarded Host value to the trusted-host allowlist.
- Keep the local loopback defaults when the service is only for local use.
- Use TLS and authentication before exposing the service outside a trusted
  subnet.

## 3) Error envelope confusion

**Symptoms**

- The caller scrapes human text from stderr or a web page.
- A request fails with a non-2xx status but the cause is unclear.
- A health or validation call returns `503` or `422`.

**Likely cause**

The caller is ignoring the stable JSON error envelope and the request-id header.

**What to try**

- Parse `error.code`, `error.message`, `error.details`, and `error.request_id`.
- Check the HTTP status alongside the JSON envelope.
- Treat common codes such as `validation_error`, `bad_request`, `timeout`,
  `not_ready`, `rate_limited`, `backpressure`, `service_busy`,
  `circuit_breaker_open`, and `internal_error` as machine-readable categories.
- Do not rely on prose strings remaining stable.

## 4) PHI in requests, logs, or screenshots

**Symptoms**

- A shell history entry contains a real note.
- Logs or traces echo source text or identifiers.
- A gateway or client returns a payload that still contains raw identifiers.

**Likely cause**

The workflow is sending raw content through an untrusted boundary or logging
payloads too verbosely.

**What to try**

- Keep examples synthetic or already authorized.
- Use local redaction before any external handoff.
- Avoid logging request bodies, mappings, or raw entity text.
- Prefer offsets, hashes, canonical labels, counts, and provenance in error or
  review artifacts.

## 5) EHR credentials and facility-specific handoffs

**Symptoms**

- OpenMRS, OpenHIM, SMART-on-FHIR, or DHIS2 calls fail with auth errors.
- A facility URL works only from one network segment.
- A dry run succeeds, but a real write-back is blocked.

**Likely cause**

The credentials, base URL, or trust boundary are not configured for the target
facility.

**What to try**

- Keep credentials in a secret store rather than in the command line.
- Use least-privilege accounts.
- Verify the facility base URL, path prefix, and TLS settings.
- For OpenMRS or OpenHIM, stay on the facility-controlled network and confirm
  that the destination endpoint is the one you intended.
- For DHIS2 exports, confirm the organisation-unit tree includes the required
  ancestor level before export.

## 6) FHIR profile validation failures

**Symptoms**

- `openmed fhir validate` returns a fatal or error issue.
- A bundle looks valid locally but fails a profile check.
- An OperationOutcome mentions unsupported or missing paths.

**Likely cause**

The resource release does not match the selected profile or release boundary.

**What to try**

- Confirm whether the bundle is meant for R4 or R5.
- Check the issue paths in the OperationOutcome rather than the raw resource.
- Ensure the required profile metadata is present on the resource or bundle.
- Treat unsupported fields as loss-aware rather than silently fixed.

## 7) OMOP schema or vocabulary prerequisites

**Symptoms**

- A loader reports missing concepts or mapping gaps.
- A round-trip check loses too much structure.
- A concept resolves to zero unexpectedly.

**Likely cause**

The caller did not supply the schema, vocabulary snapshot, or mapping data the
loader expects.

**What to try**

- Provide the facility-approved schema and vocabulary snapshot explicitly.
- Expect unmapped terms to stay at `concept_id = 0` with a reason.
- Verify the source and target resource paths before assuming a loader bug.
- Do not bundle restricted terminology assets into the skill tree.

## 8) MCP schema compatibility

**Symptoms**

- An MCP client cannot negotiate the tool schema.
- A gateway strips headers that the client or server needs.
- A tool call fails after a registry change.

**Likely cause**

The client and server are using different tool schemas or a proxy is not
forwarding required MCP headers.

**What to try**

- Re-read the tool registry and regenerate any adapters that cache tool shapes.
- Forward `MCP-Protocol-Version`, `Mcp-Session-Id`, `Accept`,
  `Content-Type`, and `Authorization` through gateways.
- Keep the negotiated protocol version intact instead of hardcoding a value.
- Re-run the bundled probe to confirm the registry imports cleanly.

## 9) Service vs one-shot CLI decision

**Use the CLI when**

- the task is finite;
- the result can be printed or written once;
- no daemon or shared model pool is needed.

**Use REST or gRPC when**

- the task needs repeated calls, async jobs, browser requests, or streaming;
- a shared warm pool or health/readiness endpoints matter;
- you need typed RPC or a client library.

**Use MCP when**

- the caller is an agent, IDE, or tool-use runtime.

If you catch yourself wrapping a one-shot CLI command in a long shell loop,
move up to the service or MCP surface instead.
