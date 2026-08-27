---
name: contribution-and-project-maintenance
description: "Add, fix, review, and triage mini-project folders while keeping
  README, requirements, assets, and repository hygiene aligned with the repo's
  contribution style."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Contribution and Project Maintenance

Use this sub-skill when the task is about adding a new mini-project folder, fixing an existing one, reviewing a PR for repo hygiene, or triaging README, requirements, asset, and cache issues.

## Use when
- A new mini-project folder needs a safe starter scaffold.
- An existing project README needs alignment with the repo template.
- Project-local dependencies, run steps, or asset paths need cleanup.
- A PR should be checked for naming, cache noise, or stale links.

## Do not use when
- The task is to run or debug a GUI, web, network, data, or ML demo.
- The request is mainly about runtime behavior rather than static maintenance.
- The change belongs in a sibling sub-skill that owns execution or backend-specific work.

## Workflow
1. Read `references/contribution-workflow.md` for the add/fix/review checklist and PR expectations.
2. Read `references/project-template.md` to shape `README.md`, file names, and optional `requirements.txt`.
3. Read `references/troubleshooting.md` when the folder has missing files, broken requirements, stale badges, or cache noise.
4. Use `scripts/create_mini_project_skeleton.py --help` before creating a new starter folder.
5. Keep changes inside the target project folder unless the task explicitly calls for repo-root or `.github/` edits.

## Boundaries
- Create or repair `README.md`, `main.py`, and optional `requirements.txt` inside the project folder.
- Use `README.md` exact case for new work; keep legacy case variants only if the task is explicitly preserving them.
- Keep assets local and referenced with relative paths.
- Remove generated caches and notebook checkpoints from review changes.
- Avoid touching the root `requirements.txt` as a shared dependency list.
- Escalate GUI, web, data, ML, or destructive runtime work to the matching sibling sub-skill.

## Expected result
A good contribution leaves the project folder easy to review: clear name, readable README, project-specific dependencies, no generated cache noise, and no stale or unsafe links.
