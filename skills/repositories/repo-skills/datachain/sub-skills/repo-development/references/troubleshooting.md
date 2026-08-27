# Repo Development Troubleshooting

Use this reference for failures that happen while editing, testing, packaging, or
reviewing DataChain itself.

## Dirty or Stale Checkout

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Generated skill provenance commit differs from the current checkout | The repository changed after the skill was generated. | Run the root provenance check and refresh the repo skill before trusting source-specific guidance. |
| `git status` shows generated skill artifacts only | Skill production dirtied the checkout. | Treat source code as clean if changes are confined to generated `skills/` artifacts. |
| `git status` shows source/docs/test/config edits | Runtime package behavior may no longer match this skill. | Use `refresh-repo-skill` after source work or re-run focused evidence collection. |

Run `python scripts/snapshot_repo_state.py` from any DataChain checkout to print
commit, branch, dirty paths, Python version requirement, and optional extras.

## Missing Optional Dependencies

| Symptom | Interpretation | Recovery |
| --- | --- | --- |
| Base `import datachain` fails | Core package or base dependency problem. | Run `python -m pip check`, inspect package install, and test `tests/unit/test_module_exports.py`. |
| `import datachain.torch` fails with a missing-dependencies message | Expected when `datachain[torch]` is not installed. | Install only `datachain[torch]` if the selected workflow needs PyTorch helpers. |
| Example tests fail importing model/API packages | `examples` extra or external service dependencies are missing. | Install `datachain[examples]` only for example verification and skip credentialed calls unless approved. |
| HF/video/vector/Postgres/Zarr imports fail | Narrow optional extra not installed. | Install the specific extra and add a focused test for that optional path. |

Do not add broad extras to a minimum inspection or CI job unless the test surface
requires them.

## Test Failures vs Harness Artifacts

- A value difference between backends is a real bug candidate.
- A crash in a long shared remote/backend run may be a harness artifact. Rerun the
  smallest failing test in isolation before redesigning logic.
- For CLI/parser changes, prefer pure parser unit tests before invoking commands
  that touch local stores, cloud storage, Studio, or user directories.
- For storage/client failures, separate local filesystem behavior from cloud
  credentials, public-bucket anonymous access, and object-store service limits.

## Schema and Backend Regressions

If a change touches nested models, column naming, SQL types, nullability, hidden
fields, or query operations:

1. Read `schema-backend-change-matrix.md`.
2. Write the affected path/backend/composition matrix before coding.
3. Add permanent tests that assert read-back values.
4. Run local SQLite tests plus the strict backend or mocked converter tests that
   match the claim.
5. Do not claim ClickHouse/BigQuery/Snowflake/Postgres behavior from SQLite only.

Common failure signals:

- `SignalResolvingError`: column path is missing, misspelled, or no longer
  present after `select`/`select_except`/`merge`/`union`.
- `DataChainParamsError`: expression is not valid for a SQL function, a Python
  callable was supplied where a native expression is expected, or a complex
  object was passed to an aggregate that needs scalar leaves.
- Nulls appear/disappear across backends: check nullable SQL type conversion,
  optional model sentinel columns, collection limitations, and export/hydration
  paths separately.
- Union succeeds in one arm order but fails in the other: test both orders and
  update schema widening rules carefully.

## CLI and Studio Development

- Studio tests often require mocked clients or configured tokens. Do not run real
  job/pipeline mutations without explicit credentials and user approval.
- `datachain auth token` prints a secret; avoid it in automated logs.
- Closing `job logs` or local follow output does not cancel a remote job; tests
  should model cancellation explicitly with `job cancel` behavior.
- Parser changes should update docs and command help tests together.

## Documentation Drift

When source signatures or public flags change:

- update the relevant docs and generated command references;
- run doc build when public API docs or mkdocs pages changed;
- avoid documenting private implementation paths as public behavior;
- update this repo skill by refreshing if the public operating surface changed.

## Comments and Docstrings

- Prefer clear code over comments.
- Public APIs should have docstrings; internal helper comments should explain
  durable invariants only.
- Avoid change-history phrasing such as "previously", "now", "this PR", or
  "regression" in comments. Git history owns that story.
