# Testing, CI, and maintenance troubleshooting

Use this table after identifying the failing surface. Read logs first, then pick the narrowest remedy. Do not refresh goldens, rerun CI, or mark tests broken before distinguishing infrastructure, expected drift, and real regression.

## Pytest and distributed test failures

| Symptom | Likely cause | Diagnosis | Fix / next action |
|---|---|---|---|
| Plain `pytest tests/unit_tests/...` hangs or fails with process-group errors. | Megatron unit tests expect a distributed launcher. | Check whether the test initializes model-parallel or torch.distributed state. | Re-run through `python -m torch.distributed.run --nproc-per-node <gpus> -m pytest ...`; use fewer GPUs only when the test's parallelism allows it. |
| Multi-rank pytest appears hung with little stdout. | Only selected ranks are tee'd to stdout; other ranks log to per-rank files. | Inspect rank log files under the chosen log directory/artifact. Search all ranks for `Traceback`, `NCCL`, `CUDA`, `barrier`, and `timeout`. | Identify the first rank to fail. If one rank exited early, other ranks may be waiting at a collective. Fix the first error, not the later timeout. |
| Distributed run times out at a barrier. | One node/rank never reached the barrier, an earlier training phase failed, or multi-node environment variables disagree. | Compare rank logs around the named barrier; verify `MASTER_ADDR`, `MASTER_PORT`, `NUM_NODES`, `NODE_RANK`, and GPU count. | Fix the earlier failing rank or launch metadata. For multi-node CI, confirm all nodes wrote barrier marker files before timeout. |
| GB200 unit recipe collects no tests. | GB200 unit selection is marker-driven. | Confirm the file has `launch_on_gb200` if it is supposed to run on GB200. | Add the marker only after the test is valid on 4-GPU GB200; otherwise leave it H100/dev-only. |
| Test data warning mentions the canonical shared-data mount. | Unit-test fixture expects shared test data and attempts download if the mount is missing or empty. | Determine whether the selected test actually requires the data. | In canonical containers, mount or populate the documented shared-data location. Outside that environment, skip data-dependent tests or provide a local equivalent rather than treating the warning as a code regression. |
| Logs interleave or hide stdout. | Project pytest options include no capture by default. | Inspect rank logs and consider `--capture=fd` for focused debugging. | Use focused node IDs and capture override for one failure, then rerun without extra flags for CI parity. |

## Functional-test and golden-value failures

| Symptom | Likely cause | Diagnosis | Fix / next action |
|---|---|---|---|
| `lm loss` / `num-zeros` golden mismatch after a container or dependency bump. | Expected numerical drift from CUDA, PyTorch, kernel, or dependency changes. | Compare changed metrics with the relative-difference helper; inspect magnitude and affected suites. | If drift is broad, small, and aligned with the bump, refresh goldens from the CI run and include the relative-diff summary. |
| One model family regresses while unrelated suites are stable. | Real code regression or model-specific dependency change. | Compare failing cases to the PR changeset; inspect first training error and metric direction. | Fix the code or isolate the broken recipe with an issue. Do not mask a targeted regression by refreshing all goldens. |
| New golden JSON contains `NaN`, `inf`, or string variants. | Training produced non-finite metrics or an artifact captured invalid values. | Run bundled `scripts/check_golden_values.py` on the updated JSON files. | Treat as failed validation. Fix the underlying training instability or mark the case broken with an issue; do not commit non-finite goldens. |
| `iteration-time` moved substantially but losses match. | Warmup, scheduler, placement, or host jitter. | Check whether correctness metrics are stable and whether timing movement is isolated. | Usually report as noise; investigate only if the PR targets performance or timing moves with correctness/memory anomalies. |
| Golden download fails with missing GitHub token. | The downloader needs GitHub API authentication. | Check that `gh auth status` works; never print token values. | Use a short-lived one-shot environment variable from `gh auth token` for the download command, then unset it. |
| Golden download from GitLab fails with missing internal variables. | GitLab path requires internal endpoint and read-only API token. | Confirm the user has internal access and variables are set. | Do not invent credentials. Ask the maintainer to provide or run the internal command. |
| Functional case hangs after a base-image bump. | Real regression, GPU/runtime incompatibility, data/cache issue, or infrastructure failure. | Check rank logs, last successful repeat/iteration, NCCL/CUDA errors, and whether rerun reproduces. | If isolated and blocking a base-image bump, file an issue and move the recipe scope to a broken/disabled variant with an inline reason. |

## CI and artifact triage

| Symptom | Likely cause | Diagnosis | Fix / next action |
|---|---|---|---|
| PR appears red but the aggregate gate failed without details. | Upstream job failed; aggregate only summarizes. | Inspect all failed upstream jobs and external statuses from PR check rollup. | Debug the upstream job, not the aggregate gate. |
| Required check is pending/queued. | CI is still running or waiting for runner capacity. | Use PR checks/rollup; do not rely only on Actions job list. | Wait or retrigger according to repo policy. Do not mark ready or call a pending job pre-existing. |
| Artifact download shows no per-rank logs. | Wrong artifact name or failed upload. | List artifacts for the exact run; check retry attempts and UUID-suffixed names. | Download the matching `logs-*` artifact; if upload failed, use runner stdout and job summary to identify the failure. |
| Re-run did not trigger on a fork PR. | `/ok to test <sha>` missing or points at old SHA. | Compare latest branch SHA with the comment body and copy-pr-bot response. | Post a new `/ok to test <latest-sha>` comment after each new commit/force-push. |
| External GitLab status exists but no GitHub job exists. | Internal pipeline surfaced as a status context, not a GitHub Actions job. | Use PR check rollup and GitLab pipeline links if available. | Treat it as a required external check when non-exempt. |

## Internal CI credentials and trigger errors

| Symptom | Likely cause | Diagnosis | Fix / next action |
|---|---|---|---|
| Trigger helper says `--access-token or GITLAB_TOKEN not set`. | Missing internal GitLab token. | Confirm this is a maintainer-only internal workflow. | Ask the maintainer to provide credentials or run it themselves. Never embed a token in commits, logs, or skill files. |
| Dry run points to an unexpected destination ref. | Wrong current branch or wrong GitLab remote. | Dry-run output shows current branch and destination `pull-request/<branch>`. | Checkout/create the intended branch or choose the correct remote before any real trigger. |
| Real trigger would overwrite shared work. | The helper force-pushes current HEAD. | Check whether the source branch is shared/protected and whether unrelated commits are present. | Stop. Use a personal PR branch only; never run real trigger from shared/protected branches. |
| `python-gitlab` import missing. | Helper dependency absent. | Run the help command or inspect Python environment. | Install only the small needed dependency in an appropriate temporary/CI environment; do not mutate a user's environment without consent. |

## Linting and formatting failures

| Symptom | Likely cause | Diagnosis | Fix / next action |
|---|---|---|---|
| CI says files would be reformatted. | Black/isort/ruff check mode found changes. | Run formatter in check mode to reproduce. | Run fix mode if user permits edits, then inspect the diff. |
| Import-order failure after editing Python imports. | `isort` not run or circular import introduced. | Run `uv run isort <edited-files>` and inspect diff, especially `__init__.py`. | Keep ordering changes minimal; if isort introduces circular imports, restore the intentional order with comments only where justified. |
| Pylint line-too-long or missing-docstring failure. | Public API style or docs requirement. | Read the exact pylint code from CI output. | Add Google-style docstrings for public APIs, split lines, or apply the smallest targeted disable if the codebase already uses that pattern. |
| Formatter script claims changed-file set is empty. | The edit is outside the wrapper's diff roots or base ref mismatch. | Compare changed files manually. | Run the relevant tool directly on those files or set the correct `BASE_REF`. |

## Dependency and lockfile conflicts

| Symptom | Likely cause | Diagnosis | Fix / next action |
|---|---|---|---|
| `uv.lock` has merge conflicts. | Lockfile generated on two branches. | Confirm `pyproject.toml` desired final dependency graph. | Do not hand-merge. Take the target/base lockfile, run `uv lock` in the project container, and commit regenerated `uv.lock`. |
| `uv sync --locked` fails after editing dependencies. | `pyproject.toml` and `uv.lock` are inconsistent. | Error usually names missing/extra packages or resolution conflict. | Rerun resolver in the container and commit both files. |
| Dependency missing in CI but present locally. | Local host install diverges from container/uv environment. | Compare the dependency group and container variant. | Use the CI container and appropriate uv group. Avoid bare host `pip install` as proof. |
| LTS dependency path changed unexpectedly. | LTS deps are pinned separately from dev. | Check whether the user explicitly requested LTS. | If not explicit, revert LTS edits. If explicit, update the LTS pin/requirements path and validate the LTS lane. |

## Base-image and container pin mismatches

| Symptom | Likely cause | Diagnosis | Fix / next action |
|---|---|---|---|
| GitHub CI uses new dev image but GitLab uses old image. | Only `docker/.ngc_version.dev` changed; GitLab matrix pins were missed. | Compare the dev pin file and both GitLab `IMAGE_TYPE: dev` `BASE_IMAGE` rows. | Update all dev pin sites to the same `nvcr.io/nvidia/pytorch:<YY.MM>-py3` tag in one PR. |
| LTS image changed unexpectedly in a dev bump. | LTS files or `container::lts` label touched without request. | Review diff and PR labels. | Revert LTS pin/requirements/label unless the user explicitly requested LTS validation. |
| Container build fails after pin bump. | Invalid tag, CUDA/PyTorch dependency break, or Dockerfile stage mismatch. | Inspect build logs and exact base image tag. | Verify tag exists, build public `main` stage for local checks, then triage dependency errors separately from golden drift. |

## Nightly sync failures

| Symptom | Likely cause | Diagnosis | Fix / next action |
|---|---|---|---|
| CODEOWNERS changed in sync PR. | Merge conflict or blanket main checkout touched governance file. | Diff against `dev`. | Restore dev version; do not include CODEOWNERS in sync changes. |
| `pyproject.toml`, `uv.lock`, or dev Dockerfile differs from dev unexpectedly. | Dependency/container triple was overwritten from main. | Diff all three files together; look for missing git source or lock mismatch. | Reconcile only necessary git sources, regenerate lock in container, and document the reason. |
| Runtime `TypeError`/`AttributeError` after conflict resolution. | Main callers and dev implementations have mismatched APIs. | For files taken from main, trace external calls and compare merged implementations. | Add shims, rename calls, or restore dev implementations where dev is ahead. |
| Dev-only functionality disappeared. | Squash-merge chain resolution dropped a dev follow-up. | Compare dev-only lines missing from merge; inspect commit history. | Restore dev-only additions unless a specific main commit intentionally removed them; document evidence. |

## Safety reminders

- `container::lts` and LTS file edits require explicit user request.
- Internal CI real trigger requires dry-run verification first.
- Golden JSONs must be finite and generated from CI artifacts, not hand-written.
- Recipe entries should be disabled with broken/disabled scopes, not deleted, when preserving discoverability matters.
- Draft PRs, fork pushes, signed-off and signed commits, and CODEOWNERS-aware review are part of the repository's normal contribution contract.
