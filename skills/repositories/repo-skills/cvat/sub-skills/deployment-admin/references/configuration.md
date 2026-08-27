# CVAT deployment configuration

## Environment variables and image tags

| Variable | Use |
|---|---|
| `CVAT_HOST` | Public host/IP/domain used for browser access and routing. Set before `docker compose up` for non-local access. |
| `CVAT_VERSION` | Image tag selector, for example `v2.71.0` or `dev` depending on the deployment target. |
| `CVAT_NUM_PROXIES` | Number of external proxies in front of CVAT; internal proxy handling adds one hop inside the backend entrypoint. |
| `CVAT_ANALYTICS` | Enables analytics initialization path when set appropriately and analytics components are deployed. |
| `CLAM_AV` | Controls optional ClamAV supervisor include behavior in backend entrypoint logic. |

Configuration support changes across CVAT versions. Validate variables against the compose/Helm files in the target deployment version before applying them.

## Common compose file sets

| Goal | Command shape |
|---|---|
| Basic self-hosted stack | `docker compose -f docker-compose.yml up -d` |
| Development source-build stack | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build` |
| Serverless infrastructure | `docker compose -f docker-compose.yml -f components/serverless/docker-compose.serverless.yml up -d` |
| Test-related services | Test docs combine main/dev/serverless/minio/file-share overlays; use only for repo tests. |

## Admin account

Create an admin/superuser after services start:

```bash
docker exec -it cvat_server bash -ic 'python3 ~/manage.py createsuperuser'
```

For scripted non-production test setups, user creation can be done through a Django shell command, but do not embed real credentials in scripts or logs.

## Backend entrypoint components

The backend entrypoint validates component names and starts server, worker, worker-pool, or nginx processes under supervisor. Worker processes require queue names. This matters when diagnosing containers that exit immediately due to an unexpected component or missing queue argument.

## Serverless configuration

Serverless functions need:

- Running CVAT stack with serverless infrastructure enabled.
- Nuclio project, often named `cvat`.
- Function YAML (`function.yaml` for CPU or `function-gpu.yaml` for GPU).
- Redis environment variables pointing at CVAT's serverless Redis service.
- Docker network matching the CVAT compose network.

Use the auto-annotation sub-skill for model-specific details.

## Browser support

CVAT is primarily tested with Chromium-based browsers such as Google Chrome and Microsoft Edge. Safari/WebKit is not supported; Firefox may work with caveats. Browser choice can be a deployment troubleshooting factor, not only a user-interface preference.
