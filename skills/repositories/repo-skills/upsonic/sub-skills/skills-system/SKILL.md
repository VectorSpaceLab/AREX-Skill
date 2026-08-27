---
name: skills-system
description: "Owns Upsonic's reusable Skill/Skills loader system, validation
  rules, dependency resolution, and skill-cache behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# skills-system

Use this route for `Skill`, `Skills`, skill loaders, skill validation, dependency resolution, caching, and skill execution hooks.

## Include

- `Skill` and `Skills` container behavior.
- Loader families such as local, inline, builtin, GitHub, and URL skills.
- Validation, dependency, and cache rules for skill directories.

## Exclude

- The repo skill itself as a managed artifact → root repo skill only.
- Core agent execution and model selection → [agent-runtime](../agent-runtime/SKILL.md) and [models-and-providers](../models-and-providers/SKILL.md).
- Project CLI scaffolding → [project-cli-interfaces](../project-cli-interfaces/SKILL.md).

## Start here

- [references/skill-loading.md](references/skill-loading.md)
- [references/validation-and-dependencies.md](references/validation-and-dependencies.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/validate_skill_dir.py](scripts/validate_skill_dir.py)
