# Hub Operations Troubleshooting

Use this reference after recording the operation class, endpoint, `repo_id`,
`repo_type`, revision, and token source. Never include token contents in a bug
report. Preserve the exception class, HTTP status, request ID, and a redacted
server message.

## Fast Triage

| Symptom | Likely causes | First safe check | Recovery |
|---|---|---|---|
| no local token / auth-required error | `HF_TOKEN` absent, no saved login, or `token=False` | call `whoami` using the intended token source | provide `HF_TOKEN` or login; do not begin mutation |
| 401 “invalid user token” | invalid/expired token; `HF_TOKEN` overrides a valid saved token | identify whether env, explicit, or stored token is effective | rotate/re-enter the token; clear an unintended env override |
| 403 | read token used for write, missing org role, gated/private denial, or policy restriction | `whoami(cache=True)` plus read-only target inspection | use least-privileged token with required role or request access |
| `RepositoryNotFoundError` | wrong ID/type, nonexistent repo, or inaccessible private repo | verify explicit `namespace/name`, singular type, endpoint, and auth | correct identity or obtain access; do not enumerate types blindly |
| `GatedRepoError` | repo exists but access approval is missing | inspect the known repo page/access policy outside automation | request/await access; token alone does not bypass gating |
| `RevisionNotFoundError` | wrong branch, tag, OID, or PR ref | `list_repo_refs(..., include_pull_requests=True)` | select an existing ref; do not fall back to `main` silently |
| stale-parent error (usually 412; mocks/proxies may use 409) | branch changed after inspection | fetch current info SHA and compare with recorded parent | revalidate proposed content, then retry once with new parent or stop |
| generic 409 | existing repo/ref/item or another conflict | inspect resource and server message | use `exist_ok`/`exists_ok` only for the matching idempotent case |
| upload contains too much/too little | wrong local root, `path_in_repo`, `.gitignore`, allow/ignore pattern | print local selection and remote path plan without applying | fix the plan; test with a small file/folder first |
| rate limit / 429 | unbounded listing, repeated `whoami`, aggressive polling | inspect `Retry-After` and call count | cache identity, bound results, wait, then retry safe reads |
| timeout/connection failure | offline mode, DNS/proxy/TLS, service issue | perform a bounded read-only info call | fix network; resolve ambiguous mutation outcome before retry |
| card push fails before upload | invalid YAML/frontmatter or remote validation failure | save locally, parse `card.data`, call `validate` separately | repair metadata; do not skip validation blindly |

## Inspect Errors Without Leaking Credentials

```python
from huggingface_hub.errors import HfHubHTTPError

try:
    # One Hub call here.
    ...
except HfHubHTTPError as error:
    diagnostic = {
        "exception": type(error).__name__,
        "status": error.response.status_code,
        "request_id": error.request_id,
        "server_message": error.server_message,
        "method": error.request.method,
        "url": str(error.request.url),  # Hub auth uses headers, not URL query tokens
    }
    print(diagnostic)
    raise
```

Do not dump request headers, environment variables, the complete client
instance, a webhook object containing `secret`, or locals. If a custom URL can
contain signed query parameters, redact its query before printing.

## Missing, Invalid, Or Wrong-Scope Credentials

### Establish the effective source

Credential precedence can make a valid saved login appear broken:

1. an explicit method/client token is used when passed;
2. `HF_TOKEN` overrides the token saved by login;
3. otherwise the saved token is used;
4. `token=False` deliberately disables authentication.

Safe probe:

```python
# READ-ONLY
import os
from huggingface_hub import HfApi
from huggingface_hub.errors import LocalTokenNotFoundError

if "HF_TOKEN" not in os.environ:
    raise LocalTokenNotFoundError("HF_TOKEN is required for this controlled workflow")

api = HfApi(token=os.environ["HF_TOKEN"])
me = api.whoami(cache=True)
print({
    "name": me["name"],
    "type": me["type"],
    "role": ((me.get("auth") or {}).get("accessToken") or {}).get("role"),
})
```

Expected observation: identity and role only. A read role is not enough for
repo creation, upload, settings changes, collection mutation, discussion
mutation, or webhook mutation.

For an invalid environment token, replace/unset `HF_TOKEN`; switching saved
tokens has no effect while the environment variable still overrides them.
`logout()` removes local saved state but cannot unset an environment variable.
Never “test” a token by echoing it.

### 401, 403, and hidden private resources

A missing or inaccessible private repo can intentionally look like a not-found
response. Do not conclude that a repo is absent from one unauthenticated 401/404
or from `repo_exists(..., token=False)`. Retry with the intended authorized
identity only when access is expected.

For 403:

- confirm the token role and organization membership;
- confirm the operation needs write/admin rather than read;
- check gated approval separately;
- do not create a replacement repo under a different namespace as an automatic
  workaround.

## Wrong Repository Type, ID, Endpoint, Or Revision

### Normalize identity

```python
repo_id = "namespace/name"
repo_type = "dataset"  # exactly model | dataset | space
revision = "main"
assert repo_id.count("/") == 1
assert repo_type in {"model", "dataset", "space"}
```

Python methods take singular types. `repo_type=None` defaults to a model in
most repository APIs. Keep URL prefixes out of `repo_id`.

`RepositoryNotFoundError` covers several cases: invalid ID, wrong type,
nonexistent repository, and inaccessible private repository. Correct using
known identity evidence; do not probe every type/namespace in a way that leaks
private resource existence.

### Diagnose a revision

```python
# READ-ONLY
refs = api.list_repo_refs(
    repo_id,
    repo_type=repo_type,
    include_pull_requests=True,
)
known = {
    "branches": {ref.name: ref.target_commit for ref in refs.branches},
    "tags": {ref.name: ref.target_commit for ref in refs.tags},
    "prs": {ref.ref: ref.target_commit for ref in (refs.pull_requests or [])},
}
print(known)
```

Use the exact PR ref (`refs/pr/N`), not the discussion URL or bare PR number.
A commit OID used as the base of `create_pr=True` can fail because PRs target a
branch; choose the intended branch and keep the OID as `parent_commit` when
optimistic concurrency is required.

Do not silently fall back from a missing tag/commit to `main`. That changes the
meaning of a reproducible operation.

## Private And Gated Access

- Private visibility controls who can see the repository. The right token and
  account/org permissions are required.
- Gating adds an access-approval policy. `GatedRepoError` is a subclass of
  `RepositoryNotFoundError`; catch it first when giving specific guidance.
- A write token cannot override missing gated approval.
- `visibility="protected"` is only valid for Spaces. `private` and `visibility`
  cannot be passed together.
- `exist_ok=True` on `create_repo` can return an existing resource without
  changing its visibility. Always inspect `info.private` afterward.

Example ordering:

```python
from huggingface_hub.errors import GatedRepoError, RepositoryNotFoundError

try:
    info = api.repo_info(repo_id, repo_type=repo_type, revision=revision)
except GatedRepoError:
    raise RuntimeError("Known gated resource requires approved access")
except RepositoryNotFoundError:
    raise RuntimeError("Check repo_id, repo_type, endpoint, private access, and existence")
```

## Parent Commit Conflicts And Concurrent Updates

`parent_commit` prevents a mutation from being based on an unexpectedly changed
branch. In 1.29.0 native integration behavior, a stale parent is commonly HTTP
412 with a “branch was updated” message. Local mocks/proxies may model the same
condition as 409. Do not classify status alone.

Recovery contract:

1. Capture `info.sha` immediately before preparing the mutation.
2. Pass it as `parent_commit`.
3. On a typed error, require status 409/412 **and** a parent/head/branch-conflict
   message.
4. If the response outcome could be ambiguous, inspect open PRs and the target
   path before retrying.
5. Fetch the new target-branch SHA.
6. Compare relevant remote files/metadata and revalidate the local proposal.
7. If concurrent changes overlap or invalidate assumptions, stop.
8. Otherwise retry exactly once with the new SHA, retaining `create_pr=True`
   when review is appropriate.
9. Verify returned `CommitInfo` and inspect its revision.

Never recover by removing `parent_commit`, retrying indefinitely, or treating
all 409 responses as concurrency errors. See the complete code in
[workflows](workflows.md#4-recover-from-a-stale-parent-without-blind-overwrite).

For large `upload_folder` operations split into multiple commits,
`parent_commit` applies only to the first commit. Verify the final returned
revision and paths after completion.

## Upload Paths, Patterns, And Commit Mistakes

### Local versus remote path

- `path_or_fileobj`/`folder_path` is local input.
- `path_in_repo` is a relative POSIX-like path in the repository.
- Leading `./` or `/` can be normalized for commit operations, but use clean
  relative paths. `.`/`..` and paths entering `.git/` or
  `.cache/huggingface/` are invalid/forbidden.
- For deletion operations, a trailing `/` denotes a folder when `is_folder` is
  not explicit. Verify file versus folder before committing.

Uploading data files such as Parquet to a model repository emits a warning.
Treat it as a likely wrong `repo_type`, not noise.

### Folder selection

- Only the root `.gitignore` is considered. A root file in the pending upload
  takes precedence; otherwise the remote root `.gitignore` can apply.
- Nested `.gitignore` files do not define separate rules.
- Any `.git/` directory is excluded.
- `allow_patterns` narrows the set; `ignore_patterns` removes matches. If both
  are present, both constraints apply.
- Patterns are glob-style and match repository-relative local paths. Start with
  a tiny fixture containing one include, one exclude, and one nested file.
- `delete_patterns` removes matching remote files in the same commit. With
  `path_in_repo`, matching is relative to that remote subfolder.
- `.gitattributes` is protected from `delete_patterns`.

Before apply, print local root, remote root, selected count/preview, and all
delete patterns. After apply, use `list_repo_files` on `CommitInfo.oid` or
`pr_revision` and assert exact expected paths.

### Resuming uploads

With the default Xet path, folder uploads are streamed, deduplicated, and can
usually resume by rerunning. Important PR exception:

- rerunning with `create_pr=True` opens another PR;
- resume an existing PR with `revision="refs/pr/N"` and without
  `create_pr=True`.

A `Future` returned by `run_as_future=True` defers errors until
`future.result()`. Do not report success merely because a future was queued.

## Rate Limits, Network Failures, And Ambiguous Outcomes

### Rate limits

For HTTP 429:

- read `Retry-After` when present;
- cache `whoami(cache=True)` rather than calling it repeatedly;
- set list limits and avoid tight polling loops;
- use bounded delay and retry only safe reads or mutations whose outcome was
  proven absent;
- preserve request IDs for support/diagnostics.

### Network and offline failures

Check:

- `HF_HUB_OFFLINE`; an online API operation cannot run in offline mode;
- endpoint spelling and expected custom Hub endpoint;
- proxy, DNS, TLS certificates, and firewall;
- whether a public read-only `repo_info` call can complete;
- service status when local networking is healthy.

A timeout after sending a mutation has an ambiguous outcome. Before retrying:

- creation: inspect whether the exact repo now exists and matches expected type;
- upload/commit: inspect target branch/PR refs, commits, and expected paths;
- collection/discussion/webhook mutation: fetch the resource and compare its
  state;
- delete/move/merge: inspect both pre- and post-state; never repeat blindly.

Only `exist_ok`/`exists_ok` for the documented create-existing case makes a
retry tolerant; it does not verify all requested attributes.

## Cards And Metadata

Common failures:

- malformed or non-dictionary YAML frontmatter;
- invalid Hub metadata values during `card.validate()`;
- template use without the optional Jinja dependency;
- `ModelCardData.eval_results` without `model_name`;
- overwriting an existing metadata key while `overwrite=False`;
- trying to synthesize a missing Space README with `metadata_update`.

Recovery:

1. load/save the card locally;
2. inspect `card.data.to_dict()`, `card.text`, and generated `card.content`;
3. call `validate(repo_type=...)` as a separate read-only network check;
4. preserve existing metadata unless overwrite is reviewed;
5. propose with `create_pr=True` and verify `pr_revision`.

Do not set `ignore_metadata_errors=True` merely to get past malformed metadata;
it can lose information. Use it only for deliberate recovery with a documented
review of what was dropped.

## Collections, Discussions, And Webhooks

### Collections

- `list_collections` truncates each collection to at most four items; use
  `get_collection` before mutation.
- Collection methods spell idempotency `exists_ok`, not `exist_ok`.
- Duplicate item insertion returns 409 unless `exists_ok=True`.
- Item update/delete requires `CollectionItem.item_object_id`, not `item_id`.
- Collection deletion is non-revertible.

### Discussions and pull requests

- `discussion_num` must be a positive integer.
- `create_pull_request` creates an empty draft PR; use a commit/upload with
  `create_pr=True` to propose file changes.
- Event objects have type-specific fields; branch on `event.type` or concrete
  class.
- Before merge, inspect `is_pull_request`, status, diff, target branch, and
  `conflicting_files`. Merge only after explicit confirmation.
- Hiding a comment is irreversible; do not use it as a reversible moderation
  action.

### Webhooks

- `create_webhook` requires exactly one of URL or Job ID.
- Validate watched types and keep scope as narrow as possible.
- Do not print `WebhookInfo` wholesale because `secret` may be present.
- Store the webhook signing secret in `WEBHOOK_SECRET` or another secret store,
  not source or shell history.
- Disable first when diagnosis needs a reversible stop; delete only after exact
  confirmation.
- Receiving payloads requires optional Pydantic/server dependencies and belongs
  to the `hosted-compute-and-integrations` sibling route.

## Destructive-Action Safeguards

Treat repository/collection/webhook deletion, repo move, branch/tag deletion,
PR merge, irreversible comment hiding, and visibility changes as guarded
operations.

Required pattern:

1. **Read-only plan:** display exact resource ID/type, SHA/version, visibility,
   important children/refs, and action.
2. **Dry-run default:** `APPLY` is absent or `0`; exit without mutation.
3. **Exact confirmation:** require a phrase containing action, type, ID, and
   inspected SHA/version when available.
4. **Immediate recheck:** fetch state again; stop if it changed.
5. **One mutation:** use `missing_ok=False` unless repeated absence is explicitly
   the desired contract.
6. **Post-check:** verify absence, destination identity, merged status, or new
   visibility.
7. **Audit output:** record identifiers and observations, never secrets.

Use the copyable repository deletion example in
[workflows](workflows.md#12-explicit-dry-run-and-check-before-delete-pattern).
If an interactive confirmation is impossible, require a separate upstream
approval artifact/control. A command-line `--yes` or `APPLY=1` is not approval
by itself.
