# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, public API,
or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T00:00:00Z",
  "repository": {
    "name": "BayesianOptimization",
    "remote_url": "https://github.com/bayesian-optimization/BayesianOptimization.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "8b9a0624dac0ba4abce04336a0890099bb26a8a3",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "bayesian-optimization",
      "version": "3.3.0",
      "import_names": [
        "bayes_opt"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "bayes_opt"
    ],
    "docs": [
      "README.md",
      "docsrc/index.rst",
      "docsrc/reference"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "tests"
    ],
    "scripts": [
      "scripts"
    ],
    "configs": [
      "pyproject.toml",
      "ruff.toml",
      ".github/workflows"
    ]
  }
}
```

## Evidence Notes

- The repository was a shallow Git checkout at the recorded commit.
- The only dirty path during generation was the newly produced `skills/` tree;
  no source package files were modified as evidence for the public package API.
- Package metadata identifies the distribution as `bayesian-optimization` and
  import root as `bayes_opt`.
- Installed-package inspection verified version `3.3.0` and key public
  signatures for `BayesianOptimization`, acquisition classes,
  `ConstraintModel`, parameter classes, and `SequentialDomainReductionTransformer`.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata, dependencies, public entry points, or `bayes_opt` public
  APIs changed even on the same commit, refresh this skill.
- If examples, docs, or tests changed in the workflows covered by this skill,
  refresh or extend the corresponding sub-skill.
- If the current working tree has source-package changes beyond generated skill
  artifacts, treat the skill as potentially stale for that checkout.
