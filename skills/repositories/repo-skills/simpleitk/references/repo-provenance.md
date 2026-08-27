# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-24T00:00:00Z",
  "repository": {
    "name": "SimpleITK",
    "remote_url": "https://github.com/SimpleITK/SimpleITK",
    "vcs": "git",
    "branch": "main",
    "tag": "latest",
    "commit": "3724b01e9badb4a0ad34e74738481ad3809da843",
    "working_tree": "dirty-untracked-generated-skill-artifacts",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "simpleitk",
      "version": "2.5.5-inspected-wheel; checkout Version.cmake baseline 3.0.0 development branch",
      "import_names": [
        "SimpleITK"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "Code/Common",
      "Code/IO",
      "Code/BasicFilters",
      "Code/Registration",
      "Code/ElastixTransformixWrappers",
      "Wrapping/Python/SimpleITK"
    ],
    "docs": [
      "Readme.md",
      "docs/source/fundamentalConcepts.rst",
      "docs/source/IO.rst",
      "docs/source/registrationOverview.rst",
      "docs/source/gettingStarted.rst",
      "docs/source/building.rst",
      "docs/source/setUp.rst"
    ],
    "examples": [
      "Examples/HelloWorld",
      "Examples/SimpleGaussian",
      "Examples/SimpleIO",
      "Examples/DicomSeriesReader",
      "Examples/DicomImagePrintTags",
      "Examples/FastMarchingSegmentation",
      "Examples/N4BiasFieldCorrection",
      "Examples/ImageRegistrationMethod1",
      "Examples/ImageRegistrationMethodBSpline1",
      "Examples/ImageRegistrationMethodDisplacement1",
      "Examples/LandmarkRegistration",
      "Examples/Elastix"
    ],
    "tests": [
      "Wrapping/Python/tests",
      "Testing/Unit"
    ],
    "configs": [
      "pyproject.toml",
      "CMakeLists.txt",
      "Version.cmake",
      "CMake/sitkLanguageOptions.cmake",
      ".pre-commit-config.yaml",
      ".readthedocs.yml"
    ],
    "existing_repo_skill_evidence": [
      "skills/simpleitk"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the dirty paths differ from the generated-skill artifact paths recorded here, run `refresh-repo-skill`.
- If package metadata, CMake options, wrapper availability, public examples, or Python entry points changed even on the same commit, run `refresh-repo-skill`.
- If a task requires APIs that differ between the inspected wheel and the current checkout, verify the current install with `scripts/check_simpleitk_env.py` and refresh this skill if the discrepancy affects guidance.
