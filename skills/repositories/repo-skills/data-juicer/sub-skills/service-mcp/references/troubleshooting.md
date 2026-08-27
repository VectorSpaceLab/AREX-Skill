# Troubleshooting

## Missing packages
- Install `fastapi`, `mcp` / `mcp[cli]`, and `uvicorn` before debugging the service.
- If the service imports fail, confirm that `data_juicer` itself is importable first.

## Route and encoding issues
- Check whether the request should be GET or POST.
- Make sure nested values are encoded with the expected JSON convention.
- Confirm whether `cfg` should be a JSON string, dict, or already-initialized config object.
- If `skip_return` is set, the response body may be empty by design.

## Tool registration issues
- Verify that the operator list path is correct.
- Confirm that the installed plugin set matches the route you are trying to call.
- If a route is missing, the underlying module may not expose it through `__all__`.

## Transport issues
- Keep the transport consistent between the server and the client.
- Re-check port and host arguments when moving between local and remote calls.

## Operational habit
If a service or tool call fails, test the smallest possible endpoint first, then add parameters back one at a time.
