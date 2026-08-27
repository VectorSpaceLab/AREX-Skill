# Deployment Troubleshooting

## Symptoms and Recoveries

| Symptom | Likely cause | Recovery |
|---|---|---|
| `config.yaml file not found` | Host-local launchers run before the template was copied. | Create `config.yaml` from the template and run the root config checker. |
| PostgreSQL connection errors on startup | DB host, user, password, or DB name does not match the deployment mode. | For Docker, use the service hostname from compose. For host-local, point to the local DB host explicitly. |
| Redis connection errors | The broker URL points to the wrong host or the Redis container is not running. | Verify `REDIS_URL` and the compose service name. |
| GUI loads but backend calls fail | nginx route or API base mismatch, or backend not healthy. | Check proxy/service names and backend port expectations. |
| `docker compose` build takes too long | Image build includes apt/pip installs and NLTK downloads. | Use a longer timeout, or prebuild once and then reuse the image. |
| GPU compose fails to start | NVIDIA runtime unavailable, unsupported Docker GPU setup, or CUDA build mismatch. | Treat GPU support as optional. Confirm host GPU passthrough and only then retry. |
| `run.sh` clones text-generation-webui unexpectedly | TGWUI directory missing. | Prefer Docker or create the expected directory only if the user explicitly wants that path. |

## Next References

- For API route or auth errors, switch to `api-service`.
- For workflow/agent runtime errors, switch to `agents-workflows`.
- For toolkit install/download failures, switch to `toolkits-integrations`.
- For provider/vector/resource failures, switch to `models-resources-vector`.
