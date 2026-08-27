# Contribution workflow

This repository is a collection of independent mini-project folders. The maintainer task is usually one of four actions: add a new folder, fix an existing folder, review a PR, or triage what kind of project a folder belongs to.

Source evidence for this workflow comes from `README.md`, `README_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE.md`, and representative project READMEs such as `Cat_command/README.md`, `Chess_Game/README.md`, `Image_compressor/README.md`, `Url_Shortener/README.md`, and `Automated_Mailing/README.md`.

## Repo contribution flow

1. Fork or clone the repository you are working in.
2. Create a feature branch from the latest main branch state.
3. Add or fix one mini-project folder at a time when possible.
4. Commit and push the change set.
5. Open a PR and complete the checklist in `.github/PULL_REQUEST_TEMPLATE.md`.

## What this sub-skill owns

- Folder creation and cleanup for a single mini-project.
- README normalization against the repo template.
- Project-local dependency files such as `requirements.txt`.
- Static asset discipline and relative path review.
- Cache and generated-file cleanup.
- PR review for naming, documentation, and hygiene.

## Add a new mini-project

1. Pick a folder name.
   - Prefer a single ASCII folder name.
   - Use underscores for new folders when practical.
   - Keep the name short, human-readable, and stable.
   - Do not include path separators or hidden-name prefixes.
   - Do not rename unrelated folders just to match a style preference.
2. Create the folder.
3. Add `README.md` with the repo's mini-project sections.
   - Title.
   - Description.
   - Dependencies or requirements note.
   - How to run.
   - Demo only if there is a real local asset.
   - Author when known.
4. Add the project entry point.
   - Most mini-projects use `main.py` or a single named script.
   - Keep the entry point path simple and documented.
5. Add `requirements.txt` only when the project needs non-stdlib runtime dependencies.
   - Keep one requirement per line.
   - Do not use the repo root `requirements.txt` as a shared lockfile.
6. Store assets inside the project folder when possible.
   - Use relative paths in the README.
   - Avoid depending on repository-wide asset folders for new work.
7. Remove generated clutter before review.
   - `__pycache__`
   - `.ipynb_checkpoints`
   - stray local screenshots or build outputs
8. Open the PR using the repo's PR template.

## Fix an existing mini-project

1. Keep the folder name stable unless the task explicitly asks for a rename.
2. Repair the smallest useful set of files.
   - README wording.
   - Entry-point naming.
   - Requirements formatting.
   - Asset references.
3. Preserve project-local intent.
   - Do not rewrite unrelated folders.
   - Do not replace a project-specific dependency file with a root-level dependency list.
4. If the project is GUI, web, data, ML, or otherwise runtime-heavy, keep this maintenance pass static and route execution work to the matching sibling sub-skill.

## Review a PR

Use the repo PR checklist as a minimum acceptance gate.

| Checklist item from `.github/PULL_REQUEST_TEMPLATE.md` | What to confirm |
| --- | --- |
| Named files and folder according to guidelines | Folder name is stable, human-readable, and does not introduce path or hidden-name problems. |
| Code follows style guidelines | The project folder uses the expected entry point and ordinary Python style for the repo's scope. |
| Comments in hard-to-understand areas | The script is readable enough for beginners and future maintainers. |
| Helpful `README.md` from `README_TEMPLATE.md` | The README has a clear title, description, run instructions, and dependency note when needed. |
| No warnings | No generated caches, stale badges, broken local paths, or obvious destructive side effects. |

## File and folder conventions

| Item | Preferred convention | Notes |
| --- | --- | --- |
| Project folder | Short, stable, ASCII name; underscores for new folders when practical | Existing historical folders may use spaces, hyphens, or mixed case; do not rename them unless asked. |
| README file | `README.md` | Use this exact case for new work. Legacy case variants can remain in untouched historical folders. |
| Entry point | `main.py` or the project's documented single script | Keep the file path simple and runnable from the folder. |
| Requirements file | `requirements.txt` | Only for project-local runtime dependencies. One package per line. |
| Assets | `assets/`, `img/`, `images/`, or another folder inside the project | Use relative paths from the README and code. |

## What to hand back

A clean maintenance change should leave the project folder ready for review with a clear README, correct filenames, local assets, and no generated noise.
