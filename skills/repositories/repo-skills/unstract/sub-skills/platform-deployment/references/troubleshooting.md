# Platform Deployment Troubleshooting

## Common Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `run-platform.sh` exits immediately | Git, Python, Docker, or Compose is missing / unreachable | Install the missing runtime or fix Docker daemon access before retrying |
| Services start but the UI is wrong | The frontend runtime config was not regenerated | Rebuild / regenerate the frontend runtime config before reloading the browser |
| Backend / platform-service env files look inconsistent | The bootstrap script merged or created env files from the service samples | Re-check the generated service env files rather than the root shell environment |
| `x2text` works in isolation but not in the stack | The platform API key, execution dir, or DB backing x2text is missing | Confirm the service env plus the execution directory mount |
| Tool-sidecar shuts down too early | SIGTERM was forwarded directly to Python instead of being trapped in the shell | Keep the shell wrapper in place so the log processor can finish cleanly |

## Service-Specific Notes

- The backend and platform-service depend on generated encryption / auth settings. If those values are blank or stale, downstream services can start but behave inconsistently.
- If Docker is healthy but Compose still fails, check whether the repo expects `docker compose` or `docker-compose` on this machine.
- Port conflicts are usually a symptom of a previous stack still running rather than a code defect.
- If a service launches in `--dev` mode but live reload never happens, confirm the file watcher / host volume behavior for that service.

## What Not To Debug First

1. Do not start with application code if Docker and the env files are wrong.
2. Do not debug the frontend build if the backend URL or runtime config was never produced.
3. Do not debug the x2text service before checking the platform API key and execution directory configuration.
4. Do not debug sidecar log delivery before confirming Redis connectivity.
