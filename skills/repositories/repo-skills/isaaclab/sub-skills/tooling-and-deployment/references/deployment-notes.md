# Deployment Notes

## Deployment helpers

Isaac Lab contains deployment-oriented helpers for specialized workflows such as cluster submission, Ray-based execution, and other environment-specific launch paths.

## Safe routing guidance

- Treat cloud or cluster automation as reference-only unless the task explicitly requires it.
- Avoid assuming a deployment helper is safe to execute locally just because it is part of the repository.
- Prefer a wrapper or inspection summary when the helper mutates remote state, provisions infrastructure, or depends on external credentials.

## Explicit exclusions

The following categories are intentionally not treated as baseline runtime workflows for this sub-skill:

- Destructive release automation
- External credential handling
- Cluster provisioning with hard environment assumptions
- Any helper that silently rewrites remote resources or source-of-truth deployment manifests

## When to revisit

If a user asks for a specific deployment path, document the exact constraints first and then decide whether the task should remain a maintainer-only workflow or move into a dedicated deployment skill in a future refresh.
