# Repository Provenance

Read this before deciding whether this skill is current for a BEHAVIOR-1K
checkout. If the source commit, dirty state, package version, or evidence paths
differ, refresh the skill before relying on version-sensitive claims.

```json
{
  "schema": "disco.repo-provenance.v1",
  "repository": {
    "name": "BEHAVIOR-1K",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "eb3c01263b76f4404e8187c1bcd758d48d47a020",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "bddl",
      "version": "3.7.0",
      "import_names": ["bddl"]
    }
  ],
  "construction_scope": "CPU-verifiable BDDL-only",
  "evidence": {
    "metadata": ["bddl3/setup.py", "bddl3/MANIFEST.in"],
    "docs": ["bddl3/README.md", "bddl3/docs/activity_definition.md", "bddl3/docs/overview.md"],
    "source_roots": [
      "bddl3/bddl/activity.py",
      "bddl3/bddl/parsing.py",
      "bddl3/bddl/condition_evaluation.py",
      "bddl3/bddl/predicates.py",
      "bddl3/bddl/logic_base.py",
      "bddl3/bddl/config.py",
      "bddl3/bddl/object_taxonomy.py",
      "bddl3/bddl/knowledge_base/"
    ],
    "runtime_data": ["bddl3/bddl/activity_definitions/", "bddl3/bddl/generated_data/"],
    "tests": ["bddl3/tests/bddl_tests.py", "bddl3/tests/test_taxonomy.py", "bddl3/tests/test_knowledgebase.py"]
  },
  "unverified_excluded": ["OmniGibson/Isaac Sim workflows", "GPU simulation", "maintainer data-generation pipelines", "non-BDDL monorepo packages"]
}
```

The dirty state refers to production outputs under `skills/`; the retained
tracked BDDL evidence was read at the commit above. Package data, activity
counts, taxonomy counts, generated models, and helper behavior are
version-sensitive. The runtime skill contains no original-checkout links,
private environment paths, or installation-location details.
