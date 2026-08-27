# Protobuf and Maintainer Notes

Read this only for SwanLab maintainer-style tasks such as protocol changes, package builds, focused native tests, or PR review. Package users who only log experiments usually do not need it.

## Scope boundary

The generated repo skill primarily supports operating SwanLab as a Python package. The repository also contains maintainer evidence:

- Python package metadata, version source, and build/test commands.
- Protocol definitions and generated Python/Go code.
- A Go `core/` subtree used by SwanLab internals.
- Repo-local PR review skills for Python SDK and Go core review.

Do not ask a future package user to open or run checkout-local scripts. Use this reference to explain the workflow if the user is actively maintaining a SwanLab checkout.

## Package build and test commands

When maintaining the repository, the Makefile documents these command families:

| Task | Typical command | Notes |
| --- | --- | --- |
| Sync development dependencies | `uv sync --all-extras` | This is a maintainer/developer setup, not required for package users. |
| Unit tests | `uv run pytest tests/unit` | Prefer a focused path when investigating a specific module. |
| Benchmarks | `uv run pytest tests/benchmark` | Skip for ordinary skill validation; benchmark-scale work needs explicit budget. |
| Formatting | `uvx ruff check --select I --fix .` and `uvx ruff format .` | Formatting/lint tasks are maintainer-only. |
| Build package | `uv build` | Version is read from the package version metadata. |

## Protocol generation

Protocol source definitions live under the repository's protocol source tree and generated outputs are committed for Python and Go consumers. Maintainer guidance:

1. Treat protocol source as authoritative.
2. After changing protocol definitions, regenerate both Python and Go outputs using the repository's documented protocol generation command.
3. Do not reuse or change published protobuf field numbers or enum meanings.
4. Keep record envelopes append-only enough that old local run records remain parseable or skippable.
5. Run focused Python and Go protocol tests/builds before claiming the protocol change is safe.

The generated skill does not bundle the source generation script because it mutates repository files and depends on the maintainer checkout layout.

## Go core boundary

The Go core subtree is relevant when a task changes process lifecycle, console logging, gRPC/protobuf contracts, Go modules, or cross-platform core behavior. For package usage questions, route back to the Python SDK/CLI sub-skills instead.

Maintainer checks commonly include Go tests, lint, and build commands from the repository's Makefile. Cross-platform behavior should account for Linux, macOS, and Windows CI rather than relying only on the current machine.

## Existing repo-local PR review skills

The repository has repo-local PR-review skills for SwanLab Python SDK and Go core changes. They are maintainer review guidance, not runtime package usage guidance. If the user asks to review a SwanLab PR, load the appropriate PR-review skill from the checkout rather than using this operating skill as a replacement.
