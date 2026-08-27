# Deployment Troubleshooting

## Docker deploy fails early

Symptoms:
- Docker daemon/Compose unavailable.
- Port conflicts.
- Image pull fails.
- Env file missing or stale.

Fix:
- Confirm Docker 24+ and Compose v2 are available.
- Check selected image source and registry prefix.
- Verify `deploy/env/.env` exists and matches intended component set.
- Resolve port policy conflicts before restarting services.

## Containers start but application is unhealthy

Likely causes:
- Backend service URL points at the wrong container/host.
- Redis, Elasticsearch, MinIO, or PostgreSQL/Supabase is not healthy.
- Missing model/provider credentials for the feature being tested.
- SQL migrations not applied or fresh-deploy init out of sync.

Fix:
- Check infrastructure services first.
- Check backend constants/env mapping through backend sub-skill.
- Use SQL migration static checks for schema-related errors.
- Do not paste secret env values into diagnostics.

## Kubernetes rollout fails

Likely causes:
- Namespace, storage class, PVC mode, local-path node, or existing-claim prefix mismatch.
- Helm values not regenerated from env files.
- Image registry not reachable from cluster nodes.
- Pods waiting on secrets/configmaps or volume mounts.

Fix:
- Confirm persistence mode and cluster storage prerequisites.
- Regenerate deployment through the script rather than hand-editing rendered values.
- If local PV data deletion is proposed, confirm backup and user intent.

## Offline package problems

Symptoms:
- Missing image tar, checksum mismatch, registry push failure, or deploy cannot find manifest.

Fix:
- Rebuild the offline package with the intended target and compression settings.
- Verify every target node has loaded images or can pull from the pushed registry.
- Keep registry credentials out of generated artifacts.

## SQL/migration drift

Symptoms:
- Fresh deploy lacks a column/table that upgraded deploys have.
- Tests or services fail with missing relation/column.

Fix:
- Update both migration and fresh-deploy init SQL copies.
- Run the bundled static SQL checker.
- Update backend model/service tests and app version references when required.

## Uninstall safety

Destructive flags can delete Docker volumes, Kubernetes namespaces, or local PV data. Default to preserving data unless the user explicitly asks to delete it and confirms backups/target environment.
