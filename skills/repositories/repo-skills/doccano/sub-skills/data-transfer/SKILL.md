---
name: data-transfer
description: "Import and export doccano datasets with the right formats and validation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# data-transfer

Use this sub-skill when the task is about getting data into or out of doccano: choosing an import format, validating a file, handling encodings or MIME checks, exporting annotations, or troubleshooting task-specific dataset shapes.

## Covers

- import format selection for text, sequence, seq2seq, intent, image, bounding box, segmentation, captioning, and speech projects
- export format selection and formatter behavior
- encoding, delimiter, column, and file-type validation
- relation extraction import/export handling
- collaborative vs per-user export behavior

## Excludes

- project creation, labels, members, comments, and annotation CRUD: use `project-annotation`
- auto-labeling template/request setup: use `auto-labeling`
- install, deployment, and package build: use `setup-and-deploy`

## Typical path

1. Confirm the project type and whether relation extraction or collaborative export is involved.
2. Choose the matching file format and any delimiter or column settings.
3. Validate the file contents before uploading when possible.
4. Check import errors or export outputs against the documented task shape.

## Read next

- `references/formats.md` for supported formats, task mapping, and export shapes.
- `references/troubleshooting.md` for parser, encoding, size, MIME, and validation failures.
- `../../references/task-types.md` for the project type that owns each annotation shape.
- `scripts/list-formats.py` for a small helper that prints the supported import/export formats by task.
- `../../references/troubleshooting.md` for cross-cutting install/runtime issues that may appear while testing imports or exports.
