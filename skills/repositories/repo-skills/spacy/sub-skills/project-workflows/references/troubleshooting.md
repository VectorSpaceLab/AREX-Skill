# Troubleshooting project workflows

Use this reference when a project operation fails, reruns unexpectedly, or looks unsafe.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Clone fails or sparse checkout errors appear | The repo path or branch is wrong, or the local Git version does not support sparse checkout. | Retry with a known-good repo, drop `--sparse`, or upgrade Git before using sparse clone again. |
| Clone hangs or fails on a private repo | The repo is reachable only with credentials or network access that are not present. | Confirm access outside spaCy first, then rerun the clone. Do not use clone as a validation step. |
| Asset download starts when you did not expect it | The asset has a `url` or `git` block, so it is a real download or sparse checkout. | Move the file to a private/local asset pattern or keep the asset out of the default run. |
| An extra asset is missing | The asset is marked `extra: true`, so it is skipped by the default asset pass. | Re-run `project assets --extra` only when you intentionally need the opt-in asset. |
| Asset download fails with network or permission errors | The asset source needs network access, a working remote URL, or the right credentials. | Validate the source URL or Git repo first, then configure credentials or use a local copy. |
| Project commands rerun every time | `deps` and `outputs` are missing, unstable, or written outside the project tree; `no_skip` may also be set. | Declare stable relative paths for deps and outputs, and use `no_skip` only for commands that should always rerun. |
| A command is skipped when it should run | The command has no recorded change in deps or outputs, or an expected upstream step never created its output. | Add the missing dependency or output, then rerun the upstream command manually or use `--force`. |
| `project run` reports missing deps or outputs | The command expects files that are not present locally. | Run the prerequisite command yourself; `project run` does not automatically rebuild earlier steps. |
| Requirements mismatch warnings appear | The installed environment and the project requirements file drifted apart. | Align the environment with the project requirements, or disable the check only if the mismatch is intentional. |
| `project document` overwrote an existing README | The file had no existing auto-generated block for spaCy to preserve. | Regenerate into a fresh output file, or restore the generated markers before rerunning. |
| `push` or `pull` fails with auth or protocol errors | The remote needs credentials, a missing protocol dependency, or a path that does not exist. | Configure the provider outside spaCy, then retry against a known-good remote. |
| `pull` brings back a stale result | The command hash or dependency hash changed, so the remote version you want is not the one at the plain output path. | Re-check the command and inputs, then pull the matching version instead of assuming a single file path. |
| `push` appears to create duplicate remote versions | That is expected: remote storage keeps versions keyed by command and dependency hashes. | Treat remote history as append-only and clean up obsolete versions separately. |
| `project dvc` fails | DVC is not installed, not initialized, or the workflow choice is incompatible with DVC's one-pipeline expectation. | Install and initialize DVC first, then generate DVC config for one workflow only. |
| `project run --dry` still seems unsafe | Dry-run skips execution, but the script itself may still be destructive when run for real. | Use dry-run only to inspect the plan; treat the actual command as side-effecting until you are sure otherwise. |

## Quick recovery order

1. Run the local project validator.
2. Inspect `project.yml` and confirm `deps`, `outputs`, and workflow names.
3. Use `project document` or `project run --dry` before any real execution.
4. Fetch only the assets you actually need.
5. Retry remote or DVC commands only after credentials, protocols, and initialization are confirmed.

## When to stop and hand off

- If the problem is a training config, reroute to `training-and-cli`.
- If the problem is a custom pipeline component inside a project script, reroute to `pipeline-components`.
- If the problem requires network access that you do not have, stop after the local validator and dry-run checks.
