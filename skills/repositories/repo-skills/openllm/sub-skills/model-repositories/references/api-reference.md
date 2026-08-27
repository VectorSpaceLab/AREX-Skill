# Model Repository API Reference

## When to read

Read this when you need the verified helper signatures or return-shape details behind OpenLLM's model repository commands.

## Verified signatures

```python
parse_repo_url(repo_url: str, repo_name: str | None = None) -> RepoInfo
list_repo(repo_name: str | None = None) -> list[RepoInfo]
list_bento(tag: str | None = None, repo_name: str | None = None, include_alias: bool = False) -> list[BentoInfo]
ensure_bento(model: str, target: DeploymentTarget | None = None, repo_name: str | None = None) -> BentoInfo
```

## Important data fields

### `RepoInfo`

- `name`
- `path`
- `url`
- `server`
- `owner`
- `repo`
- `branch`

### `BentoInfo`

- `repo`
- `path`
- `alias`
- `tag` property: `name:version`, or `name:alias` when an alias is present.
- `bentoml_tag` property: `name:version`.
- `labels`, `envs`, `pretty_yaml`, and `pretty_gpu` read Bento metadata from `bento.yaml`.

## Behavioral notes

- `list_bento` respects repository aliases and can strip duplicate aliases unless `include_alias=True`.
- `ensure_bento` prints an error and exits when no model is found.
- When a single Bento matches, OpenLLM returns it directly and may warn if the target machine is under-provisioned.
- `parse_repo_url` normalizes both HTTP(S) and SSH Git URL forms and defaults the branch to `main`.
