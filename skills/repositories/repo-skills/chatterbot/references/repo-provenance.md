# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of ChatterBot. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T19:27:01Z",
  "repository": {
    "name": "ChatterBot",
    "remote_url": "https://github.com/gunthercox/ChatterBot.git",
    "vcs": "git",
    "branch": "master",
    "tag": "1.2.14",
    "commit": "2d909e2635785efdb95ea4429ac5ab94e0c28fb2",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "ChatterBot",
      "version": "1.2.14",
      "import_names": ["chatterbot"]
    }
  ],
  "evidence": {
    "source_roots": [
      "chatterbot",
      "chatterbot/ext/django_chatterbot",
      "chatterbot/ext/sqlalchemy_app"
    ],
    "docs": [
      "README.md",
      "docs/quickstart.rst",
      "docs/chatterbot.rst",
      "docs/training.rst",
      "docs/corpus.rst",
      "docs/logic",
      "docs/storage",
      "docs/django",
      "docs/large-language-models.rst",
      "docs/security.rst"
    ],
    "examples": [
      "examples/basic_example.py",
      "examples/memory_sql_example.py",
      "examples/training_example_list_data.py",
      "examples/training_example_chatterbot_corpus.py",
      "examples/export_example.py",
      "examples/math_and_time.py",
      "examples/convert_units.py",
      "examples/specific_response_example.py",
      "examples/default_response_example.py",
      "examples/tagged_dataset_example.py",
      "examples/django_example"
    ],
    "tests": [
      "tests/test_cli.py",
      "tests/test_chatbot.py",
      "tests/test_preprocessors.py",
      "tests/test_comparisons.py",
      "tests/test_search.py",
      "tests/test_tagging.py",
      "tests/logic",
      "tests/storage",
      "tests/training",
      "tests/django_integration"
    ],
    "metadata": ["pyproject.toml", "setup.cfg"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current repo is clean and this snapshot's only dirty path was generated `skills/`, that does not by itself invalidate the skill.
- If public constructor signatures, optional dependency groups, storage adapter names, trainer classes, logic adapter names, or Django model/settings behavior changed, refresh the skill.
- If ChatterBot's default language model mapping or Redis/LLM experimental APIs changed, refresh the affected sub-skill before relying on it.
