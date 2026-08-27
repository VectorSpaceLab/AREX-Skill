---
name: python-mini-project
description: "Route and safely maintain the ndleah Python Mini Projects
  collection of standalone beginner Python scripts, games, web apps, automation
  tools, data/media demos, and ML/CV examples."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Python Mini Projects repo skill

Use this skill when the task is about the `python-mini-project` repository, its top-level mini-project folders, adding/reviewing a project contribution, or safely running/checking one of the standalone Python examples.

This repository is not one importable package. It is a gallery of independent project folders. Start by identifying the target folder and execution surface, then load the matching sub-skill.

## First steps

1. If the user names a folder, locate it in `references/project-catalog.md`.
2. If the user describes a task instead of a folder, route by execution surface in the table below.
3. Use static checks before running project code:
   - `scripts/inventory_mini_projects.py` scans a checkout and categorizes folders.
   - `scripts/check_project_static.py` parses one or more folders and reports import/runtime hazards.
4. Install dependencies only for the selected project folder and verification target. Do not install root-wide requirements blindly.
5. Execute live code only after display, network, credential, model, OS, and destructive side-effect constraints are explicit.

## Route map

| Task or signal | Read next | Why |
| --- | --- | --- |
| Add a new mini-project, review a PR, fix README/requirements/style, remove cache files | `sub-skills/contribution-and-project-maintenance/SKILL.md` | Covers repository conventions, README template, PR checklist, and project skeleton generation. |
| Pure Python CLI utilities, algorithms, data structures, text/file transforms, safe tiny checks | `sub-skills/cli-algorithms-and-utilities/SKILL.md` | Covers stdlib-heavy scripts and the only default native smoke checks. |
| Tkinter, pygame, turtle, curses, GUI calculators, desktop apps, audio/game loops | `sub-skills/games-gui-and-desktop/SKILL.md` | Covers display/audio/assets/event-loop hazards. |
| Flask/FastAPI apps, HTTP/socket servers, email/WhatsApp/bot automation, credentials, host automation | `sub-skills/web-network-and-automation/SKILL.md` | Covers services, ports, DB setup, API keys, credentialed/network/destructive work. |
| Scraping, PDF/image/audio conversion, notebooks, OpenCV, TensorFlow/Keras, Ultralytics/YOLO, plotting | `sub-skills/data-media-ml-and-vision/SKILL.md` | Covers data/media/CV/ML dependencies, fixtures, backends, and safe skip rules. |

## Root references

- `references/project-catalog.md` lists known mini-project folders by route and gives the long-tail routing rule.
- `references/dependency-and-safety-map.md` explains per-project dependency selection, optional backends, and safety classes.
- `references/troubleshooting.md` covers cross-cutting setup, cwd, dependency, display, network, credential, and unsafe-script failures.
- `references/repo-provenance.md` records the source snapshot and refresh baseline.
- `references/repo-routing-metadata.json` contains structured router metadata for managed import tooling.

## Root scripts

- `scripts/inventory_mini_projects.py --root <checkout> --format markdown` scans top-level project folders without importing or executing them.
- `scripts/check_project_static.py --root <checkout> <project-folder> [...]` statically reports syntax, imports, notebooks, requirements files, and common runtime hazards.

Both scripts are safe by default. They inspect text and AST only; they do not start servers, GUI loops, network calls, model loads, email sends, port scans, or host commands.

## Dependency posture

- The root `requirements.txt` is historical and not a clean universal lockfile.
- Prefer the target folder's `requirements.txt` or `pyproject.toml` when present.
- For folders with no dependency file, statically inspect imports first and install only what the selected task needs.
- Treat GUI/display, audio, network/API, credentials, camera, model downloads, GPU/CUDA, Windows COM, and host-destructive operations as optional prepared scopes, not mandatory baseline verification.

## Verification posture

The mandatory baseline for this skill is CPU-only static inspection plus curated safe stdlib checks. Optional projects are still documented, but they are not considered live-verified unless a future task prepares their exact environment and authorizes required side effects.

Default safe native candidates are owned by `cli-algorithms-and-utilities`:

- `Cat_command` fixture-based output check.
- `Execute Shell Command` unittest with a fixed `echo` command.

Do not run by default:

- `Smart_Calculator` tests, because the module opens Tk at import time.
- GUI/game projects without a display/audio-capable session.
- services or sockets without isolated ports and timeouts.
- network/API/email/WhatsApp/Firebase/Spotify flows without disposable credentials.
- OpenCV/TensorFlow/YOLO/camera/model workflows without a prepared project-specific environment.
- shutdown, spam, port scanning, database dumping, or other destructive/unauthorized automation.

## Refresh rule

If a future checkout has new project folders, changed contribution rules, normalized dependency files, or new safe tests/examples, refresh the project catalog, safety map, sub-skill route lists, and native candidate map together.
