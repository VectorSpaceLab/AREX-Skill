# Installed Package Inspection

## Purpose

Read this reference when using the user-provided or automatically prepared Python environment to verify runtime facts. The installed package environment is required so generated skill claims are based on live APIs, signatures, modules, imports, CLI entry points, and runtime behavior rather than source-code guesses.

If `create-repo-skill` prepared the environment through `prepare-repo-skill-env`, use the verified handoff from that skill as the temporary inspection context. Do not repeat environment creation unless verification has gone stale or the package fails to import during inspection.

## Safety and Privacy Rules

Inspect only with read-only commands unless the user explicitly authorizes side effects.

Do not copy these details into the generated public skill:

- Local Python executable paths
- Virtualenv or conda environment names
- Activation commands
- Machine-specific paths
- Local checkout paths
- `pip show` installation locations

These details are allowed in working notes only. Normalize findings into public, reproducible installation and runtime guidance.

## Basic Checks

Useful checks include:

```bash
python -c "import package_name; print(package_name.__file__)"
python -c "import package_name, inspect; print(dir(package_name))"
python -m pip show package-name
```

Use `pip show` for metadata such as public package name, version, requirements, and entry points where available, but do not copy local installation paths into the generated skill.

## Signature and Docstring Inspection

For important objects, inspect signatures and docstrings:

```bash
python - <<'PY'
import inspect
from package_name import target

print(inspect.signature(target))
print(inspect.getdoc(target))
PY
```

When APIs are discovered dynamically, write short temporary inspection snippets rather than guessing signatures from memory.

## What to Verify

Verify:

- Importability of the public package and important submodules.
- Public classes, functions, config objects, and constants that the generated skill will mention.
- Signatures, defaults, accepted parameter names, and return shapes for important APIs.
- CLI entry points, help output, command names, flags, and config file expectations.
- Optional dependency behavior, backend availability, and common import errors.
- Minimal smoke tests that are safe, deterministic, and do not require downloads, credentials, training runs, or destructive writes unless the user explicitly wants that behavior.

## Translating Findings into Skill Content

Use installed-package inspection to confirm facts, then describe them generically:

- Prefer public install commands and documented extras over local editable install details unless editable install is relevant to community users.
- Say what dependencies, credentials, services, hardware, data files, or extras are required.
- Include minimal import checks in the generated root `SKILL.md`.
- Put deeper API signatures and parameter notes in the nearest `references/api-reference.md`.
- Put safe reusable checks or smoke tests in generated `scripts/`.
