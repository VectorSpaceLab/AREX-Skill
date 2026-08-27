# Testing and release

This reference explains how to choose a validation level and how to handle versioning or release work without introducing accidental side effects.

## Test selection matrix

| Change type | Preferred check | Why | Service / credential requirement |
| --- | --- | --- | --- |
| Package import or dependency drift | Backend package import smoke | Fastest way to prove the backend package still imports cleanly | None |
| Backend logic with no live dependencies | Backend unit tests | Keeps the check local and fast | None |
| API, persistence, permissions, or side effects | Backend integration tests | Verifies the real HTTP and service boundary | Running Compose stack |
| Full end-to-end behavior | Backend e2e tests | Catches flow regressions that unit tests miss | Running Compose stack |
| CLI behavior, config, or command wiring | CLI pytest | Confirms the `yuxi-cli` package remains usable | None |
| Frontend components, stores, or helpers | Frontend unit tests | Keeps browser-free behavior fast and isolated | None |
| Frontend lint or import hygiene | Explicit ESLint check | No-write validation for the Vue app | None |
| User-visible formatting or release cleanup | `make format` | Applies repo-wide formatting and fixups | None, but it rewrites files |
| Service-backed smoke checks | Service-required backend tests | Only for tasks that truly depend on the live stack | Compose services must already be running |

## Native candidates worth remembering

- Backend import smoke: the package import test under `backend/test/unit/`.
- Backend unit suite: the rest of `backend/test/unit/`.
- Backend integration suite: `backend/test/integration/`.
- Backend e2e suite: `backend/test/e2e/`.
- CLI suite: `packages/yuxi-cli/tests/`.
- Frontend suite: `web/test/unit/`.

## Service gates

Use the live stack only when the change truly needs it.

- Compose services are required for backend integration and e2e coverage.
- The usual stack pieces are `api-dev`, `worker-dev`, `web-dev`, `postgres`, `redis`, `minio`, and `sandbox-provisioner`, plus any extra service a specific test explicitly needs.
- The bundled helper does not start or stop services. If the stack is not already up, treat the check as blocked and ask the user to start it manually.
- External model providers, Langfuse, and non-local OCR engines are credential or service gated and should stay out of the default maintainer path.

## Release and versioning workflow

1. Decide the target version before touching files.
2. If the task explicitly asks for a release/version bump, use the repo-owned version-bump helper from the checkout only after confirming the target version and whether it is a development or release bump.
3. Treat that helper as interactive and mutating.
4. Re-check the diff after the helper runs.
5. Commit the version bump before creating the tag.
6. Create the tag after the commit; do not force-overwrite an existing tag.
7. Push the branch and tag explicitly.

### What the bump script changes

- Backend package metadata and workspace metadata.
- Frontend package metadata.
- Docker image tags and related release references.
- Release docs only when you are not in `--dev` mode.

### Development versus release mode

- Use the helper's development mode for intermediate development tags.
- Use release mode only for a real release bump.
- If you do not want docs or marketing text touched, make sure you are in the correct mode before running the script.

## Documentation and contribution policy

- User-visible behavior changes should be reflected in `docs/develop-guides/changelog.md`.
- New formal docs must be added to the VitePress nav in `docs/.vitepress/config.mts`.
- Keep PRs focused on one task and run the smallest suitable checks before opening the PR.
- Use `git diff --check` before commit to catch whitespace mistakes early.
- Keep secrets out of tests, release notes, and examples.

## CI touch points worth remembering

- Backend unit CI currently runs the backend unit test layer on Python 3.12.
- Ruff CI checks backend style and import sorting without editing the repository during CI.
- Docs changes trigger a VitePress build; the local check is `cd docs && pnpm install && pnpm build`.
- `yuxi-cli` is published from the release workflow, so CLI changes should keep the package tests green before a release.

## What not to do

- Do not run the version-bump helper as a casual cleanup step.
- Do not tag before the versioned commit exists.
- Do not claim service-backed coverage if Compose was never running.
- Do not let a docs-only or release-only change expand into unrelated implementation cleanup.
