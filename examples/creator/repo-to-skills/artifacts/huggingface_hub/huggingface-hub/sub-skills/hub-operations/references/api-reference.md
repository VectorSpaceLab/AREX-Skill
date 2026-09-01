# Hub Operations API Reference

Read this reference before implementing Python calls or interpreting API
results. Signatures below were inspected from `huggingface_hub` 1.29.0. They
show the public call contract, not every supported method or returned field.
Root-level helpers and methods on `HfApi` expose the same operations.

## Client And Authentication

```text
HfApi(
    endpoint: str | None = None,
    token: str | bool | None = None,
    library_name: str | None = None,
    library_version: str | None = None,
    user_agent: dict | str | None = None,
    headers: dict[str, str] | None = None,
) -> None
```

Token meanings on most methods:

- `None`: use the client token, then the normal local/environment resolution.
- a string: use that token without persisting it.
- `False`: deliberately send no token; useful to verify public access.
- `True`: require the locally resolved token where supported.

`HF_TOKEN` takes precedence over a saved login. Do not pass a literal token in
source. `HfApi(token=os.environ["HF_TOKEN"])` is suitable when explicit
per-process authentication is required.

Representative auth signatures:

```text
login(token: str | None = None, *, add_to_git_credential: bool = False,
      skip_if_logged_in: bool = True) -> None
logout(token_name: str | None = None) -> None
whoami(token: bool | str | None = None, *, cache: bool = False) -> dict
auth_switch(token_name: str, add_to_git_credential: bool = False) -> None
auth_list() -> None
```

`login` persists a token; an `HfApi(token=...)` client does not. Use
`whoami(cache=True)` when repeated identity checks are needed because that
endpoint has a strict rate limit. `whoami` requires authentication and rejects
`token=False`; use an HfApi-shaped mock or a patched session for anonymous
unit tests. Never print the returned credential inputs.

## Repository Identity

Python APIs use these primary repository types:

| `repo_type` | Meaning | URL namespace | Typical info method |
|---|---|---|---|
| `None` or `"model"` | model repository | root | `model_info` |
| `"dataset"` | dataset repository | `/datasets/` | `dataset_info` |
| `"space"` | Space repository | `/spaces/` | `space_info` |

Use singular values. Keep `repo_id="namespace/name"` separate from
`repo_type`; do not put `datasets/` or `spaces/` into `repo_id`. The package
also exposes limited `kernel` read/ref operations; this route does not make
kernel publishing a supported workflow.

A revision may identify a branch (`main`), tag (`v1.0`), commit OID, or PR ref
(`refs/pr/7`). Reads accept all of these where documented. A mutation normally
starts from a branch; method-specific PR constraints are listed below. A
missing revision must raise or be reported as `RevisionNotFoundError`; never
silently substitute `main`.

## Required Core Signatures

### Create a repository

```text
create_repo(
    repo_id: str,
    *,
    token: str | bool | None = None,
    private: bool | None = None,
    visibility: RepoVisibility_T | None = None,
    repo_type: str | None = None,
    exist_ok: bool = False,
    resource_group_id: str | None = None,
    region: REPO_REGIONS | None = None,
    space_sdk: str | None = None,
    space_hardware: SpaceHardware | None = None,
    space_storage: SpaceStorage | None = None,
    space_sleep_time: int | None = None,
    space_secrets: list[dict[str, str]] | None = None,
    space_variables: list[dict[str, str]] | None = None,
    space_volumes: list[Volume] | None = None,
    space_template: str | None = None,
) -> RepoUrl
```

Use `visibility` for new code. `private` remains accepted but is mutually
exclusive with `visibility`. `protected` is Space-only. A Space requires a
valid `space_sdk` unless a template supplies it. With `exist_ok=True`, inspect
the returned existing resource: creation-only visibility/settings are not
reapplied.

### Upload one file

```text
upload_file(
    *,
    path_or_fileobj: str | Path | bytes | BinaryIO,
    path_in_repo: str,
    repo_id: str,
    token: str | bool | None = None,
    repo_type: str | None = None,
    revision: str | None = None,
    commit_message: str | None = None,
    commit_description: str | None = None,
    create_pr: bool | None = None,
    parent_commit: str | None = None,
    run_as_future: bool = False,
    _hot_reload: bool | None = None,
) -> CommitInfo | Future[CommitInfo]
```

The repository must already exist. `path_in_repo` is a repository-relative
file path. Supply an explicit commit message in automation. `create_pr=True`
returns PR fields in `CommitInfo`; `parent_commit` makes the mutation
conditional on the expected base.

### Upload a folder

```text
upload_folder(
    *,
    repo_id: str,
    folder_path: str | Path,
    path_in_repo: str | None = None,
    commit_message: str | None = None,
    commit_description: str | None = None,
    token: str | bool | None = None,
    repo_type: str | None = None,
    revision: str | None = None,
    create_pr: bool | None = None,
    parent_commit: str | None = None,
    allow_patterns: list[str] | str | None = None,
    ignore_patterns: list[str] | str | None = None,
    delete_patterns: list[str] | str | None = None,
    run_as_future: bool = False,
) -> CommitInfo | Future[CommitInfo]
```

The local tree is mapped under `path_in_repo` (root when `None`). Allow and
ignore patterns both apply when both are set. `delete_patterns` also mutates
remote state in the same operation and must be previewed. In 1.29.0,
`upload_folder(create_pr=True)` opens against the default branch; do not pair it
with a non-default `revision`. To resume into an existing PR, use
`revision="refs/pr/N"` without `create_pr=True`.

### Create a lower-level commit

```text
create_commit(
    repo_id: str,
    operations: Iterable[CommitOperation],
    *,
    commit_message: str,
    commit_description: str | None = None,
    token: str | bool | None = None,
    repo_type: str | None = None,
    revision: str | None = None,
    create_pr: bool | None = None,
    num_threads: int = 5,
    parent_commit: str | None = None,
    run_as_future: bool = False,
    _hot_reload: bool | None = None,
) -> CommitInfo | Future[CommitInfo]
```

Operations are `CommitOperationAdd`, `CommitOperationDelete`, or
`CommitOperationCopy`. Operation objects are mutated during processing and
must not be reused. An empty `commit_message` is invalid. The installed
implementation documents limits of 25,000 LFS files and a 1 GB regular-file
payload per `create_commit`. A stale `parent_commit` rejects rather than
overwrites concurrent changes; inspect the current head before a bounded
retry.

## Discovery And Metadata

```text
model_info(repo_id: str, *, revision: str | None = None,
           timeout: float | None = None, securityStatus: bool | None = None,
           files_metadata: bool = False, expand: list[str] | None = None,
           token: bool | str | None = None) -> ModelInfo

dataset_info(repo_id: str, *, revision: str | None = None,
             timeout: float | None = None, files_metadata: bool = False,
             expand: list[str] | None = None,
             token: bool | str | None = None) -> DatasetInfo

space_info(repo_id: str, *, revision: str | None = None,
           timeout: float | None = None, files_metadata: bool = False,
           expand: list[str] | None = None,
           token: bool | str | None = None) -> SpaceInfo

repo_info(repo_id: str, *, revision: str | None = None,
          repo_type: str | None = None, timeout: float | None = None,
          files_metadata: bool = False, expand = None,
          token: bool | str | None = None
) -> ModelInfo | DatasetInfo | SpaceInfo | KernelInfo
```

Representative list signatures:

```text
list_models(*, filter=None, author=None, apps=None, gated=None,
            inference=None, inference_provider=None, model_name=None,
            trained_dataset=None, search=None, pipeline_tag=None,
            num_parameters=None, emissions_thresholds=None, sort=None,
            limit: int | None = None, expand=None, full=None,
            cardData: bool = False, fetch_config: bool = False,
            token: bool | str | None = None) -> Iterable[ModelInfo]

list_datasets(*, filter=None, author=None, benchmark=None, dataset_name=None,
              gated=None, language_creators=None, language=None,
              multilinguality=None, size_categories=None,
              task_categories=None, task_ids=None, search=None, sort=None,
              limit: int | None = None, expand=None, full=None,
              token: bool | str | None = None) -> Iterable[DatasetInfo]

list_spaces(*, filter=None, author=None, search=None, datasets=None,
            models=None, linked: bool = False, sort=None,
            limit: int | None = None, expand=None, full=None,
            token: bool | str | None = None) -> Iterable[SpaceInfo]

search_spaces(query: str, *, filter=None, sdk=None,
              include_non_running: bool = False,
              token: bool | str | None = None) -> Iterable[SpaceSearchResult]

list_user_repos(namespace: str | None = None, *,
                token: bool | str | None = None) -> Iterable[RepoStorageInfo]
```

These return lazy iterables. Set `limit` or use `itertools.islice`; do not
materialize an unbounded result. Filter names and available expanded fields can
change with the Hub service, so inspect returned optional fields.
`list_user_repos` lists the authenticated user's or an organization's
repositories with storage information; it is not the public search surface.

Repository inspection helpers:

```text
list_repo_files(repo_id: str, *, revision=None, repo_type=None,
                token=None) -> list[str]
list_repo_tree(repo_id: str, path_in_repo: str | None = None, *,
               recursive: bool = False, expand: bool = False,
               revision=None, repo_type=None, token=None
) -> Iterable[RepoFile | RepoFolder]
get_paths_info(repo_id: str, paths: list[str] | str, *, expand=False,
               revision=None, repo_type=None, token=None
) -> list[RepoFile | RepoFolder]
list_repo_commits(repo_id: str, *, repo_type=None, token=None,
                  revision=None, formatted: bool = False
) -> list[GitCommitInfo]
repo_exists(repo_id: str, *, repo_type=None, token=None) -> bool
revision_exists(repo_id: str, revision: str, *, repo_type=None, token=None) -> bool
file_exists(repo_id: str, filename: str, *, repo_type=None,
            revision=None, token=None) -> bool
```

This route owns API inspection. Download/cache behavior belongs to the
`downloads-and-storage` sibling.

## Lifecycle, Files, Branches, And Tags

Representative lifecycle methods:

```text
delete_repo(repo_id: str, *, token=None, repo_type=None,
            missing_ok: bool = False) -> None
duplicate_repo(from_id: str, to_id: str | None = None, *, repo_type=None,
               private=None, visibility=None, token=None,
               exist_ok: bool = False, ...) -> RepoUrl
move_repo(from_id: str, to_id: str, *, repo_type=None, token=None)
update_repo_settings(repo_id: str, *, gated=None, private=None,
                     visibility=None, token=None, repo_type=None) -> None
copy_files(source: str, destination: str, *, token=None) -> None
delete_file(path_in_repo: str, repo_id: str, *, token=None, repo_type=None,
            revision=None, commit_message=None, commit_description=None,
            create_pr=None, parent_commit=None) -> CommitInfo
delete_files(repo_id: str, delete_patterns: list[str], *, token=None,
             repo_type=None, revision=None, commit_message=None,
             commit_description=None, create_pr=None, parent_commit=None
) -> CommitInfo
delete_folder(path_in_repo: str, repo_id: str, *, token=None, repo_type=None,
              revision=None, commit_message=None, commit_description=None,
              create_pr=None, parent_commit=None) -> CommitInfo
```

`copy_files` uses `hf://` source and destination URIs and copies Hub-hosted
content server-side. A trailing slash on a source folder means “copy its
contents” rather than nest the folder. Storage/bucket transfers belong to the
`downloads-and-storage` sibling.

Refs:

```text
create_branch(repo_id: str, *, branch: str, revision=None, token=None,
              repo_type=None, exist_ok: bool = False) -> None
delete_branch(repo_id: str, *, branch: str, token=None,
              repo_type=None) -> None
create_tag(repo_id: str, *, tag: str, tag_message=None, revision=None,
           token=None, repo_type=None, exist_ok: bool = False) -> None
delete_tag(repo_id: str, *, tag: str, token=None, repo_type=None) -> None
list_repo_refs(repo_id: str, *, repo_type=None,
               include_pull_requests: bool = False, token=None) -> GitRefs
```

`revision` selects the source commit for a new branch or tag. `exist_ok=True`
only suppresses the “already exists” case. Deleting the protected default
branch is expected to fail.

## Collections

```text
get_collection(collection_slug: str, *, token=None) -> Collection
list_collections(*, owner=None, item=None, sort=None, limit=None,
                 token=None) -> Iterable[Collection]
create_collection(title: str, *, namespace=None, description=None,
                  private: bool = False, resource_group_id=None,
                  exists_ok: bool = False, token=None) -> Collection
update_collection_metadata(collection_slug: str, *, title=None,
                           description=None, position=None, private=None,
                           theme=None, token=None) -> Collection
delete_collection(collection_slug: str, *, missing_ok: bool = False,
                  token=None) -> None
add_collection_item(collection_slug: str, item_id: str, item_type: str, *,
                    note=None, exists_ok: bool = False,
                    token=None) -> Collection
update_collection_item(collection_slug: str, item_object_id: str, *,
                       note=None, position=None, token=None) -> None
delete_collection_item(collection_slug: str, item_object_id: str, *,
                       missing_ok: bool = False, token=None) -> None
```

Collection creation and item insertion use `exists_ok`, with an “s”.
`item_type` may be `model`, `dataset`, `space`, `paper`, `collection`, or
`bucket`; a collection item is identified by the `(item_id, item_type)` pair.
Listing collections includes at most four items per collection; call
`get_collection` for the complete item list. Updating/deleting an item
requires `item_object_id`, not the underlying `repo_id`/paper ID.

## Cards And Repository Metadata

```text
ModelCard.load(repo_id_or_path, repo_type=None, token=None,
               ignore_metadata_errors: bool = False)
ModelCard.from_template(card_data: ModelCardData,
                        template_path=None, template_str=None, **values)
card.save(filepath)
card.validate(repo_type=None)
card.push_to_hub(repo_id: str, token=None, repo_type=None,
                 commit_message=None, commit_description=None,
                 revision=None, create_pr=None, parent_commit=None)

metadata_update(repo_id: str, metadata: dict, *, repo_type=None,
                overwrite: bool = False, token=None, commit_message=None,
                commit_description=None, revision=None,
                create_pr: bool = False, parent_commit=None) -> str
```

The same load/save/validate/push pattern exists for `DatasetCard` and
`SpaceCard`. `card.data` is a `CardData` subclass, `card.text` excludes YAML
frontmatter, and `card.content` includes it. `to_dict()` and `to_yaml()` export
metadata. Validation calls the Hub. `metadata_update` refuses to overwrite an
existing value unless `overwrite=True`; review the diff or use a PR.

## Discussions And Pull Requests

```text
get_repo_discussions(repo_id: str, *, author=None, discussion_type=None,
                     discussion_status=None, repo_type=None,
                     token=None) -> Iterator[Discussion]
get_discussion_details(repo_id: str, discussion_num: int, *,
                       repo_type=None, token=None) -> DiscussionWithDetails
create_discussion(repo_id: str, title: str, *, token=None,
                  description=None, repo_type=None,
                  pull_request: bool = False) -> DiscussionWithDetails
create_pull_request(repo_id: str, title: str, *, token=None,
                    description=None, repo_type=None) -> DiscussionWithDetails
comment_discussion(repo_id: str, discussion_num: int, comment: str, *,
                   token=None, repo_type=None) -> DiscussionComment
edit_discussion_comment(repo_id: str, discussion_num: int, comment_id: str,
                        new_content: str, *, token=None, repo_type=None
) -> DiscussionComment
rename_discussion(repo_id: str, discussion_num: int, new_title: str, *,
                  token=None, repo_type=None) -> DiscussionTitleChange
change_discussion_status(repo_id: str, discussion_num: int,
                         new_status: Literal["open", "closed"], *,
                         token=None, comment=None, repo_type=None
) -> DiscussionStatusChange
merge_pull_request(repo_id: str, discussion_num: int, *, token=None,
                   comment=None, repo_type=None)
```

`create_pull_request` creates an empty draft PR. To propose file changes, use
`upload_file`, `upload_folder`, `create_commit`, card push, or
`metadata_update` with `create_pr=True`. Treat close, hide, and merge as
destructive or irreversible operations requiring confirmation.

## Webhook Resources

```text
list_webhooks(*, token=None) -> list[WebhookInfo]
get_webhook(webhook_id: str, *, token=None) -> WebhookInfo
create_webhook(*, url: str | None = None, job_id: str | None = None,
               watched: list[dict | WebhookWatchedItem], domains=None,
               secret: str | None = None, token=None) -> WebhookInfo
update_webhook(webhook_id: str, *, url=None, watched=None, domains=None,
               secret=None, token=None) -> WebhookInfo
enable_webhook(webhook_id: str, *, token=None) -> WebhookInfo
disable_webhook(webhook_id: str, *, token=None) -> WebhookInfo
delete_webhook(webhook_id: str, *, token=None) -> None
```

Create with exactly one of `url` or `job_id`. Watched item types are `user`,
`org`, `model`, `dataset`, and `space`. The 1.29.0 source type alias spells the
second domain `"discussions"`, while the shipped API examples, service
responses, and unit fixtures use `"discussion"`; use the value accepted by
the target service and verify the returned `domains` rather than guessing from
the annotation. Do not dump `WebhookInfo` because its `secret` field may be
populated. Record only fields such as `id`, `url` host if appropriate,
`watched`, `domains`, and `disabled`.

Webhook payload parsing uses `WebhookPayload` and nested Pydantic objects such
as `event.action`, `repo.id`, `repo.type`, `repo.head_sha`, `discussion`, and
`updatedRefs`. Receiving/serving those payloads is a server integration and
belongs to the `hosted-compute-and-integrations` sibling.

## Practical Result Shapes

Fields are service-dependent and many are optional. Use attributes, not tuple
unpacking or assumptions about raw JSON.

| Object | Practical fields to inspect |
|---|---|
| `RepoUrl` | string URL plus `endpoint`, `namespace`, `repo_name`, `repo_id`, `repo_type`, `url` |
| `ModelInfo` | `id`, `author`, `sha`, `private`, `gated`, `last_modified`, `tags`, `pipeline_tag`, `siblings`, `card_data`; list results may omit many fields |
| `DatasetInfo` | `id`, `author`, `sha`, `private`, `gated`, `last_modified`, `tags`, `siblings`, `card_data`, `downloads`; fields can be `None` |
| `SpaceInfo` | `id`, `author`, `sha`, `private`, `gated`, `sdk`, `host`, `models`, `datasets`, `siblings`, `card_data`; runtime fields are routed elsewhere |
| `Collection` | `slug`, `title`, `owner`, complete-or-truncated `items`, `private`, `description`, `position`, `theme`, `upvotes`, `url` |
| `CollectionItem` | `item_object_id` (collection mutation key), `item_id` (underlying resource), `item_type`, `position`, `note` |
| `CommitInfo` | `commit_url`, `commit_message`, `commit_description`, `oid`, `repo_url`, and optional `pr_url`, `pr_revision`, `pr_num` |
| `Discussion` | `num`, `title`, `status`, `author`, `repo_id`, `repo_type`, `is_pull_request`, `created_at`, computed `git_reference`, `url` |
| `DiscussionWithDetails` | all discussion fields plus `events`, `conflicting_files`, `target_branch`, `merge_commit_oid`, and `diff` |
| discussion events | base `id`, `type`, `created_at`, `author`; comments add `content`/edit state, commits add `summary`/`oid`, status/title changes add new/old values |
| `WebhookInfo` | `id`, exactly one of `url`/`job`, `watched`, `domains`, sensitive `secret`, `disabled` |

`RepoFile` exposes `path`, `size`, `blob_id`, and optional LFS/expanded fields;
`RepoFolder` exposes `path`, `tree_id`, and optional expanded commit data.
`list_repo_tree` and the search/list APIs are lazy iterables, whereas
`list_repo_files`, `get_paths_info`, and `list_repo_commits` return lists.
`get_paths_info` ignores missing paths and supports file paths only.

For mutation verification, assert the specific fields that prove the intended
state. Do not compare full object representations: optional service fields can
change independently.
