# Maintenance troubleshooting

## TypeScript SDK tests fail immediately

**Symptom:** direct `bun test` fails because no server exists.

**Likely cause:** the TypeScript SDK tests are orchestrated by pytest, which
sets up the needed infrastructure.

**Recovery:** run the pytest-driven TypeScript command from the monorepo root.
Use direct Bun only for type checking.

## Route policy tests fail

**Symptom:** auth or scope policy tests fail after changing a route.

**Likely cause:** a route's auth flags no longer match the policy allowlist, or
a mutating route was granted member-read access.

**Recovery:** inspect whether the route mutates state and avoid using
member-read access on mutating paths.

## DB session rules fail in review

**Symptom:** code holds a DB session during a model/provider call, or writes
through a read-only session.

**Likely cause:** the change crossed async external calls with database state.

**Recovery:** compute external results before opening a DB write session, and
reserve read-only sessions for SELECT-only windows.

## Live LLM tests skip or fail

**Symptom:** provider tests are deselected, skipped, or fail at auth/model
selection.

**Likely cause:** credentials or live model environment variables are missing.

**Recovery:** set the provider-specific variables only when the task requires
live-provider verification.

## Version drift

**Symptom:** API, Python SDK, and TypeScript SDK versions disagree after a
release-adjacent change.

**Likely cause:** only one package manifest was updated.

**Recovery:** inspect all package manifests and changelogs together.

## Script behavior surprises

**Symptom:** a maintenance helper changes more than expected.

**Likely cause:** the helper is intended for a narrow maintenance path such as
embedding configuration or version updates.

**Recovery:** read the script purpose, run dry-run/help modes when available,
and prefer read-only inspection before mutation.
