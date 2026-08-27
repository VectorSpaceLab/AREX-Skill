---
name: repo-development
description: "Contribute to Feast itself: setup, scoped tests, lint/type checks,
  docs/blog placement, protobufs, Go/Java/operator awareness, PR conventions,
  and safe native verification selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Feast Repo Development

Use this sub-skill when the user asks to modify Feast source code, add or reuse tests, run contributor checks, update documentation, regenerate protobufs, touch Go/Java/operator code, prepare a PR, or choose safe verification commands for a Feast repository change.

## Route First

- Use this sub-skill for Feast contributor setup, source-tree orientation, Makefile targets, `uv`/`pixi` workflows, scoped `pytest`, `ruff`, `mypy`, docs placement, protobuf generation, Go/Java commands, PR conventions, and safe native verification selection.
- Route end-user feature repository creation, `feast init`, `feature_store.yaml`, `feast apply`, and `feast plan` to `../feature-repos-and-cli/SKILL.md`.
- Route Feast object modeling with `Entity`, `Field`, `FeatureView`, transformations, or feature services to `../feature-definitions/SKILL.md`.
- Route retrieval, materialization, `push`, and online/historical feature API behavior to `../retrieval-and-materialization/SKILL.md`.
- Route feature servers, registry/offline servers, remote stores, TLS/auth/RBAC serving to `../servers-and-remote/SKILL.md`.
- Route optional backend/store/provider implementation design to `../integrations-and-extensibility/SKILL.md`; return here for Feast-core tests, docs, lint, and PR workflow.

## Fast Path

1. Confirm context: changed files, intended behavior, whether service-backed integration tests are safe, and whether protobufs, docs navigation, Go, Java, UI, or operator code are in scope.
2. Prefer targeted checks first: `uv run ruff check <python paths>`, `uv run ruff format <python paths>`, `uv run bash -c "cd sdk/python && mypy feast/<module>.py"`, and `uv run python -m pytest <specific tests> -v`.
3. Use `python scripts/select_feast_tests.py <changed paths...>` from this sub-skill to suggest small scoped checks without running them.
4. Escalate to Makefile targets only when needed: `make test-python-smoke`, `make test-python-unit`, `make lint-python`, `make mypy-full`, `make compile-protos-python`, `make protos`, `make build-go && make test-go`, or `make test-java`.
5. Avoid broad or service-backed integration suites unless explicitly authorized and prerequisites are available; record skipped unsafe native checks clearly.
6. For docs, update navigation and use the blog path rule: blog posts belong under `infra/website/docs/blog/`; other docs belong under `docs/` and should be discoverable from navigation.

## References

- `references/development-workflows.md` for setup, source-tree orientation, Makefile targets, PR conventions, and language/component awareness.
- `references/testing-guide.md` for safe test selection, unit vs integration boundaries, markers, and difficult change examples.
- `references/docs-and-protos.md` for docs placement, blog rules, protobuf generation, Go/Java/operator notes, and generated artifact checks.
- `references/troubleshooting.md` for install/import, optional extras, validation, CLI/API misuse, credentials, service prerequisites, and workflow failures.
- `scripts/select_feast_tests.py` for advisory scoped command suggestions from changed paths; it does not execute tests or require a Feast checkout.
