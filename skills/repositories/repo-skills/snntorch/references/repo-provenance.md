{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T18:00:50Z",
  "repository": {
    "name": "snntorch",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": "v1.0.0",
    "commit": "04053eddf88b2fb919d5c4f42d81663fa0cd12ad",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "snntorch",
      "version": "1.0.0",
      "import_names": [
        "snntorch"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "snntorch"
    ],
    "docs": [
      "README.rst",
      "docs"
    ],
    "tests": [
      "tests"
    ],
    "examples": [
      "examples"
    ],
    "packaging": [
      "setup.py",
      "setup.cfg",
      "pyproject.toml",
      "requirements_dev.txt",
      "docs/requirements.txt"
    ],
    "ci": [
      ".github/workflows/build.yml"
    ]
  }
}
