---
name: "deployment"
description: "Guides AppAgent's task-execution phase that uses generated docs to
  operate an Android app."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Deployment

Use this sub-skill when the task is to run AppAgent against an app that already has documentation.

## What this sub-skill covers
- Choosing the documentation base for an app.
- Running a task with or without docs.
- Understanding the grid-overlay action path.
- Interpreting deployment logs and output folders.

## When to route here
- The user wants AppAgent to complete a phone task now.
- The user is asking how AppAgent selects between auto docs and demo docs.
- The user wants to know where deployment logs or screenshots are written.
- The user needs help when the deployment loop reports no docs or malformed model output.

## Read first
- `references/workflows.md` for the task-execution flow and output layout.
- `references/troubleshooting.md` for no-doc, no-device, parser, and grid issues.
- `../../references/configuration.md` when the model backend or output directories need adjustment.
- `../../references/api-reference.md` when you need parser, controller, or utility details.

## Bundled script
Use the launcher in this sub-skill instead of reconstructing the source launch sequence yourself:
- `scripts/start_deployment.py`

It invokes the deployment loop with explicit argument handling, no shell-string construction, and takes `--repo-root <AppAgent checkout>` when you are not already inside the repository.

## Typical workflow
1. Validate the environment with `../../scripts/check_setup.py --repo-root <AppAgent checkout>` if the host/device status is uncertain.
2. Confirm that the app already has `auto_docs/` or `demo_docs/` output.
3. Run the bundled deployment launcher with the target app and a writable `root_dir`.
4. Answer the prompts for docs base and task description.
5. Inspect the task log and any screenshots in `tasks/task_<app>_<timestamp>/`.

## What to keep in mind
- Deployment still needs a live device and adb.
- If both doc bases exist, AppAgent asks which one to use.
- If no docs exist, you must choose whether to proceed without docs.
- The grid overlay is a fallback for unlabeled UI regions.
- The precise grid-swipe path has a known bug in the source repo.

## Common failure signals
- No docs found for the app.
- More than one docs base exists and the user has not chosen one.
- Invalid device size or adb failure.
- Parser failure in the model response.
- Grid overlay action misfires or swipes the wrong area.

## Useful outputs
- `tasks/task_<app>_<timestamp>/log_<app>_*.txt`
- labeled screenshots and XML captures under the same task directory

## Cross-links
- Use `../exploration/SKILL.md` if the app needs a docs base first.
- Use `../../references/troubleshooting.md` for issues that affect both phases.
