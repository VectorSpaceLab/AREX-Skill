# `project.yml` reference

This file describes the project file structure and the local checks used by the validator helper.

## Top-level keys

| Key | Type | Required? | Purpose | Validation notes |
| --- | --- | --- | --- | --- |
| `title` | string | Optional | Human-readable project title used in generated docs and help text. | Keep short and descriptive. |
| `description` | string | Optional | Longer project summary used in generated docs. | Can be a single paragraph. |
| `vars` | mapping | Optional | Reusable variables for paths, URLs, and script interpolation. | Values may be nested mappings. |
| `env` | mapping | Optional | Maps project variables to environment variable names. | Use for command-time interpolation only. |
| `directories` | list of strings | Optional | Directories that should always exist in the project. | Use relative paths. |
| `assets` | list of asset objects | Optional | Files or directories to download or copy into the project. | Networked assets should be explicit. |
| `commands` | list of command objects | Required for execution | Named commands that can run independently or inside workflows. | Command names must be unique. |
| `workflows` | mapping of workflow name to command list | Optional | Ordered command sequences. | Every referenced command must exist. |
| `remotes` | mapping | Optional | Named storage locations for `push` and `pull`. | Values may be local paths or remote URLs. |
| `spacy_version` | version specifier string | Optional | Compatibility gate for the installed spaCy version. | The installed version must satisfy the specifier. |
| `check_requirements` | boolean | Optional | Controls the runtime requirements check used by `project run`. | Defaults to `true` when omitted. |

## Command object

| Key | Type | Required? | Purpose | Validation notes |
| --- | --- | --- | --- | --- |
| `name` | string | Yes | Command identifier used by `project run` and workflows. | Must be unique within `commands`. |
| `help` | string | Optional | Short description shown in command help and generated docs. | Keep it concise. |
| `script` | list of strings | Yes | Steps that run in order. | Each entry should be a command string. |
| `deps` | list of strings | Optional | Files the command needs to read. | Use relative paths where possible. |
| `outputs` | list of strings | Optional | Files or directories the command creates. | Use relative paths where possible. |
| `outputs_no_cache` | list of strings | Optional | Outputs that should not be cached by DVC. | Useful for DVC-oriented projects. |
| `no_skip` | boolean | Optional | Forces the command to run every time. | Best for tests and checks. |

Notes:
- Commands without outputs are never skipped.
- `project run` uses the declared deps and outputs to decide whether to rerun a command.
- `project run` does not automatically infer upstream dependencies.
- Command scripts are meant to be explicit; if you need environment variables, route them through `env`.

## Asset object

| Key | Type | Required? | Purpose | Validation notes |
| --- | --- | --- | --- | --- |
| `dest` | string | Yes | Destination path inside the project. | Must be relative to the project. |
| `url` | string | Optional | Remote or local source path for a download or copy. | If the string has a URI scheme, treat it as networked. |
| `git` | mapping | Optional | Git-backed asset source with sparse checkout. | Must include at least `repo` and `path`. |
| `checksum` | string | Optional | Expected checksum for the asset. | Used for repeatable fetches and mismatch checks. |
| `extra` | boolean | Optional | Marks the asset as opt-in for `project assets --extra`. | Default is `false`. |
| `description` | string | Optional | Human-readable asset description. | Helps generated docs. |

Git-backed asset notes:
- `repo` is the repository URL.
- `branch` defaults to `master` if omitted.
- `path` is the file or directory inside the remote repo.
- An empty `path` means the repo root.
- Git-backed assets still require network access and repo permissions.

Private asset notes:
- If an asset has a `dest` but no `url` and no `git` block, the file must already exist locally.
- A checksum is useful for private assets because it confirms the expected file once the file is in place.

## Workflow value

| Key | Type | Required? | Purpose | Validation notes |
| --- | --- | --- | --- | --- |
| workflow name | string | Yes | Name used by `project run` and `project dvc`. | Must not shadow a command name. |
| workflow steps | list of strings | Yes | Ordered list of command names. | Every step must match an existing command. |

## Remote value

| Key | Type | Required? | Purpose | Validation notes |
| --- | --- | --- | --- | --- |
| remote name | string | Yes | Alias used by `project push` and `project pull`. | Keep names short and stable. |
| remote target | string | Yes | Storage path or URL. | Networked remotes may need credentials or extra protocol support. |

## Requirements checks

- When `check_requirements` is enabled, `project run` compares the installed environment with the project requirements file when one is present.
- A mismatch is a warning that the environment and project are drifting apart.
- If the mismatch is intentional, set `check_requirements: false` in the project file and document the reason.
- The validator helper also checks the installed spaCy version against `spacy_version`, if present.

## Path rules used by the validator

- `dest`, `deps`, `outputs`, and `directories` should be relative paths.
- Absolute paths are a warning or error because they make projects harder to reuse.
- Paths with `..` segments are risky because they escape the project tree.
- Local `url` values are checked only for existence; network URLs are not fetched.

## Minimal example

```yaml
title: Demo project
description: Small local workflow demo
commands:
  - name: preprocess
    help: Prepare local inputs
    script:
      - "python -m spacy info --silent"
    deps:
      - assets/input.spacy
    outputs:
      - corpus/output.spacy
workflows:
  all:
    - preprocess
remotes:
  default: ./remote-cache
```
