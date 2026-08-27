# CLI reference for ModelScope Hub workflows

This reference covers the `modelscope` and `ms` console scripts and the Hub-oriented commands owned by this sub-skill. Evidence came from the package metadata, command documentation, CLI shim, clear-cache compatibility class, and CLI tests. The runtime guidance below is self-contained; future agents do not need the original repository checkout.

## Entry points and delegation

- Distribution script names: `modelscope` and `ms` both dispatch to the same command runner.
- In current ModelScope, the local `modelscope.cli.cli` module is a thin compatibility shim that delegates command registration and execution to `modelscope_hub.cli.main.run_cmd`.
- If `modelscope` imports but `modelscope --help` fails with `ModuleNotFoundError: No module named 'modelscope_hub'`, install or repair the Hub dependency (`modelscope-hub>=0.2.0` is the declared Hub requirement).
- Top-level command families observed for the current package include Hub commands (`download`, `upload`, `cache`, `scan-cache`, `clear-cache`, `login`), package/plugin commands (`pipeline`, `server`, `plugins`/`plugin`, `llamafile`), content commands (`modelcard`, legacy `model`), and auxiliary commands (`skills`, `studio`, `mcp`). Use this sub-skill for command selection and Hub mechanics; route deployment, model inference, dataset loading, and development details to sibling sub-skills.

Always run `modelscope <command> --help` or `ms <command> --help` in the target environment before executing a command that changes remote or local state, because plugin-provided commands may vary with installed `modelscope_hub` and extras.

## Safe command categories

| Command | Typical purpose | Side effect level | Notes |
| --- | --- | --- | --- |
| `modelscope --help`, `ms --help` | Discover command families. | Safe read-only. | Verifies the console script and `modelscope_hub` import. |
| `modelscope download ...` | Download a model/dataset repo or files. | Network and local writes unless cache-only/offline. | Supports repo id positional style and legacy `--model`/`--dataset` style in tests/docs. |
| `modelscope cache scan` / `modelscope scan-cache` | Inspect cache. | Read-only. | `scan-cache --dir /fake/cache/path` should report zero repos rather than fail. |
| `modelscope cache clear` / `modelscope clear-cache` | Delete cached repos or all cache. | Destructive local delete. | Get explicit approval; legacy `clear-cache` prompts interactively. |
| `modelscope cache verify` | Verify cache integrity/metadata where supported by the installed CLI. | Read-only or local metadata checks. | Use help output for exact flags. |
| `modelscope upload ...` | Upload files/folders to Hub repositories. | Remote mutation and network. | Requires a token with repository permission. Prefer a dry-run plan first when available. |
| `modelscope login --token ...` | Persist credentials. | Writes credentials. | Avoid literal tokens in shell history when possible. |
| `modelscope modelcard ...` / legacy `model` | Create/upload/download model card or model metadata. | May mutate remote repo. | Deep model-card content authoring is not covered here. |
| `modelscope skills ...` | Manage ModelScope skill packaging/operations. | Varies by subcommand. | Use only for high-level routing here. |
| `modelscope studio ...` | Studio/Space-like repository operations. | Remote/local side effects. | Route deployment details to `../../serving-export-and-tools/SKILL.md`. |
| `modelscope mcp ...` | MCP-related Hub tooling. | Varies by subcommand. | Inspect help and credentials before use. |

## Download command patterns

The current installed facts for `download --help` include a positional `repo_id` plus options `--repo-type`, `--revision`, `--cache-dir`, `--local-dir`, `--include`, `--exclude`, and `--force`. Older documentation and CLI tests also show legacy forms with `--model`, `--dataset`, `--cache_dir`, and `--local_dir`. Prefer the hyphenated, positional form when help shows it; use legacy flags only when the target environment's help exposes them.

### Whole model repo to reusable cache

```bash
modelscope download Qwen/Qwen3-0.6B --repo-type model --revision master
```

Equivalent legacy style if supported:

```bash
modelscope download --model Qwen/Qwen3-0.6B --revision master
```

### Selected files by explicit path

```bash
modelscope download Qwen/Qwen3-0.6B README.md tokenizer.json --repo-type model --revision master
```

Explicit file paths are interpreted as relative repository paths. When files are present, include/exclude glob filters may be ignored by the CLI/API layer, so do not combine explicit files with pattern filters unless the command help explicitly says how they interact.

### Selected files by glob pattern

```bash
modelscope download Qwen/Qwen3-0.6B \
  --repo-type model \
  --include '*.json' 'tokenizer*' \
  --exclude 'onnx/*' '*.bin'
```

Quote globs so the local shell does not expand them before the CLI receives them.

### Dataset snapshot

```bash
modelscope download damo/some_dataset --repo-type dataset --revision master
```

Equivalent legacy style if supported:

```bash
modelscope download --dataset damo/some_dataset --revision master
```

After the snapshot is local, route dataset loading or `MsDataset.load` questions to `../../datasets-config/SKILL.md`.

### Local visible copy instead of cache-managed path

```bash
modelscope download Qwen/Qwen3-0.6B \
  --repo-type model \
  --local-dir ./vendor/modelscope/Qwen3-0.6B \
  --include '*.json' 'tokenizer*'
```

Use `--local-dir` when the user wants a stable, project-visible folder. If both `local_dir` and `cache_dir` are provided, local-dir semantics take precedence for the returned/visible files; avoid specifying both unless you have a specific reason and have checked the installed help.

### Custom cache root for reuse

```bash
MODELSCOPE_CACHE=/mnt/modelscope-cache \
modelscope download Qwen/Qwen3-0.6B --repo-type model --revision master
```

or:

```bash
modelscope download Qwen/Qwen3-0.6B \
  --repo-type model \
  --cache-dir /mnt/modelscope-cache \
  --revision master
```

Use one cache root consistently across CLI, Python, and serving processes. Mixed cache roots are the most common reason a file appears to be downloaded but later cannot be found.

### Force refresh

```bash
modelscope download Qwen/Qwen3-0.6B --repo-type model --revision master --force
```

Use `--force` only when the user accepts a network refresh and possible overwrite of local cached content. It is not an offline troubleshooting step.

## Cache commands

The current installed facts say `cache` owns `scan`, `clear`, and `verify`, while legacy top-level `scan-cache` and `clear-cache` remain available or aliased in compatibility paths.

### Scan the default cache

```bash
modelscope cache scan
# or, on older/compat CLIs:
modelscope scan-cache
```

### Scan a chosen cache root

```bash
modelscope cache scan --dir /mnt/modelscope-cache
# or:
modelscope scan-cache --dir /mnt/modelscope-cache
```

A non-existent scan directory should be reported as zero repositories, not treated as proof that your requested model is absent from another cache root.

### Clear cache safely

Prefer targeted clears over deleting the entire cache:

```bash
modelscope cache clear --repo-type model Qwen/Qwen3-0.6B
```

If the target environment exposes only the legacy command, it supports mutually exclusive `--model` and `--dataset` flags and prompts for confirmation:

```bash
modelscope clear-cache --model Qwen/Qwen3-0.6B
modelscope clear-cache --dataset damo/some_dataset
```

If neither a model nor dataset id is provided to legacy `clear-cache`, it targets the entire ModelScope cache. Do not run that form without explicit user approval.

## Upload command and API selection

Use `modelscope upload --help` for exact CLI flags in the target environment. For scripted uploads, prefer Python `HubApi.upload_file` or `HubApi.upload_folder` because the signatures make repo type, path-in-repo, and commit message explicit:

```python
from modelscope.hub.api import HubApi

api = HubApi(token=os.environ['MODELSCOPE_API_TOKEN'])
api.upload_file(
    repo_id='owner/name',
    repo_type='model',
    path_or_fileobj='local-file.bin',
    path_in_repo='weights/local-file.bin',
    commit_message='Add local-file.bin',
)
```

Uploads mutate remote repositories and require a token with write permission. Confirm repository id, repo type, destination path, overwrite behavior, and commit message before execution.

## Authentication and endpoint commands

- `modelscope login --token TOKEN` persists credentials; treat it as a credential write.
- Prefer avoiding tokens directly in command lines because shell history and process listings may expose them. Use environment variables in shell wrappers or Python `token=` parameters where possible.
- Use explicit `--endpoint` or Python `endpoint=` only when the user intentionally targets a non-default domain. If an endpoint is passed without a scheme in Python utility resolution, ModelScope helper logic can add `https://`; CLI behavior is controlled by the installed `modelscope_hub` CLI.

## Dry-run planner

This sub-skill bundles `scripts/plan_download.py`, which validates common repo-id mistakes and prints a shell command plus Python snippet without network calls:

```bash
python scripts/plan_download.py Qwen/Qwen3-0.6B \
  --repo-type model \
  --include '*.json' 'tokenizer*' \
  --local-dir ./vendor/qwen-config
```

Use the planner output as a starting point; still check `modelscope download --help` when running in an environment with unknown `modelscope_hub` version.
