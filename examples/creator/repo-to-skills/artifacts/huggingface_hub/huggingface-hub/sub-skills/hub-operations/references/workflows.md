# Hub Operations Workflows

Use these recipes as operating patterns, not as a requirement to run every
step. Each section labels read-only and mutating boundaries. Replace placeholder
IDs through environment variables; never paste a real token into source,
command arguments, logs, or commit messages.

## 1. Establish A Safe Client

### Supply a process-scoped token

```bash
# LOCAL AUTH SETUP — reads a token without echoing it and exports only to this shell.
read -rsp "HF token: " HF_TOKEN && export HF_TOKEN && printf '\n'
```

For persistent interactive login, `hf auth login` or `login()` writes local
credential state. For automation, prefer the process-scoped `HF_TOKEN` pattern.
A read token is sufficient for public/private inspection; mutations need the
corresponding write permission.

```python
# READ-ONLY
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ["HF_TOKEN"])
identity = api.whoami(cache=True)
print({"name": identity["name"], "type": identity["type"]})
```

Expected observation: a username and account type, with no token value in
stdout. If this fails, stop before mutation and use the authentication section
of [troubleshooting](troubleshooting.md).

A custom/private Hub endpoint is explicit:

```python
# READ-ONLY CLIENT CONFIGURATION
api = HfApi(
    endpoint=os.environ.get("HF_ENDPOINT", "https://huggingface.co"),
    token=os.environ["HF_TOKEN"],
    user_agent={"workflow": "hub-operations"},
)
```

Keep this client for every subsequent call so endpoint and token do not drift.

## 2. Discover And Inspect Resources

### Bounded search

```python
# READ-ONLY
from itertools import islice

models = api.list_models(
    search="sentence embedding",
    filter=["sentence-transformers"],
    sort="downloads",
    limit=5,
)
for item in models:
    print({
        "id": item.id,
        "sha": item.sha,
        "private": item.private,
        "gated": item.gated,
        "pipeline_tag": item.pipeline_tag,
    })

# islice is useful when the called list method has no limit in your wrapper.
spaces = list(islice(api.search_spaces("visualize embeddings"), 5))
print([space.id for space in spaces])
```

Expected observation: at most five objects. Treat every non-ID field as
optional. `list_datasets` and `list_spaces` follow the same bounded-iterator
pattern.

### Resolve type and revision before mutation

```bash
export REPO_ID='namespace/repository'
export REPO_TYPE='dataset'  # model | dataset | space
export REVISION='main'
```

```python
# READ-ONLY
import os

repo_id = os.environ["REPO_ID"]
repo_type = os.environ["REPO_TYPE"]
revision = os.environ.get("REVISION", "main")
assert repo_type in {"model", "dataset", "space"}

info = api.repo_info(repo_id, repo_type=repo_type, revision=revision)
refs = api.list_repo_refs(repo_id, repo_type=repo_type, include_pull_requests=True)
files = api.list_repo_files(repo_id, repo_type=repo_type, revision=revision)

print({
    "id": info.id,
    "type": repo_type,
    "resolved_sha": info.sha,
    "private": info.private,
    "gated": info.gated,
    "file_count": len(files),
    "branches": [ref.name for ref in refs.branches],
    "tags": [ref.name for ref in refs.tags],
    "pull_requests": [ref.name for ref in (refs.pull_requests or [])],
})
```

Expected observations:

- `info.id` equals the intended `repo_id`;
- `info.sha` is the commit selected by `revision`;
- the expected branch/tag/PR appears in the matching ref list;
- private/gated state is understood before choosing credentials or mutation.

Do not infer a dataset or Space from a 404 using the model default. Retry only
after correcting `repo_type` from known identity evidence.

## 3. Create → Inspect → Upload → Verify A PR Revision

This complete flow intentionally creates a private dataset and proposes a file
through a PR. It does not merge or delete anything.

```bash
export REPO_ID='your-namespace/operations-example'
```

```python
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ["HF_TOKEN"])
repo_id = os.environ["REPO_ID"]
repo_type = "dataset"

# MUTATION: create, idempotent only with respect to existence.
repo_url = api.create_repo(
    repo_id=repo_id,
    repo_type=repo_type,
    visibility="private",
    exist_ok=True,
)
assert repo_url.repo_id == repo_id
assert repo_url.repo_type == repo_type

# READ-ONLY: verify an existing repo also satisfies the requested state.
base = api.dataset_info(repo_id, revision="main")
assert base.id == repo_id
assert base.private is True, "exist_ok does not change an existing repo's visibility"
assert isinstance(base.sha, str) and base.sha
print({"repo_id": base.id, "base_sha": base.sha, "private": base.private})

# MUTATION: create a proposed commit, guarded by the inspected parent.
commit = api.upload_file(
    repo_id=repo_id,
    repo_type=repo_type,
    path_or_fileobj=b"row_id,value\n1,example\n",
    path_in_repo="data/sample.csv",
    commit_message="Add a small sample dataset",
    create_pr=True,
    parent_commit=base.sha,
)
assert commit.repo_url.repo_id == repo_id
assert commit.pr_revision and commit.pr_revision.startswith("refs/pr/")
assert commit.pr_num is not None

# READ-ONLY: main should not be assumed changed; inspect the returned PR ref.
proposed = api.dataset_info(repo_id, revision=commit.pr_revision)
paths = api.list_repo_files(
    repo_id,
    repo_type=repo_type,
    revision=commit.pr_revision,
)
assert proposed.sha == commit.oid
assert "data/sample.csv" in paths
print({
    "commit_oid": commit.oid,
    "pr_num": commit.pr_num,
    "pr_revision": commit.pr_revision,
    "verified_path": "data/sample.csv",
})
```

Expected observation: `CommitInfo.pr_revision` is a `refs/pr/N` value, the file
exists on that revision, and no assertion claims it exists on `main`.

For `upload_folder(create_pr=True)`, omit a non-default `revision`. If a folder
upload was interrupted after a PR was opened, resume the same PR with
`revision="refs/pr/N"` and without `create_pr=True`; otherwise a new PR is
opened.

## 4. Recover From A Stale Parent Without Blind Overwrite

The current Hub may report a stale branch parent as HTTP 412; a local mock,
proxy, or other compatible service may report 409. Handle either only when the
message and operation establish a parent/head conflict. A generic 409 can mean
an existing repo, ref, or collection item and must not enter this path.

```python
# MUTATION WITH BOUNDED RECOVERY
import os
from itertools import islice

from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

api = HfApi(token=os.environ["HF_TOKEN"])
repo_id = os.environ["REPO_ID"]
repo_type = "dataset"
path_in_repo = "data/sample.csv"
payload = b"row_id,value\n1,revalidated\n"
commit_message = "Update the reviewed sample"

base = api.dataset_info(repo_id, revision="main")
expected_parent = base.sha
assert expected_parent


def propose(parent_sha: str):
    return api.upload_file(
        repo_id=repo_id,
        repo_type=repo_type,
        path_or_fileobj=payload,
        path_in_repo=path_in_repo,
        commit_message=commit_message,
        create_pr=True,
        parent_commit=parent_sha,
    )


try:
    result = propose(expected_parent)
except HfHubHTTPError as error:
    status = error.response.status_code
    message = str(error).lower()
    parent_conflict = status in {409, 412} and any(
        marker in message for marker in ("parent", "branch was updated", "conflict")
    )
    if not parent_conflict:
        raise

    # READ-ONLY: avoid duplicate PRs if outcome was ambiguous.
    existing = None
    for discussion in islice(
        api.get_repo_discussions(
            repo_id,
            repo_type=repo_type,
            discussion_type="pull_request",
            discussion_status="open",
        ),
        50,
    ):
        details = api.get_discussion_details(
            repo_id,
            discussion.num,
            repo_type=repo_type,
        )
        if path_in_repo in (details.diff or ""):
            existing = details
            break

    if existing is not None:
        result_revision = existing.git_reference
        assert result_revision
        assert path_in_repo in api.list_repo_files(
            repo_id, repo_type=repo_type, revision=result_revision
        )
        print({"reused_existing_pr": existing.num, "revision": result_revision})
    else:
        # READ-ONLY: fetch the new head and revalidate assumptions.
        latest = api.dataset_info(repo_id, revision="main")
        assert latest.sha and latest.sha != expected_parent
        assert payload.startswith(b"row_id,value\n")  # replace with domain checks
        print({"old_parent": expected_parent, "new_parent": latest.sha})

        # MUTATION: exactly one retry, retaining optimistic concurrency and PR review.
        result = propose(latest.sha)
        assert result.pr_revision
        assert path_in_repo in api.list_repo_files(
            repo_id, repo_type=repo_type, revision=result.pr_revision
        )
        print({"retried_once": True, "pr_revision": result.pr_revision})
```

Replace the sample payload assertion with checks that establish the proposed
content is still valid against the new base. If the concurrent change touches
the same path or alters an invariant, stop for human resolution. Never recover
by silently removing `parent_commit`.

## 5. Preview Folder Mapping Before Upload

There is no universal no-network dry-run for `upload_folder`. Build a local
plan, inspect remote targets, then make the mutation a separate step. Treat
`delete_patterns` as destructive.

```bash
export LOCAL_FOLDER='./prepared-data'
export PATH_IN_REPO='data'
export APPLY='0'  # change to exactly 1 only after reviewing the plan
```

```python
import fnmatch
import os
from pathlib import Path

repo_id = os.environ["REPO_ID"]
repo_type = os.environ["REPO_TYPE"]
local_root = Path(os.environ["LOCAL_FOLDER"])
remote_root = os.environ.get("PATH_IN_REPO", "").strip("/")
apply = os.environ.get("APPLY") == "1"
allow = ["**/*.jsonl", "*.jsonl"]
ignore = ["**/temporary/**", "**/*.bak"]
delete_patterns: list[str] = []  # populate only with separately approved paths

assert local_root.is_dir()
local_files = [
    path.relative_to(local_root).as_posix()
    for path in local_root.rglob("*")
    if path.is_file() and ".git" not in path.relative_to(local_root).parts
]
selected = [
    path for path in local_files
    if any(fnmatch.fnmatch(path, pat) for pat in allow)
    and not any(fnmatch.fnmatch(path, pat) for pat in ignore)
]
remote_before = api.list_repo_files(repo_id, repo_type=repo_type, revision="main")

print({
    "dry_run": not apply,
    "local_root": str(local_root),
    "path_in_repo": remote_root or ".",
    "selected_count": len(selected),
    "selected_preview": selected[:20],
    "remote_file_count_before": len(remote_before),
    "delete_patterns": delete_patterns,
})

if not apply:
    raise SystemExit("Dry run only. Review output, then set APPLY=1 deliberately.")

# MUTATION
result = api.upload_folder(
    repo_id=repo_id,
    repo_type=repo_type,
    folder_path=local_root,
    path_in_repo=remote_root,
    allow_patterns=allow,
    ignore_patterns=ignore,
    delete_patterns=delete_patterns or None,
    commit_message="Upload reviewed dataset files",
    parent_commit=api.repo_info(repo_id, repo_type=repo_type).sha,
)
print({"commit_oid": result.oid, "commit_url": result.commit_url})
```

Expected dry-run observation: local root, remote root, selected count/preview,
remote count, and deletion patterns are visible; no commit is made while
`APPLY=0`. The local `fnmatch` preview is conservative planning, not proof of
the library's exact filter result. After applying, inspect the resulting
revision and exact paths.

Root `.gitignore`, allow/ignore patterns, and remote delete patterns can all
affect the final plan. Nested `.git/` directories are excluded. Keep
repository paths relative and never use `..`.

## 6. Create And Verify Branches And Tags

```python
# READ-ONLY
base = api.repo_info(repo_id, repo_type=repo_type, revision="main")
assert base.sha

# MUTATION
api.create_branch(
    repo_id,
    repo_type=repo_type,
    branch="reviewed-change",
    revision=base.sha,
    exist_ok=True,
)
api.create_tag(
    repo_id,
    repo_type=repo_type,
    tag="v0.1.0",
    tag_message="Validated first release",
    revision="reviewed-change",
    exist_ok=True,
)

# READ-ONLY verification
refs = api.list_repo_refs(repo_id, repo_type=repo_type)
branch = next(ref for ref in refs.branches if ref.name == "reviewed-change")
tag = next(ref for ref in refs.tags if ref.name == "v0.1.0")
assert branch.target_commit == base.sha
assert tag.target_commit == base.sha
print({"branch_sha": branch.target_commit, "tag_sha": tag.target_commit})
```

Before deleting a branch or tag, display its target commit, confirm it is not
the only name for required work, and request exact confirmation. A default
protected branch cannot be deleted.

## 7. Move Or Duplicate A Repository

Use duplication when history should be copied while keeping the source. Use
move when renaming/transferring the original identity.

```python
# READ-ONLY
source = api.repo_info("source-owner/source-name", repo_type="model")
print({"source_id": source.id, "source_sha": source.sha, "private": source.private})

# MUTATION: creates a separate repository with history.
copy_url = api.duplicate_repo(
    "source-owner/source-name",
    "your-namespace/copied-name",
    repo_type="model",
    visibility="private",
    exist_ok=False,
)
assert copy_url.repo_id == "your-namespace/copied-name"
```

For `move_repo(from_id, to_id, ...)`, first inspect references to the old ID,
organization permissions, and destination nonexistence. Require explicit
confirmation because the canonical ID changes. Verify the destination and
update dependent configuration afterward.

## 8. Create, Validate, And Propose A Card

```python
# LOCAL ONLY until validate/push
from pathlib import Path
from huggingface_hub import ModelCard, ModelCardData

card_data = ModelCardData(
    language="en",
    license="apache-2.0",
    library_name="transformers",
    pipeline_tag="text-classification",
    tags=["example"],
)
card = ModelCard.from_template(
    card_data,
    model_id=repo_id,
    model_description="A concise, reviewed description.",
)
card.save(Path("README.preview.md"))
assert card.data.to_dict()["pipeline_tag"] == "text-classification"
print({"preview": "README.preview.md", "metadata": card.data.to_dict()})

# READ-ONLY NETWORK VALIDATION
card.validate(repo_type="model")

# MUTATION: propose README.md on a PR.
base = api.model_info(repo_id, revision="main")
result = card.push_to_hub(
    repo_id,
    token=os.environ["HF_TOKEN"],
    commit_message="Document model usage and metadata",
    create_pr=True,
    parent_commit=base.sha,
)
assert result.pr_revision
print({"pr_revision": result.pr_revision, "commit_oid": result.oid})
```

`DatasetCard`/`DatasetCardData` and `SpaceCard`/`SpaceCardData` use the same
shape. Prefer `metadata_update(..., create_pr=True)` for a small metadata-only
change. Its default `overwrite=False` is a safeguard; do not set
`overwrite=True` until existing values and the proposed diff are reviewed.

## 9. Manage A Collection

```python
from huggingface_hub import HfApi

# MUTATION
collection = api.create_collection(
    "Reviewed resources",
    description="Resources inspected for this project",
    private=True,
    exists_ok=True,
)
assert collection.private is True, "exists_ok does not change an existing collection's privacy"
collection = api.add_collection_item(
    collection.slug,
    item_id=repo_id,
    item_type=repo_type,
    note="Inspected at the recorded revision",
    exists_ok=True,
)

# READ-ONLY verification: get_collection returns the complete item list.
collection = api.get_collection(collection.slug)
item = next(
    item for item in collection.items
    if item.item_id == repo_id and item.item_type == repo_type
)
print({
    "slug": collection.slug,
    "private": collection.private,
    "item_object_id": item.item_object_id,
    "item_id": item.item_id,
})
```

Use `item.item_object_id` to update or delete the collection entry. Do not use
`item.item_id` for that mutation. Collection deletion is irreversible and must
follow the confirmation pattern below.

## 10. Inspect And Operate Discussions Or PRs

```python
# READ-ONLY
from itertools import islice

items = list(islice(api.get_repo_discussions(
    repo_id,
    repo_type=repo_type,
    discussion_status="open",
), 50))
print([
    {"num": item.num, "title": item.title, "is_pr": item.is_pull_request}
    for item in items
])

if items:
    details = api.get_discussion_details(
        repo_id,
        items[0].num,
        repo_type=repo_type,
    )
    print({
        "num": details.num,
        "status": details.status,
        "event_types": [event.type for event in details.events],
        "conflicting_files": details.conflicting_files,
        "target_branch": details.target_branch,
    })
```

For a discussion-only mutation:

```python
# MUTATION
created = api.create_discussion(
    repo_id,
    "Question about the documented workflow",
    description="Please review the proposed behavior.",
    repo_type=repo_type,
)
assert created.is_pull_request is False
```

For file changes, prefer an upload/commit with `create_pr=True` over an empty
draft PR. Before `merge_pull_request`, fetch details, require
`is_pull_request`, open/draft status as intended, no unresolved
`conflicting_files`, inspect `diff`, and ask for exact confirmation.

## 11. Manage Webhook Registrations Without Leaking Secrets

```bash
read -rsp "Webhook signing secret: " WEBHOOK_SECRET \
  && export WEBHOOK_SECRET && printf '\n'
export WEBHOOK_URL='https://example.invalid/hugging-face-events'
```

```python
import os

# MUTATION
webhook = api.create_webhook(
    url=os.environ["WEBHOOK_URL"],
    watched=[{"type": "dataset", "name": repo_id}],
    domains=["repo", "discussion"],
    secret=os.environ["WEBHOOK_SECRET"],
)

# SAFE OUTPUT: do not print the WebhookInfo object or its secret.
print({
    "id": webhook.id,
    "watched": [(item.type, item.name) for item in webhook.watched],
    "domains": webhook.domains,
    "disabled": webhook.disabled,
})

# MUTATION, reversible
webhook = api.disable_webhook(webhook.id)
assert webhook.disabled is True
webhook = api.enable_webhook(webhook.id)
assert webhook.disabled is False
```

Create a webhook with exactly one destination: `url=...` or `job_id=...`.
Review watched scope and domains before update. Treat secret rotation as a
sensitive mutation. Webhook deletion is permanent and uses the guarded pattern.
Implementing a payload receiver or triggering hosted Jobs belongs to the
`hosted-compute-and-integrations` sibling.

## 12. Explicit Dry-Run And Check-Before-Delete Pattern

The Python delete methods do not provide a universal server-side dry run. Use a
separate inspection process and require both `APPLY=1` and a typed target. This
example deletes a repository only after displaying its exact state.

```bash
export REPO_ID='your-namespace/repository-to-delete'
export REPO_TYPE='dataset'
export APPLY='0'
python delete_guard.py
# Review the plan. Only then, in a controlled shell:
# export APPLY='1'; python delete_guard.py
```

```python
# delete_guard.py
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ["HF_TOKEN"])
repo_id = os.environ["REPO_ID"]
repo_type = os.environ["REPO_TYPE"]
apply = os.environ.get("APPLY") == "1"
assert repo_type in {"model", "dataset", "space"}

# READ-ONLY plan
info = api.repo_info(repo_id, repo_type=repo_type, revision="main")
refs = api.list_repo_refs(repo_id, repo_type=repo_type)
files = api.list_repo_files(repo_id, repo_type=repo_type, revision="main")
plan = {
    "action": "PERMANENTLY DELETE REPOSITORY",
    "repo_id": info.id,
    "repo_type": repo_type,
    "head_sha": info.sha,
    "private": info.private,
    "branches": [ref.name for ref in refs.branches],
    "tags": [ref.name for ref in refs.tags],
    "file_count": len(files),
    "file_preview": files[:20],
    "dry_run": not apply,
}
print(plan)
assert info.id == repo_id

if not apply:
    raise SystemExit("Dry run only: no deletion performed.")

expected = f"delete {repo_type} {repo_id} at {info.sha}"
confirmation = input(f"Type exactly '{expected}' to continue: ")
if confirmation != expected:
    raise SystemExit("Confirmation mismatch: no deletion performed.")

# READ-ONLY recheck immediately before destruction.
latest = api.repo_info(repo_id, repo_type=repo_type, revision="main")
if latest.sha != info.sha:
    raise SystemExit("Head changed after review: no deletion performed.")

# DESTRUCTIVE
api.delete_repo(repo_id, repo_type=repo_type, missing_ok=False)

# READ-ONLY expected observation
exists = api.repo_exists(repo_id, repo_type=repo_type)
assert exists is False
print({"deleted": repo_id, "repo_type": repo_type, "verified_absent": True})
```

Expected observations:

1. With `APPLY=0`, the exact type/ID/SHA, refs, and file preview are printed and
   the process exits without mutation.
2. With `APPLY=1`, any confirmation mismatch or changed head stops deletion.
3. Only after exact confirmation does deletion run; the final existence check
   reports `False`.

Adapt the same two-gate pattern to collection deletion, webhook deletion, tag
or branch deletion, PR merge, repo move, and public/private visibility changes.
For non-interactive automation, approval must be supplied by an upstream
reviewed control; do not silently replace typed confirmation with an always-on
flag.

## 13. Exercise A Private Dataset Conflict With A Mocked HfApi

This deterministic case exercises the difficult path without contacting the
Hub. It models an existing private dataset, inspects `main`, attempts a PR
upload with the inspected parent, receives a synthetic **409 stale-parent**
response, checks for an already-created open PR, fetches the new head, and
retries exactly once. The fake token is held only in the mock call; the safe
result and diagnostic never print it. A real implementation should use a
secret manager or `HF_TOKEN`, not the placeholder below.

```python
# MOCKED / NO NETWORK
import os
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
from huggingface_hub import CommitInfo, HfApi, RepoUrl
from huggingface_hub.errors import HfHubHTTPError

repo_id = "acme/private-eval"
repo_type = "dataset"
path_in_repo = "data/sample.csv"
token = os.environ.get("HF_TOKEN", "token-held-in-memory")

api = Mock(spec=HfApi)
api.create_repo.return_value = RepoUrl(
    "https://hub.example/datasets/acme/private-eval", endpoint="https://hub.example"
)
base = SimpleNamespace(id=repo_id, sha="a" * 40, private=True, gated=False)
latest = SimpleNamespace(id=repo_id, sha="b" * 40, private=True, gated=False)
proposed = SimpleNamespace(id=repo_id, sha="c" * 40, private=True, gated=False)
api.dataset_info.side_effect = [base, latest, proposed]
api.list_repo_files.return_value = [".gitattributes", path_in_repo]
api.get_repo_discussions.return_value = iter([])

stale_response = httpx.Response(
    409,
    request=httpx.Request("POST", "https://hub.example/api/datasets/acme/private-eval/commit"),
    headers={"X-Request-Id": "synthetic-stale-parent"},
    json={"error": "branch was updated; parent commit is stale"},
)
stale_error = HfHubHTTPError(
    "parent commit is stale: branch was updated",
    response=stale_response,
    server_message="branch was updated",
)
commit = CommitInfo(
    commit_url="https://hub.example/datasets/acme/private-eval/commit/" + ("c" * 40),
    commit_message="Add reviewed sample",
    commit_description="",
    oid="c" * 40,
    pr_url="https://hub.example/datasets/acme/private-eval/discussions/7",
    _endpoint="https://hub.example",
)
api.upload_file.side_effect = [stale_error, commit]

# MUTATION: creation is mocked; verify requested visibility because exist_ok
# does not change an already-existing repository.
created = api.create_repo(
    repo_id=repo_id,
    repo_type=repo_type,
    visibility="private",
    exist_ok=True,
    token=token,
)
assert created.repo_id == repo_id and created.repo_type == repo_type

# READ-ONLY: inspect the exact revision before proposing a change.
inspected = api.dataset_info(repo_id, repo_type=repo_type, revision="main", token=token)
assert inspected.private is True and inspected.sha == "a" * 40

payload = b"row_id,value\n1,revalidated\n"

def propose(parent_sha: str):
    return api.upload_file(
        repo_id=repo_id,
        repo_type=repo_type,
        path_or_fileobj=payload,
        path_in_repo=path_in_repo,
        commit_message="Add reviewed sample",
        create_pr=True,
        parent_commit=parent_sha,
        token=token,
    )

try:
    result = propose(inspected.sha)
except HfHubHTTPError as error:
    status = error.response.status_code
    parent_conflict = status in {409, 412} and any(
        marker in str(error).lower()
        for marker in ("parent", "branch was updated", "stale", "conflict")
    )
    assert parent_conflict, "A generic 409 must not be retried as a stale parent."

    # READ-ONLY: the first request could have opened a PR before failing to
    # return. Reuse it if the mocked discussion diff already contains the path.
    existing = None
    for discussion in api.get_repo_discussions(
        repo_id,
        repo_type=repo_type,
        discussion_type="pull_request",
        discussion_status="open",
        token=token,
    ):
        details = api.get_discussion_details(repo_id, discussion.num, repo_type=repo_type, token=token)
        if path_in_repo in (details.diff or ""):
            existing = details
            break
    assert existing is None

    # READ-ONLY: re-read and validate the proposal against the new head.
    refreshed = api.dataset_info(repo_id, repo_type=repo_type, revision="main", token=token)
    assert refreshed.sha == "b" * 40 and refreshed.private is True
    assert payload.startswith(b"row_id,value\n")

    # MUTATION: the only retry keeps the parent guard and PR intent.
    result = propose(refreshed.sha)

assert result.pr_revision == "refs/pr/7"
verified = api.dataset_info(repo_id, repo_type=repo_type, revision=result.pr_revision, token=token)
assert verified.sha == "c" * 40
assert path_in_repo in api.list_repo_files(
    repo_id, repo_type=repo_type, revision=result.pr_revision, token=token
)
assert api.upload_file.call_count == 2
parents = [call.kwargs["parent_commit"] for call in api.upload_file.call_args_list]
assert parents == ["a" * 40, "b" * 40]
assert all(call.kwargs["create_pr"] is True for call in api.upload_file.call_args_list)

safe_result = {
    "repo_id": repo_id,
    "repo_type": repo_type,
    "requested_visibility": "private",
    "starting_revision": "main",
    "old_parent": "a" * 40,
    "new_parent": "b" * 40,
    "pr_revision": result.pr_revision,
    "retried_once": True,
    "request_id": stale_error.request_id,
}
rendered = repr(safe_result)
assert token not in rendered
print(safe_result)
```

The fixture is deliberately synthetic and does not contact the Hub. The
important assertions are: `repo_type="dataset"`, `private=True`, explicit
revision and parent SHAs, `create_pr=True` on both attempts, exactly one retry,
PR-ref verification, and no token in output. If the open-PR scan finds a
matching path, reuse and verify that PR instead of calling `propose` again.
