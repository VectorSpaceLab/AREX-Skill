---
name: labelme
description: "Routes labelme image annotation, Annotation File, dataset export,
  AI-assisted annotation, configuration, and repository-maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# labelme

Use this skill when a task involves the `labelme` Python image-annotation
application, its JSON Annotation Files, its YAML Config File, its conversion
examples, or maintenance of the `wkentaro/labelme` repository.

## First checks

- Install for normal use with `python -m pip install labelme` on Python 3.12+.
- Smoke-check an environment with `scripts/check_labelme_environment.py` when the
  task depends on the installed package, CLI, optional converters, or GUI display.
- Read `references/public-interface-and-scope.md` before treating any Python
  module as stable; labelme v7 is an application, not a general-purpose library.
- Read `references/repo-provenance.md` before deciding whether this skill is
  current for a checkout.
- For cross-cutting install, display, optional dependency, AI, or JSON load
  failures, start with `references/troubleshooting.md`.

## Route by task

| User task | Read next |
| --- | --- |
| Launch labelme, choose CLI flags, set labels/flags, use `--config`, inspect or validate the Config File, handle PySide6/display startup | `sub-skills/cli-and-config/SKILL.md` |
| Understand or validate labelme JSON, Shapes, Flags, Shape Flags, Groups, Mask Shapes, embedded `imageData`, dimensions, or rasterization behavior | `sub-skills/annotation-data/SKILL.md` |
| Convert Annotation Files to `label.png`, `label_names.txt`, VOC segmentation/object outputs, VOC bbox XML, or COCO `annotations.json` | `sub-skills/dataset-export/SKILL.md` |
| Use or debug AI Assist, AI Text Prompt, SAM/SAM2/SAM3/EfficientSAM/YOLO-World model choices, prompt compatibility, output shapes, suppression | `sub-skills/ai-assisted-annotation/SKILL.md` |
| Modify the labelme repository, choose tests, update changelog/docs/translations, interpret domain docs or triage labels | `sub-skills/repo-development/SKILL.md` |

## Operating model

- Use the project glossary terms precisely: an **Annotation** is the whole JSON
  bundle for one Image; a **Shape** is one drawn region; a **Flag** is
  image-level; a **Shape Flag** belongs to one Shape; a **Group** is shared
  `group_id`.
- Do not tell future agents to open original repo examples or tests. This skill
  bundles distilled references and reusable scripts for the common workflows.
- Prefer direct JSON parsing for downstream ML datasets. The package's internal
  modules are useful evidence but not public API promises.
- Treat real AI model download/inference as optional and network-bound. Prompt
  compatibility must be checked before model download or inference.
- Treat GUI tests and interactive sessions as display-dependent. CLI help,
  config parsing, Annotation File validation, and conversion scripts are
  headless.

## Bundled shared scripts

- `scripts/check_labelme_environment.py` verifies installed package metadata,
  imports, CLI help, optional dependency availability, and display variables.
- `scripts/labelme_json_core.py` is a shared, self-contained helper library used
  by the bundled Annotation File and dataset export scripts; read it when
  adapting those scripts.

## Verification and import status

This skill was produced with `not import`; it is a runtime candidate under the
repository's `skills/disco/` tree and is not installed into DisCo's managed
`repo-skills/` collection by this creation run. If later importing, use the
verified repo-skill import protocol rather than manually editing a router.
