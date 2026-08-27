# Contribution and PR reference

This reference distills Megatron-LM's contribution workflow for maintainers and contributors. It is self-contained; use it to prepare PRs, decide reviewer scope, split large changes, and respond to issues.

## Non-negotiable PR rules

- All PRs start as drafts. If a non-draft PR is opened, automation converts it back to draft.
- Contributors must push branches to a personal fork, then open a PR from the fork branch against the upstream repository. Do not push ordinary contributor branches directly to the upstream repository.
- Commits must be signed off with `-s`; repository guidance also requires signed commits with `-S` so verification bots can trust the pushed commit.
- Use imperative, concise commit subjects.
- Keep PR scope tight; do not include unrelated formatting or refactors.
- Mark a PR ready for review only after merge conflicts are resolved and relevant CI is passing.

Typical commit:

```bash
git commit -S -s -m "Fix optimizer state resume validation"
```

Typical draft PR creation from a fork:

```bash
gh pr create \
  --repo NVIDIA/Megatron-LM \
  --head <github-user>:<branch> \
  --base main \
  --draft \
  --title "<imperative title>" \
  --body-file <prepared-body.md>
```

## PR checklist before opening

1. Confirm the branch contains only intended files.
2. Run the minimum relevant tests and formatter/isort checks.
3. Include or update unit tests for behavior changes.
4. Include functional tests and goldens for training/inference/numerical behavior changes.
5. Link a feature issue for larger new features; link an issue for bugs when available.
6. Ensure no secrets, CI tokens, private paths, or local environment names were committed.
7. Create the PR as draft.
8. Add CI labels based on the test-selection decision table, not by habit.

## Ready-for-review and approval flow

1. Draft PR opened.
2. Author marks ready only after conflicts are resolved and CI is passing.
3. Oncall and expert reviewers are assigned based on changed paths.
4. For PRs that change `megatron/core`, after expert approvals the `Final Review` label is applied automatically and final reviewers review repository standards.
5. Once required reviewers approve, the `Approved` label is applied automatically.
6. A member of the mcore engineers group can merge.

Do not ask final reviewers to approve a PR that still has unresolved conflicts, red required CI, missing goldens, or unclear scope.

## CODEOWNERS routing

The CODEOWNERS map assigns review teams by path. Important high-level groups:

| Path pattern | Review implication |
|---|---|
| `megatron/core/` | Core reviewers plus final review path. |
| `megatron/core/models/gpt/`, `bert/`, `common/` | GPT/model-family reviewers in addition to core. |
| `megatron/core/models/mamba/`, `megatron/core/ssm/`, `megatron/core/models/hybrid/` | Hybrid/model reviewers. |
| `megatron/core/models/multimodal/` | Multimodal reviewers. |
| `megatron/core/datasets/`, `tokenizers/` | Dataset/tokenizer reviewers. |
| `megatron/core/distributed/`, FSDP, optimizer, dist checkpointing, pipeline, transformer, MoE, inference, post-training | Specialized core teams for those domains. |
| `megatron/training/` | Training reviewers. |
| `.github/`, `.gitlab/`, `docker/`, recipe paths, functional shell/python test utilities | CI reviewers. |
| `scripts/check_api_backwards_compatibility.py` and API-compat related files | CI/API compatibility reviewers. |
| `megatron/rl/`, `examples/rl/`, `train_rl.py` | Reinforcement learning reviewers. |

Before asking for review, inspect the changed path set and explain why the PR belongs to each reviewer group. If too many groups are pulled in, consider splitting.

## Splitting a large PR

Goal: reduce review burden while preserving independent mergeability.

Constraints:

- Minimize CODEOWNERS groups per PR.
- Keep tests with the production code they validate; do not split tests into a separate PR solely to reduce reviewers.
- If PR B depends on PR A symbols, add compatibility shims or aliases in PR A where practical.
- Dependent PRs should target `pull-request/<base PR number>` while stacked, not the base author's branch name.
- Before merging a base PR, retarget dependent PRs back to `main` and refresh them; otherwise GitHub can close dependents and lose review context.
- Wait for user approval before executing a split plan.

Split-plan workflow:

1. List changed files and map each to CODEOWNERS groups.
2. Cluster files by identical or compatible owner sets.
3. Ensure each cluster can compile and test independently.
4. Keep shared compatibility changes in the earliest PR.
5. Present a table: proposed PR title, included files, owner groups, dependencies, tests to run.
6. After approval, create draft PRs from the proper base, push to the contributor fork, and preserve attribution if the original author differs from the executor.

## Issue handling and external contributor responses

Issue triage expectations:

- Bug reports should use the bug template; regressions in speed or accuracy should use the regression template; feature requests should use the enhancement template.
- One issue per bug or request.
- Reproducible reports receive the fastest attention.
- After two business days without maintainer response, contributors may tag mcore-oncall.

When drafting a response:

1. Fetch issue title, body, labels, state, and comments.
2. Classify as bug, regression, feature request, or question.
3. Search code and recent history for the referenced behavior.
4. Verify any commit hash, symbol, line number, or missing-feature claim before citing it.
5. Search for existing PRs/issues that may address the same topic.
6. Draft a concise, friendly, technically grounded reply.
7. If the report identifies a clean actionable bug, offer a follow-up branch/PR plan rather than only a comment.
8. Do not post without explicit approval unless the user asked you to post.

## PR body content expectations

A useful PR body includes:

- one-line summary of the change;
- linked issue or reason no issue is required;
- tests run and exact CI labels used;
- golden-value update summary when goldens changed;
- compatibility or migration notes when public APIs changed;
- reviewer notes for risky areas such as distributed collectives, checkpoint compatibility, lockfile/base image changes, or sync conflict resolutions;
- confirmation that the author personally reviewed every line.

## Maintainer-specific exceptions

The automated nightly sync bot is a special maintainer workflow that pushes directly to upstream using a service identity. Do not generalize that exception to normal contributor work. For normal human-authored PRs, use forks, drafts, signed commits, and standard review routing.
