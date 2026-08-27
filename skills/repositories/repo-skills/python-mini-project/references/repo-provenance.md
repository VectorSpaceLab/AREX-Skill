# Repository provenance

Schema: `disco.repo-provenance.v1`

This generated skill is based on a source snapshot of `ndleah/python-mini-project`, a collection of independent beginner Python mini-project folders.

## Source snapshot

| Field | Value |
| --- | --- |
| Repository | `python-mini-project` |
| Remote URL | `https://github.com/ndleah/python-mini-project.git` |
| Commit | `c092b63f24ee927dc1a55a0fe28b176e7a6b6521` |
| Branch | `main` |
| Exact tag | none detected |
| Source package version | not applicable; repository root is not an installable package |
| Subproject package metadata | `RSS_Manager/pyproject.toml` declares `rss-manager` version `0.1.0` |
| Dirty state during generation | untracked `skills/` production output existed/was created; generated skill and review artifacts are not source evidence |

## Evidence paths used

- Repository-level docs and policy: `README.md`, `README_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE.md`, `LICENSE`.
- Project-local docs and code: top-level mini-project folders containing `README*`, `.py`, `requirements*.txt`, `pyproject.toml`, `.ipynb`, local assets, or templates.
- Dependency evidence: root `requirements.txt` (UTF-16LE historical aggregate), project-local `requirements.txt`, and `RSS_Manager/pyproject.toml`.
- Native verification evidence: `Cat_command/cat.py`, `Cat_command/test_cat.txt`, `Execute Shell Command/execute_shell_command.py`, `Execute Shell Command/execute_shell_command_test.py`; `Smart_Calculator` was static-only because it opens Tk at import time.
- Optional/heavy evidence: GUI/game folders, Flask/FastAPI apps, scraping/media folders, notebooks, OpenCV/TensorFlow/YOLO projects, Windows/credentialed/destructive automation examples.

## Refresh guidance

Refresh this skill when any of these change:

- the project folder list changes substantially;
- root or PR contribution rules change;
- root/project-local dependency files are normalized or replaced;
- new tests/examples become safe native candidates;
- a heavy optional project becomes a first-class required workflow;
- source scripts move from top-level folders into a package or shared framework.

When refreshing, update `references/project-catalog.md`, `references/dependency-and-safety-map.md`, all sub-skill routing lists, and the review artifact native candidate map together.
