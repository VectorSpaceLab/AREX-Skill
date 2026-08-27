# CI and maintenance reference

This reference covers the Megatron-LM maintainer workflows that connect tests to CI, golden values, container/dependency maintenance, internal GitLab pipelines, and nightly main-to-dev sync.

## PR label decision tree

The main CI workflow derives scope, repeat count, lightweight mode, cadence, and image variant from PR labels.

| Trigger/label state | Effective scope | Repeats | Lightweight | Golden comparison | Use when |
|---|---:|---:|---:|---:|---|
| Merge group | `L1` | 1 | false | yes, for selected rows | Merge queue validation. |
| Label `Run tests` | `L1` | 1 | true | no for lightweight functional path | Fast broad PR validation; good default for code, tests, tooling, dependency, or container changes that should not run full goldens. |
| Label `Run functional tests` | `L1` | 5 | false | yes | New functional tests, re-enabled tests, numerics-affecting changes, golden refresh, or base image bumps. |
| Scheduled/dispatch CI workload | `L1` | 5 | false | yes | Nightly/manual workload path. |
| No label on ordinary PR | `L0` | 5 | false | yes for slim subset | Default slim PR subset only. |

Additional labels:

- `container::lts`: selects the LTS container image path. This is opt-in only; do not add it unless the user explicitly requests LTS validation.
- `Run MBridge tests`: triggers downstream MBridge L1 tests. Without it, MBridge is skipped for ordinary PR pushes.

Cadence defaults to `pr`, `nightly`, or `mergegroup` depending on trigger. The `Run tests` and `Run functional tests` labels bypass cadence filtering, so a manual label can select L1 rows that would otherwise be cadence-filtered.

## CI pipeline shape

The GitHub CI flow is:

1. contributor/maintainer branch is copied to a `pull-request/<number>` branch after `/ok to test <sha>` authorization;
2. pre-flight computes docs-only, external-contributor, merge-group, and deployment state;
3. configure job maps labels to `scope`, `n_repeat`, `lightweight`, `lts`, `cadence`, and downstream MBridge settings;
4. linting runs formatter checks and validates modified golden JSONs for finite values;
5. container build creates dev/LTS/utility images;
6. parser jobs expand unit and functional recipe YAML into workload matrices;
7. unit/integration/functional jobs run on H100/GB200/A100 runners as selected;
8. the aggregate gate reports pass/fail after upstream jobs and external statuses settle.

Do not declare a PR green while required checks are queued, pending, or in progress. External status contexts from internal GitLab may not appear in GitHub Actions job lists; use PR check rollup or the PR checks view as the source of truth.

## Logs and artifacts

When CI fails, the runner stdout is only a starting point.

- Unit tests tee ranks 0 and 3 to stdout. Other rank logs are captured in per-rank log files and uploaded as artifacts.
- Functional tests upload training outputs, TensorBoard-derived actuals, golden comparison logs, and runner logs. Start with rank 0 for pytest/golden failures, then inspect other ranks for NCCL, CUDA, data, or process-exit mismatches.
- Artifact names commonly include `logs-<test_case>-<run_id>-<uuid>` or coverage equivalents.
- Large logs should be read in chunks. Search first for `Traceback`, `FAILED`, `ERROR`, `NCCL`, `CUDA`, `fatal`, `would reformat`, and `line-too-long`.

Useful GitHub CLI patterns:

```bash
# List runs for a PR testing branch.
gh run list --repo NVIDIA/Megatron-LM --branch "pull-request/<PR_NUMBER>"

# Show failed job logs from a run.
gh run view <RUN_ID> --repo NVIDIA/Megatron-LM --log-failed

# List and download log artifacts.
gh run view <RUN_ID> --repo NVIDIA/Megatron-LM --json artifacts --jq '.artifacts[].name'
gh run download <RUN_ID> --repo NVIDIA/Megatron-LM --name '<artifact-name>' -D ./ci-artifacts
```

## Golden-value workflow

Golden values are JSON metric trajectories for functional tests. CI validates changed golden JSON files with a finite-value checker; the bundled `scripts/check_golden_values.py` provides the same finite-value behavior for local/synthetic fixtures.

Refresh goldens only from a relevant CI run, not by hand editing:

1. Identify the GitHub Actions workflow run ID that produced the desired functional artifacts.
2. Decide scope:
   - `only-failing` for fixing failing/cancelled jobs only;
   - `all` for a full refresh.
3. Ensure a short-lived GitHub token is available for the command. Deriving one from authenticated `gh` is preferred; never commit or print token values.
4. Run the repo's golden download helper with `--source github --pipeline-id <RUN_ID>` and add `--only-failing` when using failing-only scope.
5. Run a finite-value check over every updated `golden_values*.json` file.
6. Run the relative-difference comparison helper and summarize the change for the PR.

Relative-difference summary semantics:

- The comparison rows are `(file, metric)` pairs.
- `n_steps` is the count of shared finite step values used.
- `avg_rel_diff = mean((old - new) / old)` over shared steps, skipping old values with `|old| < 1e-12`.
- The sign matters: positive means the new run is smaller than old on average; negative means it is larger.
- Sort and bucket by `|avg_rel_diff|` for review. Sub-`1e-4` `lm loss` or `num-zeros` movement is often run-to-run or container drift; rows around or above `1e-3` deserve focused review.
- `iteration-time` is noisy and usually not a correctness signal by itself.
- Brand-new golden files have no baseline and must be reported separately from files included in the diff summary.

PR summary should include: run ID, failing-only vs full refresh, number of golden files updated, headline per-metric median/max `|avg_rel_diff|`, bucket counts, and an interpretation that distinguishes expected container/numerical drift from suspicious regressions.

## Internal GitLab trigger safety

The internal trigger helper is maintainer-only and requires a GitLab remote plus a token with API scope. The unsafe behavior is central:

- A real invocation force-pushes the current local branch to the internal GitLab remote under `pull-request/<branch>`.
- It then triggers a pipeline on that ref with variables such as functional scope, repeat count, selected cases, clusters, and time limit.
- Always run a dry run first and verify the remote name, hostname, source branch, and destination ref.
- Never run it from a shared branch, protected branch, or branch containing unreviewed unrelated work.

Safe preflight pattern:

```bash
python tools/trigger_internal_ci.py --gitlab-origin gitlab --dry-run
```

Only after the dry-run output matches the intended target should a maintainer consider removing `--dry-run` and adding optional functional-test flags.

## Linting and formatting

The repository formatter entrypoint targets changed Python files under Megatron Core and tests. It requires Git >= 2.31, fetches a base ref, then runs black, isort, pylint, ruff, and mypy.

Common invocations:

```bash
# Check mode, no edits.
BASE_REF=main CHECK_ONLY=true SKIP_DOCS=false bash tools/autoformat.sh

# Fix mode.
BASE_REF=main CHECK_ONLY=false bash tools/autoformat.sh

# After editing imports in Python files.
uv run isort <file1>.py <file2>.py
```

Tooling expectations:

- The linting dependency group installs black, isort, ruff, pylint, and mypy.
- Black/isort line length in the project config is 100 for those tools, while contribution prose may mention a broader style target; follow the current config and CI output.
- The formatter computes changed files against the merge-base with the selected base ref; if a file is not under the formatter's changed-file set, run the relevant tool explicitly.
- `mypy` warnings in the wrapper are non-blocking in the script (`|| true`), but CI logs should still be reviewed for real type regressions.

## API compatibility check

A dedicated script checks Megatron Core public API breakage against a baseline ref using Griffe. Typical use:

```bash
python scripts/check_api_backwards_compatibility.py --baseline core_r0.14.0
```

The checker ignores objects decorated as internal, deprecated, or experimental. It also ignores some non-signature breakages and `__init__` parameter moves. Use it when changing public symbols, exports, config dataclasses, or `megatron.core` APIs. If the script prints debug sections in addition to findings, triage the actual breaking-change list before deciding whether a compatibility shim or documented break is needed.

## Base-image and dependency maintenance

### Dev base image bump

A dev base-image PR must update both the GitHub/local pin and the GitLab matrix pins in the same change:

| Pin site | What to update |
|---|---|
| `docker/.ngc_version.dev` | Single-line `nvcr.io/nvidia/pytorch:<YY.MM>-py3` value used by the dev Dockerfile build. |
| `.gitlab/stages/01.build.yml` | Both `IMAGE_TYPE: dev` rows: amd64 and arm64 `BASE_IMAGE` values. |

Do not touch `docker/.ngc_version.lts`, LTS Dockerfile rows, or LTS requirements unless the user explicitly asked for an LTS bump.

After a dev base-image bump:

1. Open a draft PR with `Run functional tests`.
2. Expect golden drift across H100/GB200 suites; refresh goldens from the first relevant run and include a relative-difference summary.
3. If a small number of tests hang, OOM, or show true regressions, do not fold fixes into the base-image bump. File tracking issues and mark affected recipe scopes as broken/disabled with a comment.
4. Before review, verify all dev pin sites show the same tag.

### uv.lock and dependency updates

- `uv.lock` is generated; do not resolve conflicts by hand.
- Dependency changes should be resolved inside the project container with the pinned toolchain.
- For a `uv.lock` conflict, take the target branch lockfile as a base, then rerun the resolver so the lock reflects the merged `pyproject.toml`.
- Automated lockfile bump PRs are expected to sign off commits and run functional tests.
- LTS dependencies are pinned separately from the dev dependency graph; do not add new packages under an obsolete LTS optional-dependency path.

## Nightly main-to-dev sync

Nightly sync is a high-risk maintenance flow because `main` and `dev` may have diverged through squash-merge chains. The sync preserves dev-only additions unless a specific main commit intentionally removed them.

High-risk files and rules:

| File or group | Rule |
|---|---|
| `.github/CODEOWNERS` | Never modify in a sync; restore dev's version if it changes. |
| `pyproject.toml`, `uv.lock`, `docker/Dockerfile.ci.dev` | Treat as a coupled dependency/container triple. Do not blindly take main's version; reconcile git sources and regenerate the lock only in the proper container. |
| Selected training/bootstrap files | Main may be intentionally preferred for known semantic conflicts, but every override needs an API mismatch audit. |
| Interface-heavy model/optimizer/data files | Check caller/callee signatures after conflict resolution; accidental method-name or parameter mismatches often compile but fail at runtime. |
| Deleted files | Restore only if current merged code imports them; otherwise verify whether dev intentionally deleted them. |

Nightly sync PR shape:

- Create from `dev`, merge `main`, resolve conflicts surgically, then open a draft PR.
- Include Python-only line stats, files taken from main, restored deleted files, advisory audit dispositions, and remerge-diff conflict resolution notes.
- Add `Run functional tests` and `Run MBridge tests` immediately.
- Iterate CI to green before marking ready. Do not classify queued/pending jobs as infrastructure-blocked; wait for terminal status.

## CI issue response and filing

When asked to respond to an issue or file a CI failure issue:

- Fetch issue/PR/run metadata, comments, labels, state, and failing job names before drafting conclusions.
- Quote actual error snippets; do not guess root cause from filenames alone.
- Search for duplicate issues before filing a new one.
- Keep external contributor replies concise, respectful, and technically grounded.
- Do not post comments or create issues without explicit user approval unless the user specifically asked to perform that action.
