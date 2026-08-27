# Release and Version Workflows

## When to read

Read this when the task is about version bumps, chart releases, API-doc sync, or the GitHub Actions that maintain release metadata.

## Release-please flow

- `release-please/config.json` tracks the repository release version and the extra file used to keep the README badge in sync.
- The repo uses a simple release model for the top-level package name `instill-core`.
- `releases.yml` triggers release-please on `main` and tags the release series after a release is created.

## Helm chart release flow

- `releases-helm-charts.yml` reacts to changes under `charts/**/Chart.yaml`.
- The workflow updates chart dependencies, packages the chart, uploads the package into the chart repository, and re-tags the release in the chart repo.
- This is a chart-maintainer workflow, not a local deployment step.

## API-doc sync flow

- `sync-version-with-api-docs.yml` opens a PR in `instill-ai/protobufs` after a release is published.
- The workflow rewrites the OpenAPI version in `openapi/v2/conf.proto` to match the release tag.
- This is a CI-only cross-repository update.

## Service version update flow

- `update-service-version.yml` is a reusable workflow that updates a single service version variable in `.env` and the matching image tag in `charts/core/values.yaml`.
- The supported service input values are `api-gateway`, `mgmt`, `pipeline`, `artifact`, `model`, `console`, and `ray`.
- The `ray` case currently has no matching Helm image tag in the chart tree, so a local helper should treat that path as `.env` only unless the chart later grows a Ray block.
