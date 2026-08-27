---
name: project-annotation
description: "Create projects, define labels, manage members, and annotate with doccano."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# project-annotation

Use this sub-skill for the interactive annotation workflow: creating projects, choosing the right task type, defining labels, adding members, assigning work, annotating examples, reviewing comments, cloning projects, and reading progress metrics.

## Covers

- project creation and project-type selection
- label type creation, import, and deletion
- member creation, role changes, and member permissions
- example lists, assignments, comments, and annotation CRUD
- project cloning and progress/label-distribution metrics

## Excludes

- dataset import/export file formats: use `data-transfer`
- auto-labeling template and mapping setup: use `auto-labeling`
- install, deployment, package build, and CLI startup: use `setup-and-deploy`

## Typical path

1. Create the project with the right task type.
2. Define the labels and decide whether members may create label types.
3. Add members with the correct role for the annotation workflow.
4. Import or create examples, assign work if needed, and annotate.
5. Use comments, clone, and metrics to review progress or duplicate a project.

## Read next

- `../../references/task-types.md` for the supported task types and their label shapes.
- `references/workflows.md` for the full project, label, member, comment, and annotation flow.
- `references/troubleshooting.md` for permission, validation, and annotation-conflict failures.
- `../../references/troubleshooting.md` for cross-cutting runtime failures that can surface in the UI.
