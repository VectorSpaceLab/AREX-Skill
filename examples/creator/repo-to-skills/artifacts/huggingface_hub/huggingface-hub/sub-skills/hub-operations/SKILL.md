---
name: hub-operations
description: "Operate Hugging Face Hub repositories and API resources with authenticated or mocked Python workflows, explicit revision control, safe mutations, and actionable error recovery."
license: Apache-2.0
disable-model-invocation: true
metadata:
  disco-role: operating
---

# Hub Operations

Use this sub-skill for Python workflows that discover or mutate Hub API
resources: repositories, files and commits, refs, collections, cards,
discussions and pull requests, and webhook registrations. It is grounded in
`huggingface_hub` 1.29.0.

## Trigger And Route

This is the routing surface, not a full API manual. Select the smallest
linked reference that covers the request, then keep the operation and
verification boundaries visible.

| Request signal | Route | Read next |
|---|---|---|
| create/inspect/search a repo, list files/tree/commits, or manage refs | repository and discovery | [API reference](references/api-reference.md) |
| upload/copy/delete files, create a commit or PR, or pin a parent SHA | files and commits | [Workflows](references/workflows.md) |
| cards, metadata, collections, discussions, or PR review | collaboration and metadata | [API reference](references/api-reference.md) and [Workflows](references/workflows.md) |
| webhook registration, scope, enable/disable, or deletion | webhook resources | [Workflows](references/workflows.md) |
| token precedence, access, 401/403/404/409/412/429, or ambiguous mutation | authentication and recovery | [Troubleshooting](references/troubleshooting.md) |
| deterministic unit-style behavior without Hub access | mocked HfApi case | [Mocked recovery case](references/workflows.md#13-exercise-a-private-dataset-conflict-with-a-mocked-hfapi) |

Use this route when the request includes one or more of:

- create, list, inspect, update, delete, move, or duplicate a model, dataset,
  or Space repository;
- upload, delete, or server-side copy repository files; create a commit or PR;
- inspect a revision or manage branches and tags;
- search models, datasets, or Spaces and interpret returned info objects;
- create or curate collections and repository cards;
- read or manage discussions, PRs, and their events;
- create, inspect, enable, disable, update, or delete webhook resources;
- configure or diagnose authentication needed upstream of these operations;
- identify and recover from Hub API errors, including stale-parent conflicts.

Route elsewhere when the primary task is:

- download/cache behavior, `HfFileSystem`, or buckets: sibling
  `downloads-and-storage` route;
- hosted inference or Inference Endpoints: sibling `inference-and-endpoints`
  route;
- exact `hf` command syntax, output modes, or shell automation: sibling
  `cli-and-automation` route;
- Jobs, sandboxes, Space runtime/hardware, or a deployed webhook server:
  sibling `hosted-compute-and-integrations` route.

Webhook registration is owned here; receiving payloads in a server is not.
Space repository metadata is owned here; running or scaling the Space is not.

## Operating Contract

1. **Classify the operation.** Label every step `READ-ONLY`, `MUTATION`, or
   `DESTRUCTIVE`. Do not hide a mutation inside an inspection step.
2. **Resolve identity.** Record `repo_id`, `repo_type`, `revision`, endpoint,
   and token source before calling the API. Prefer explicit
   `namespace/name`; Python uses singular repo types: `model`, `dataset`,
   `space`.
3. **Authenticate safely.** Prefer `HF_TOKEN` or a previously saved login.
   Never hardcode, log, print, serialize, or include a token in an exception
   report. Use a write-scoped token only for mutations.
4. **Inspect before mutation.** Fetch the target object and revision, confirm
   ownership/type/visibility, capture the current SHA when concurrency matters,
   and preview local paths or remote resources affected.
5. **Use explicit mutation intent.** Set a meaningful `commit_message`; pass
   `repo_type`; choose `revision`; use `create_pr=True` when review is safer;
   use `parent_commit` for optimistic concurrency.
6. **Verify the result.** Assert returned IDs/types and inspect the resulting
   revision. For PR commits, verify `CommitInfo.pr_revision` and inspect that
   ref rather than assuming `main` changed.
7. **Guard destructive actions.** Require an exact target display, a dry-run
   plan, and explicit confirmation immediately before delete, merge, move, or
   visibility reduction. Re-inspect after confirmation if the workflow waited.
8. **Recover narrowly.** Branch on typed exceptions and HTTP status. Retry
   only operations shown to be safe, bounded, and still valid after re-read.

### Safety confirmations

Deletion, move, visibility reduction, branch/tag deletion, collection or
webhook deletion, irreversible comment hiding, and PR merge require a
read-only plan, a dry-run gate, exact target confirmation, an immediate SHA or
state recheck, one mutation, and a post-check. `--yes` or `APPLY=1` is only a
mechanism; non-interactive use must receive approval from an upstream reviewed
control. See [the guarded workflow](references/workflows.md#12-explicit-dry-run-and-check-before-delete-pattern).

## Core Concepts

- `repo_id` is normally `namespace/name`. A bare name can use the authenticated
  namespace for creation, but explicit IDs are safer in automation.
- `repo_type=None` means a model for most APIs. Always pass `dataset` or
  `space`; never pass plural forms to Python methods.
- A revision can be a branch, tag, commit OID, or PR ref such as `refs/pr/3`.
  Mutating methods normally default to `main`; verify the method-specific
  constraints before combining `revision` and `create_pr`.
- `exist_ok=True` makes repository, branch, or tag creation tolerant of an
  existing target. It does not prove that the existing resource has the
  requested visibility or settings. Collections spell this `exists_ok`.
- `visibility` accepts `public` or `private`, plus `protected` for Spaces.
  Do not pass both `private` and `visibility`.
- `parent_commit` is a full or short commit OID used as an optimistic
  concurrency check. On conflict, fetch the new head and re-evaluate; do not
  blindly drop the check.
- `create_pr=True` places a proposed commit on a PR ref. `CommitInfo` exposes
  `pr_url`, `pr_num`, and `pr_revision`; `main` is unchanged until merge.
- `commit_message` is the commit summary. Keep it specific and never place
  credentials, signed URLs, or private payload content in it.
- API listings are iterables and returned info fields are often optional.
  Limit iteration and test for `None`; an `info` query usually contains more
  detail than a list query.

## Choose The Client Surface

Use `HfApi(...)` when several calls should share an endpoint, token,
user-agent, or headers. Root-level helpers such as `create_repo`,
`upload_file`, and `list_models` expose the same public operations and are
convenient for isolated calls. Keep one configured client through a workflow
so endpoint and credentials cannot drift.

Read [API reference](references/api-reference.md) before writing calls or
interpreting `RepoUrl`, info, collection, discussion, webhook, or commit
objects. It contains signatures verified from the installed 1.29.0 package.

Read [workflows](references/workflows.md) when implementing create → inspect →
upload → revision/PR flows, discovery, refs, cards, collections, discussions,
webhook resources, or a check-before-delete plan. Examples explicitly mark
read-only and mutation boundaries.

Read [troubleshooting](references/troubleshooting.md) when credentials,
identity, access, revisions, concurrency, upload patterns, rate limits,
network failures, or destructive safeguards are involved. Follow its typed,
bounded recovery rules instead of broad retries.

## Output Expectations

Return or record, without secrets:

- resolved endpoint, `repo_id`, `repo_type`, and requested revision;
- mutation classification and whether confirmation occurred;
- observed starting SHA and resulting SHA or PR ref when applicable;
- concise fields from returned objects, not raw object dumps containing
  secrets (notably webhook resources);
- verification observations: resource exists, expected path/ref/card/event is
  present, or resource is absent after an approved deletion;
- typed error, HTTP status, request ID, recovery attempted, and any remaining
  ambiguity.

Stop rather than guess when target ownership, repo type, destructive intent,
credential scope, or post-conflict content validity cannot be established.
