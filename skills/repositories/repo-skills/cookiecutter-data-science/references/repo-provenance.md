# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Cookiecutter Data Science. If the current repo commit, dirty state, package version, public entry points, option schema, hooks, template tree, docs, or tests differ from this snapshot, run `refresh-repo-skill` before relying on this skill for precise behavior.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T18:38:11Z",
  "repository": {
    "name": "cookiecutter-data-science",
    "remote_url": "https://github.com/drivendataorg/cookiecutter-data-science.git",
    "vcs": "git",
    "branch": "master",
    "tag": "v2.3.0",
    "commit": "0f6b163cdbe3918a2c65ab57ad9fefda93976d9e",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "cookiecutter-data-science",
      "version": "2.3.0",
      "import_names": [
        "ccds"
      ],
      "console_scripts": [
        "ccds"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "ccds/",
      "hooks/"
    ],
    "template_roots": [
      "{{ cookiecutter.repo_name }}/"
    ],
    "docs": [
      "README.md",
      "docs/docs/index.md",
      "docs/docs/using-the-template.md",
      "docs/docs/opinions.md",
      "docs/docs/why.md",
      "docs/docs/v1.md",
      "docs/docs/all-options.md"
    ],
    "configs": [
      "pyproject.toml",
      "setup.cfg",
      "ccds.json",
      "ccds-help.json",
      "cookiecutter.json",
      ".github/workflows/tests.yml"
    ],
    "tests": [
      "tests/conftest.py",
      "tests/test_creation.py",
      "tests/test_functions.sh",
      "tests/conda_harness.sh",
      "tests/virtualenv_harness.sh",
      "tests/pipenv_harness.sh",
      "tests/uv_harness.sh",
      "tests/pixi_harness.sh",
      "tests/poetry_harness.sh"
    ],
    "scripts": [
      "docs/scripts/configuration-table.py",
      "docs/scripts/generate-termynal.py"
    ]
  }
}
```

## Refresh check

Run `refresh-repo-skill` if any of these change:

- `git rev-parse HEAD` differs from the `repository.commit` above.
- The current checkout is not tag `v2.3.0` and the task requires exact released behavior.
- `pyproject.toml` changes distribution metadata, Python support, dependencies, or console entry points.
- `ccds.json` or `ccds-help.json` changes options, defaults, nested subfields, or help semantics.
- `ccds/monkey_patch.py`, `ccds/__main__.py`, `ccds/hook_utils/`, or `hooks/` changes prompt, context, dependency-writing, or post-generation behavior.
- The template tree under `{{ cookiecutter.repo_name }}/` changes generated paths, Makefile rules, scaffold modules, docs, tests, or configuration files.
- Native tests in `tests/` change the valid option matrix or expected generated output.

This provenance omits local environment paths and private setup details by design.
