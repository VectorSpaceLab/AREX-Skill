# Repository Provenance

## Purpose

Read this before deciding whether this Vaex repo skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T18:13:53Z",
  "repository": {
    "name": "vaex",
    "remote_url": "https://github.com/vaexio/vaex.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "65ab46281939e2fd2fc291266bb08a328ff59882",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "Only generated skill, artifact, and production log paths were dirty at creation time."
  },
  "packages": [
    {"name": "vaex", "version": "4.19.0", "import_names": ["vaex"]},
    {"name": "vaex-core", "version": "4.19.0", "import_names": ["vaex"]},
    {"name": "vaex-hdf5", "version": "0.15.0", "import_names": ["vaex.hdf5"]},
    {"name": "vaex-viz", "version": "0.6.0", "import_names": ["vaex.viz"]},
    {"name": "vaex-ml", "version": "0.19.0", "import_names": ["vaex.ml"]},
    {"name": "vaex-server", "version": "0.10.0", "import_names": ["vaex.server"]},
    {"name": "vaex-astro", "version": "0.10.0", "import_names": ["vaex.astro"]},
    {"name": "vaex-jupyter", "version": "0.9.0", "import_names": ["vaex.jupyter"]},
    {"name": "vaex-graphql", "version": "0.3.0", "import_names": ["vaex.graphql"]},
    {"name": "vaex-arrow", "version": "0.5.1", "import_names": ["vaex.arrow"]}
  ],
  "evidence": {
    "source_roots": [
      "packages/vaex-core/vaex",
      "packages/vaex-core/src",
      "packages/vaex-hdf5/vaex/hdf5",
      "packages/vaex-viz/vaex/viz",
      "packages/vaex-ml/vaex/ml",
      "packages/vaex-server/vaex/server",
      "packages/vaex-jupyter/vaex/jupyter",
      "packages/vaex-astro/vaex/astro",
      "packages/vaex-graphql/vaex/graphql",
      "packages/vaex/vaex/meta"
    ],
    "metadata": [
      "setup.py",
      "packages/vaex/setup.py",
      "packages/vaex-core/setup.py",
      "packages/vaex-core/pyproject.toml",
      "packages/vaex-hdf5/setup.py",
      "packages/vaex-viz/setup.py",
      "packages/vaex-ml/setup.py",
      "packages/vaex-server/setup.py",
      "packages/vaex-jupyter/setup.py",
      "packages/vaex-astro/setup.py",
      "packages/vaex-graphql/setup.py"
    ],
    "docs": [
      "README.md",
      "docs/source/api.rst",
      "docs/source/installing.rst",
      "docs/source/conf.md",
      "docs/source/tutorial.ipynb",
      "docs/source/tutorial_ml.ipynb",
      "docs/source/tutorial_jupyter.ipynb",
      "docs/source/guides/io.ipynb",
      "docs/source/guides/server.md",
      "docs/source/guides/advanced_plotting.ipynb",
      "docs/source/guides/data_types.ipynb",
      "docs/source/guides/missing_or_invalid_data.ipynb",
      "docs/source/guides/ml_iris.ipynb",
      "docs/source/guides/ml_titanic.ipynb",
      "docs/source/guides/progressbars.ipynb"
    ],
    "tests": [
      "tests/from_dict_test.py",
      "tests/evaluate_test.py",
      "tests/groupby_test.py",
      "tests/agg_test.py",
      "tests/join_test.py",
      "tests/export_test.py",
      "tests/hdf5_test.py",
      "tests/arrow/",
      "tests/ml/",
      "tests/viz_test.py",
      "tests/jupyter/",
      "tests/server/",
      "tests/astro/",
      "tests/settings_test.py",
      "tests/open_test.py"
    ],
    "scripts": [
      "bin/vaex",
      "bin/webveax",
      "bin/vaex_benchmark.py",
      "bin/vaex_benchmark_memory.py",
      "bin/vaex_benchmark_mmap.py",
      "bin/get_vaex.sh",
      "bin/install_pcre.sh",
      "ci/",
      "dodo.py",
      "Makefile"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source package versions, setup metadata, entry points, or public API signatures changed, run `refresh-repo-skill`.
- If the current working tree has non-generated changes under the evidence paths listed above, refresh before relying on this skill for exact source behavior.
- If optional dependency behavior changed for GraphQL, Jupyter widgets, TensorFlow, FastAPI/TestClient, or cloud filesystems, refresh the affected sub-skill and verification artifacts.

## Source State Notes

- The source checkout used for skill creation was a shallow clone. Several vendored C++ submodule directories under `packages/vaex-core/vendor/` were present as submodule placeholders; ordinary API inspection used matching public Vaex wheels rather than a source editable build.
- The generated runtime skill is self-contained and does not require access to those submodules or the source checkout.
