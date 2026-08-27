# Project template

This reference distills the repo's README patterns from `README_TEMPLATE.md` and representative project READMEs such as `Cat_command/README.md`, `Chess_Game/README.md`, `Image_compressor/README.md`, `Url_Shortener/README.md`, and `Investment Calculator/README.md`.

The goal is not to force every historical folder into one shape. The goal is to give new or repaired mini-project folders a clear, beginner-friendly README that matches the repo's contribution style.

## Core fields for a new starter

| Field | What to include | Why it matters | Generator mapping |
| --- | --- | --- | --- |
| Title | Human-readable project name at the top of the README | Matches the repo's visible style and makes the folder easy to scan | `--title` or a title derived from the folder name |
| Description | One short paragraph explaining what the project does | Tells reviewers and future maintainers what belongs in the folder | `--description` |
| Dependencies | Either a simple list of runtime packages or a note that the project uses only the standard library | Prevents missing-install confusion and keeps dependency files project-local | `--requirement` values and the presence or absence of `requirements.txt` |
| How to run | The exact command or short step list needed to launch the project | Gives users a direct start path without inspecting the source first | a fixed `python main.py` starter or a task-specific run note |
| Demo | A screenshot, GIF, or other local demo asset only if one really exists | Avoids broken image links and stale badges | `--demo` when a real asset path or note is known |
| Author | Name, handle, or profile when available | Useful for attribution in a contribution repo | `--author` |

## Optional fields

| Field | Use it when | Notes |
| --- | --- | --- |
| Demo image block | A project-local image or GIF exists | Prefer a relative path inside the project folder. Do not rely on missing remote assets. |
| Framework list | The project uses named libraries or frameworks | Keep the list short and plain. Avoid copying full install instructions into this section. |
| Stop instructions | The project is interactive or long-running | Mention the normal stop action, such as `CTRL + C`, when relevant. |
| Extra notes | The project needs a short warning or setup detail | Keep it local to the project. Do not turn the README into a general repo policy document. |

## Minimal README shape

````md
# <Project Title>

## Description
<One paragraph that explains what the project does.>

## Requirements
- <runtime dependency or note>

## How to run
```bash
python main.py
```

## Demo
<optional local screenshot or GIF path>

## Author
<name or handle>
````

## Content rules

- Use `README.md` for new work.
- Keep paths relative to the project folder.
- Prefer a short, beginner-friendly explanation over a long marketing block.
- If the project has no external dependencies, say so plainly.
- If the project does have dependencies, create `requirements.txt` only for that folder.
- Historical READMEs mix `Languages or Frameworks Used` and `Requirements`; the starter can normalize that into one clear dependency section.
- Do not copy the root `requirements.txt` into a project folder.
- Do not keep placeholder badge images or broken demo links in a new starter.
- Do not depend on repository-wide assets for a new project unless the task explicitly says to preserve an existing link.

## Distilled template fields

The safe skeleton generator uses the following fields:

| Field | Description |
| --- | --- |
| `title` | The README heading. |
| `description` | The first explanatory paragraph. |
| `requirements` | A list of runtime packages that becomes `requirements.txt` and the README dependency note. |
| `run_command` | The documented run command, defaulting to `python main.py`. |
| `demo` | Optional local demo note or asset path. |
| `author` | Optional attribution line. |

A generated starter should stay small enough that a future maintainer can open the folder, read the README, and understand the first runnable step without guessing.
