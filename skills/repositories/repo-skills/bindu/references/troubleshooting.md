# Cross-Cutting Troubleshooting

## Fast routing

| Symptom | First place to read |
|---|---|
| `bindu` command missing, import fails, wrong package version | root `scripts/check_bindu_install.py`, then `deployment-runtime-and-operations` |
| Handler rejected, config missing field, task stays submitted/working, malformed UUID | `agent-authoring-and-a2a/references/troubleshooting.md` |
| 401/403, DID signature, private catalog, x402 402, mTLS certificate error | `security-identity-and-payments/references/troubleshooting.md` |
| TypeScript SDK registration, `:3774` refused, callback timeout, proto drift | `grpc-and-language-sdks/references/troubleshooting.md` |
| boxd deploy, source tarball, `.env` leakage, Postgres/Redis, OTLP/Sentry, tunnel | `deployment-runtime-and-operations/references/troubleshooting.md` |
| Gateway `/plan`, recipes, peer auth, Inbox personal agent, contacts/webhooks | `gateway-inbox-and-orchestration/references/troubleshooting.md` |

## Install/import checklist

1. Confirm Python is `>=3.12`.
2. Confirm the installed distribution is `bindu` and imports `bindu`.
3. Confirm the `bindu` console script exists.
4. Run `python -m pip check` in the environment that will execute Bindu.
5. If using TypeScript SDK or Gateway/Inbox, separately check Node and npm dependencies in that package directory.

## Port checklist

Default ports:

| Port | Owner |
|---|---|
| `3773` | Bindu HTTP/A2A server |
| `3774` | Bindu core gRPC server or Gateway default when run separately |
| `3775` | Inbox Vite UI |
| `3787` | Inbox Hono API |
| `5773`, `5776` | Inbox demo peers |

Use a process/port check before assuming a package bug. Stale local servers are common when developing SDK or Inbox flows.

## Generated code

If imports under generated gRPC packages fail or protocol fields drift, do not patch generated files. The source of truth is the proto contract; regenerate stubs and run the relevant build/tests.

## Credentialed workflows

Do not debug live external-service workflows by guessing credentials. Ask which service is in use and verify non-secret facts first: endpoint URL, enabled setting, expected auth mode, health endpoint, token presence without printing values, and whether the workflow is local/mock/testnet/production.
