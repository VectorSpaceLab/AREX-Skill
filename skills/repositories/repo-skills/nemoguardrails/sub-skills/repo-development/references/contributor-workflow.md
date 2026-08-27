# Contributor Workflow

This reference applies to a live NVIDIA NeMo Guardrails source checkout. It is for source changes, contribution drafts, and maintainer-style review preparation, not for ordinary package usage.

## Authority and default behavior

- `CONTRIBUTING.md` is the canonical public contribution workflow.
- `AI_POLICY.md` is the canonical AI-assisted contribution policy.
- `AGENTS.md` adds agent-operational rules for direct GitHub actions, validation, generated files, and review readiness.
- When editing under `nemoguardrails/`, also apply the package rules summarized in [provider-integration-rules](provider-integration-rules.md).
- When editing under `docs/`, also apply the docs rules summarized in [docs-and-generated-files](docs-and-generated-files.md).
- Default to drafting issue text, PR text, review replies, and validation summaries for a human to review and submit.
- Do not fabricate identity, authorization, issue assignment, triage labels, CI results, local validation, reviewer approval, benchmark numbers, or compatibility claims.

## Issues

- Search existing issues and PRs before proposing new work.
- Usage questions such as "How do I...?" belong in Discussions, not new issues.
- Use the repository issue templates for bugs, features, documentation issues, and refactor proposals.
- AI-assisted issue content must be reviewed, edited, and owned by a human. If policy or operator instruction does not explicitly authorize direct submission, stop at a complete draft.
- A new issue has no assignment/triage pre-check, but direct issue creation still requires explicit operator instruction and must use repository-approved GitHub tooling, not browser automation.

Useful draft issue comment forms:

```text
I would like to work on this.
Proposed approach: <1-3 sentence summary>
Planned validation: <tests/docs/checks>
```

```text
Is this still being worked on? If not, I would be happy to take it over.
Proposed approach: <1-3 sentence summary>
```

## Pull requests, branches, and direct GitHub actions

Do not push a branch, open a PR, submit a PR, or mark a PR ready unless all applicable gates pass.

Required before direct branch push or PR submission:

1. The user explicitly directs the direct action.
2. A linked issue exists.
3. The linked issue is triaged.
4. The linked issue is assigned to the authenticated GitHub user.
5. Read-only checks confirm the current user and issue state.
6. No open PR already covers the same issue or area.
7. The draft uses the current PR template, a Conventional Commit-style title, verification notes, and AI Assistance disclosure.

Read-only checks are always allowed before PR-shaped work. Use the repository remote/owner from the checkout:

```bash
gh issue view <issue-number> --comments
gh pr list --state open --search "<issue-number> in:body"
gh pr list --state open --search "<area keywords>"
gh api user --jq .login
gh api repos/<owner>/<repo>/issues/<issue-number> --jq '{labels:[.labels[].name], assignees:[.assignees[].login]}'
```

The issue passes the assignment gate only when its labels mark it triaged and its assignees include the authenticated login. Otherwise, draft the PR text or issue comment and stop.

## PR content requirements

A PR must be cohesive, reviewable, and based on `develop`. It must include:

- A linked, triaged issue assigned to the PR author.
- A Conventional Commit-style title such as `fix: ...`, `feat: ...`, `docs: ...`, `test: ...`, `refactor: ...`, `perf: ...`, `style: ...`, `chore: ...`, `ci: ...`, or `revert: ...`; scopes such as `fix(server): ...` are acceptable.
- A description of the user-facing problem and the implementation approach.
- A verification section listing the exact checks run and any checks skipped with residual risk.
- An AI Assistance section when AI tools created or substantially modified code, tests, docs, issues, or comments.
- Documentation updates when behavior, public APIs, configuration syntax, examples, installation, provider requirements, or optional dependencies change.
- Tests when behavior changes.

## DCO, commits, and authorship

- Public contributions must satisfy the Developer Certificate of Origin through GPG-signed commits or a `Signed-off-by:` line in commit messages.
- Do not add AI tools or agents as commit co-authors.
- The human submitter must understand, verify, and be able to explain every submitted change.
- Do not prefix titles or commits with agent markers.

## Refactors and scope control

- Opportunistic refactoring is acceptable only when small, local, and clearly in service of an assigned change.
- Standalone refactors, broad renames, module reshuffles, architecture changes, or sweeping cleanups require a maintainer-approved proposal and assignment before implementation.
- If work is exploratory, draft an issue comment that includes the branch name and relevant files instead of opening a premature PR.

## Safety and privacy

Never commit or paste:

- API keys, credentials, private endpoints, proprietary prompts, provider secrets, or sensitive request/response logs.
- Raw provider logs unless sanitized and required by maintainers.
- Fabricated test results, benchmark results, citations, approvals, compatibility claims, or CI outcomes.
- Generated media, large generated assets, or synthetic datasets without clear provenance and maintainer alignment.

## Changelog and release notes

- Do not edit `CHANGELOG.md` or `CHANGELOG-Colang.md` manually.
- Put release-note context in the issue or PR draft text for maintainers to use in generated release workflows.

## Review readiness

Before requesting maintainer review or drafting a ready-for-review statement:

- Run appropriate validation from [test-and-validation](test-and-validation.md) and report exact commands.
- Address every CodeRabbit, Greptile, and human review comment, or reply with a clear reason why no change is needed.
- Wait for automated-review resolution confirmation when the tool provides it.
- Do not resolve human reviewer conversations unless you opened them or the reviewer explicitly asks you to resolve them.
- Do not self-apply or request a ready-for-maintainer-review label while unresolved author action remains.
- If reviewing a branch, compare against the merge base with `develop`; inspect tests as well as implementation; include a security pass for auth, input handling, deserialization, external calls, secret handling, and telemetry/tracing behavior.
