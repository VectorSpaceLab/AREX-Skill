---
name: repo-development
description: "Checkout-local OpenLLMetry maintenance workflows for package
  discovery, uv/Nx commands, safe test selection, VCR replay, release caveats,
  and evaluator-model codegen context."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Repo Development

Use this sub-skill for checkout-local maintenance and verification tasks.

## Route away from this sub-skill

- Runtime SDK setup and tracing behavior -> [sdk-and-tracing](../sdk-and-tracing/SKILL.md)
- Provider, vector, framework, and protocol wrappers -> [instrumentations](../instrumentations/SKILL.md)
- Semantic-convention constants and migration rules -> [semantic-conventions](../semantic-conventions/SKILL.md)

## This sub-skill owns

- package discovery and workspace inventory
- `uv` and Nx install / lint / test / type-check / build patterns
- focused native test selection and VCR replay policy
- package layout conventions for `pyproject.toml` and `project.json`
- release and evaluator-model codegen cautions
- checkout-local troubleshooting for missing tools, sources, entry points, and cassette issues

## Start here

- [Development workflows](references/development-workflows.md)
- [Testing, VCR, and Nx](references/testing-vcr-and-nx.md)
- [Source script map](references/source-script-map.md)
- [Troubleshooting](references/troubleshooting.md)
- [Package inventory helper](scripts/list_openllmetry_projects.py)

## Router notes

- Prefer the narrowest package target that exercises the change.
- Use the bundled helper before guessing package structure.
- Keep VCR re-recording explicit; do not refresh cassettes by accident.
