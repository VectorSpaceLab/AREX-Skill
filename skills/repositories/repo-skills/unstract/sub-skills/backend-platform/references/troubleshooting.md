# Backend Troubleshooting

## Common Symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `django.setup()` fails during backend import | Missing test env vars or wrong `DJANGO_SETTINGS_MODULE` | Use `backend.settings.test` and the safe defaults from `configuration.md` |
| `ModuleNotFoundError: No module named 'plugins.apps'` | Import path ordering is wrong and the worker `plugins/` package is shadowing the backend one | Put the backend source root ahead of worker paths when building `sys.path` |
| A route that should exist 404s | The route family is not included in the correct URLconf | Check `routes-and-mcp.md` and the composing URL files |
| A platform MCP request is rejected with 403 | The key tier or HTTP-method mapping does not allow the tool | Check the tool's `required_method` and the key permission tier |
| A platform MCP result leaks credentials | The tool returned a raw serializer / model payload instead of a named field list | Compare the tool with the no-credential-leak tests |

## Route and Auth Pitfalls

- Do not test middleware-authenticated behavior through direct view calls; use the real URL path and the real middleware stack.
- Keep the deployment MCP path and the platform MCP path distinct. Moving the platform server under the whitelisted deployment prefix would remove authentication.
- A read-only platform key is expected to fail against the platform MCP server because MCP transport is POST-only.

## Data and Validation Pitfalls

- Long S3 pre-signed URLs can fail validation if the URL length cap regresses.
- `getExecutionStatus` is not a normal pure read once the run has completed; it can consume the stored result.
- The backend's API / deployment routes intentionally exclude some credential-bearing and destructive operations. Their absence is part of the security contract, not a bug.

## What To Check First

1. Confirm the settings module and test defaults.
2. Confirm the route family that should own the path.
3. Confirm the API-key tier and the tool's equivalent HTTP method.
4. Confirm the backend path order if the import issue smells like shadowing.
