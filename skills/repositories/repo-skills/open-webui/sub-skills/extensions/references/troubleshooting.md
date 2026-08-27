# Extensions and Multimodal Troubleshooting

## Manifest or dependency failure

- **Symptom**: the extension never loads, or dependency installation fails.
- **Likely causes**: invalid manifest, unsupported package requirement, or a missing optional dependency.
- **Recovery**: validate the manifest first, then install the smallest working example before expanding the dependency list.

## Tool-server timeout

- **Symptom**: tool or MCP calls stall, time out, or fail after partial progress.
- **Likely causes**: slow service, wrong timeout, transport mismatch, or a blocked network path.
- **Recovery**: increase the specific tool-server timeout only after confirming the service is reachable.

## SSL or auth mismatch

- **Symptom**: the tool server is reachable but the call fails on SSL or authentication.
- **Likely causes**: wrong certificate trust, wrong transport mode, or missing credentials.
- **Recovery**: verify the transport and certificate settings separately from the chat workflow.

## Browser helper problems

- **Symptom**: browser-backed loaders or scraping helpers do not start.
- **Likely causes**: `WEB_LOADER_ENGINE` was not set correctly, or the companion browser service is absent.
- **Recovery**: confirm the browser helper endpoint and re-run the workflow with a tiny page.

## Image / audio backend problems

- **Symptom**: image or voice features appear in the UI but fail when used.
- **Likely causes**: missing helper service, wrong backend URL, or a codec/backend mismatch.
- **Recovery**: check the backend endpoint, then test a minimal request before changing the chat prompt.

## Terminal/helper side effects

- **Symptom**: helper execution changes state unexpectedly or fails after a partial run.
- **Likely causes**: the helper has external side effects or its runtime environment is not isolated.
- **Recovery**: use the smallest possible example and confirm the service's expected side effects before widening the scope.

## Safe checks to repeat

- Confirm the helper endpoint before retrying the UI.
- Re-run with a tiny manifest or tiny request body.
- Use the deployment sub-skill to confirm the app itself is healthy before debugging the extension.
