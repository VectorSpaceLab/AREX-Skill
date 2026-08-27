# Release Maintenance Troubleshooting

## Invalid service name

**Symptoms**: The helper refuses the input or the workflow exits during the service validation step.

**Likely cause**: The service key is not one of the supported release-update inputs.

**Recovery**: Use one of `api-gateway`, `mgmt`, `pipeline`, `artifact`, `model`, `console`, or `ray`.

## Chart tag mismatch

**Symptoms**: `.env` updated successfully, but the chart edit fails because the repository block cannot be found.

**Likely cause**: The chart tree no longer uses the expected image repository name or the service has no chart block yet.

**Recovery**: Verify the service-to-tag mapping in the versioning reference. If the service is `ray`, a local helper should treat the chart as `.env` only until the chart gains a Ray values block.

## GitHub Actions credentials are missing

**Symptoms**: Release-please or chart release automation cannot create the PR or publish the package.

**Likely cause**: The workflow needs GitHub tokens or signing keys that are only available in CI.

**Recovery**: Treat the workflow as CI-only. Prepare the local change, then let the repository's GitHub Actions run with the configured secrets.

## Chart release still has stale dependencies

**Symptoms**: The chart release workflow packages an out-of-date chart or the generated chart archive does not match the current dependency lock.

**Likely cause**: The dependencies under `charts/core` were not refreshed before packaging.

**Recovery**: Refresh the chart dependencies, rerun the packaging step, and confirm the chart version before opening the PR.

## API-doc sync updates the wrong repository

**Symptoms**: The workflow opens the PR but the target branch or repository is unexpected.

**Likely cause**: The cross-repository release sync is a CI action and should only touch `instill-ai/protobufs`.

**Recovery**: Confirm the release tag and rerun the sync workflow with the correct release context.
