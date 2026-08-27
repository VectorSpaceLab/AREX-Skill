# Repository Provenance

## Purpose

Read this before deciding whether this HanLP repo skill is current for a checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:30:00Z",
  "repository": {
    "name": "HanLP",
    "remote_url": "https://github.com/hankcs/HanLP.git",
    "vcs": "git",
    "branch": "doc-zh",
    "tag": null,
    "commit": "ddb1299bddff079e447af52ec12549c50636bfa8",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "hanlp", "version": "2.1.0-beta.64", "import_names": ["hanlp"]},
    {"name": "hanlp-common", "version": "0.0.22", "import_names": ["hanlp_common"]},
    {"name": "hanlp-trie", "version": "0.0.5", "import_names": ["hanlp_trie"]},
    {"name": "hanlp-restful", "version": "0.0.23", "import_names": ["hanlp_restful"]}
  ],
  "evidence": {
    "source_roots": ["hanlp/", "plugins/hanlp_common/hanlp_common/", "plugins/hanlp_trie/hanlp_trie/", "plugins/hanlp_restful/hanlp_restful/"],
    "docs": ["README.md", "docs/install.md", "docs/tutorial.md", "docs/configure.md", "docs/data_format.md", "docs/contributing.md", "docs/api/"],
    "examples": ["plugins/hanlp_demo/hanlp_demo/"],
    "tests": ["tests/", "plugins/hanlp_trie/tests/", "plugins/hanlp_restful/tests/"],
    "configs": ["setup.py", "plugins/hanlp_common/setup.py", "plugins/hanlp_trie/setup.py", "plugins/hanlp_restful/setup.py", ".github/workflows/unit-tests.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If package versions, optional extras, public method signatures, pretrained identifier modules, RESTful methods, or documented data formats changed, refresh the skill.
- Ignore dirty paths that are only newly generated skill/review artifacts unless the source package, docs, tests, or examples also changed.
