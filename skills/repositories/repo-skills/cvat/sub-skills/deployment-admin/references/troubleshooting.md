# CVAT deployment troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| UI not reachable on expected host | `CVAT_HOST` not set, wrong port, proxy/firewall issue, or containers not running | Check `docker compose ps`, host/port mapping, and set `CVAT_HOST` before startup for non-local access. |
| Login works but normal users cannot see tasks | Users lack assigned roles/permissions | Create/use a superuser and assign roles/groups through admin/UI. |
| Browser UI behaves incorrectly | Unsupported browser | Use Chrome/Chromium/Microsoft Edge; avoid Safari/WebKit. |
| Containers exit during startup | Missing dependencies, failed migrations, unexpected backend component, bad worker queue args | Inspect `docker compose logs` for the specific service and verify compose overlays. |
| `createsuperuser` command fails | Server container not running or migrations incomplete | Wait for services, check server logs, and confirm the container name. |
| Docker image build/pull timeout | Registry/network issue | Retry after fixing network/proxy, or use pinned images already available in the environment. |
| Version mismatch after update | Old images/volumes or mixed `CVAT_VERSION` tags | Pin a consistent version, pull/rebuild deliberately, and read upgrade notes before migrating data. |
| Serverless model absent from Models UI | Serverless overlay not enabled, Nuclio function not ready, wrong network/project, or function labels invalid | Check serverless compose services, `nuctl get function`, function annotations, and CVAT logs. |
| GPU serverless fails | Missing NVIDIA runtime/driver, wrong YAML, insufficient VRAM | Verify host GPU runtime before deployment and choose CPU YAML when GPU is unavailable. |
| Tests fail to start services | Existing CVAT containers occupy ports or volumes | Stop conflicting containers; avoid deleting volumes unless data loss is approved. |
| OPA/permission tests fail | OPA container/rules not available or stale | Rebuild/start the OPA service for the test stack. |

## Safe diagnostic order

1. Check service status: `docker compose ps`.
2. Read logs for the failing service only.
3. Confirm compose file list and `CVAT_VERSION`.
4. Confirm database/Redis/OPA dependencies are healthy.
5. Confirm browser and host URL.
6. For serverless, check Nuclio separately from CVAT server health.

## Destructive commands

Commands such as `docker compose down -v`, volume pruning, database reset, or deleting projects/tasks can destroy annotation data. Do not recommend execution unless the user explicitly approves data loss or has a verified backup.
