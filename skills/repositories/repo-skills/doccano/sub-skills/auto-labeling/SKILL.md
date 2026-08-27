---
name: auto-labeling
description: "Configure and troubleshoot doccano auto-labeling templates and mappings."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# auto-labeling

Use this sub-skill when the task is about doccano's auto-labeling feature: choosing a template, setting request parameters, testing the request, rendering the response, mapping labels, or enabling the feature for a project.

## Covers

- template selection from the settings page or API
- request-parameter testing for predefined or custom REST services
- response mapping and Jinja2-style template rendering
- label mapping into doccano's internal labels
- enabling auto-labeling for annotation workflows
- permission and service troubleshooting

## Excludes

- project creation and annotation CRUD: use `project-annotation`
- import/export file formats: use `data-transfer`
- install, deployment, and package build: use `setup-and-deploy`

## Typical path

1. Confirm the project type and make sure it supports the label collection you need.
2. Choose the predefined template or a custom REST request.
3. Test the request parameters before worrying about mapping.
4. Test the response template and then the label mapping.
5. Enable the feature on the annotation page once the config is stable.

## Read next

- `references/workflows.md` for the end-to-end template, request, mapping, and activation flow.
- `references/troubleshooting.md` for model, credential, response, and permission failures.
- `../../references/task-types.md` for the task types that the mapping layer expects.
- `scripts/list-templates.py` for a small helper that prints the available auto-labeling templates.
- `../../references/troubleshooting.md` for cross-cutting install/runtime issues that can affect service testing.
