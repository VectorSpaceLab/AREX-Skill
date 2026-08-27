# TypeScript Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Node engine mismatch | Node is older than the supported floor | use Node `>=20.19.0` |
| Missing provider SDK | the requested direct LLM client package is not installed | install only the SDK used by the chosen recipe |
| Missing DB driver | `pg`, `mysql2`, or `better-sqlite3` is absent | install the driver for the selected dialect |
| Native binding load failure | the platform-specific artifact is missing or incompatible | check the package metadata, Node version, and platform pair |
| Request identity bleed | a shared instance is used without `forRequest(...)` | create request scopes in each concurrent handler |
| Storage build omitted | the application created BYODB storage but never ran migrations | call `await memori.config.storage!.build()` at startup |
| Cloud request errors | API key, timeout, or base URL configuration is wrong | check `MEMORI_API_KEY`, `MEMORI_TEST_MODE`, and `baseUrl` |

## Recovery order

1. Confirm the Node version.
2. Confirm the provider or DB driver package that the recipe needs.
3. Build storage once if BYODB is enabled.
4. Use `forRequest(...)` for concurrent servers.

## Avoid

- Do not suggest Python package commands for a Node-only task.
- Do not suggest rebuilding native artifacts as the first fix unless the user is
  explicitly debugging the native layer.
