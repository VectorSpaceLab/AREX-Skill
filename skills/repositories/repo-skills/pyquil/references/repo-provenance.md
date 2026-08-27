# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a PyQuil checkout.
If the commit, tag, dirty state, package version, or public evidence paths differ
materially, run `refresh-repo-skill` before relying on the graph.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T18:20:00Z",
  "repository": {
    "name": "pyquil",
    "remote_url": "https://github.com/rigetti/pyquil.git",
    "vcs": "git",
    "branch": "master",
    "tag": "v4.18.0",
    "commit": "7a61029b3b39709cbf7986ad2d0886237a4af044",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pyquil",
      "version": "4.18.0",
      "import_names": ["pyquil"]
    }
  ],
  "evidence": {
    "source_roots": ["pyquil"],
    "docs": [
      "README.md",
      "docs/source/getting_started.rst",
      "docs/source/programs_and_gates.rst",
      "docs/source/advanced_usage.rst",
      "docs/source/compiler.rst",
      "docs/source/the_quantum_computer.rst",
      "docs/source/wavefunction_simulator.rst",
      "docs/source/noise.rst",
      "docs/source/troubleshooting.rst"
    ],
    "examples": ["README.md", "docs/source", "docs/source/quilt_*.ipynb"],
    "tests": [
      "test/unit/test_program.py",
      "test/unit/test_quantum_computer.py",
      "test/unit/test_wavefunction_simulator.py",
      "test/unit/test_noise.py",
      "test/unit/test_noise_model.py",
      "test/unit/test_paulis.py",
      "test/unit/test_operator_estimation.py",
      "test/unit/test_graph.py",
      "test/unit/test_qcs.py",
      "test/unit/test_latex.py"
    ],
    "configs": ["pyproject.toml", "test/unit/data/*.json"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale.
- If the checkout's branch/tag or dirty state differs, inspect changed paths
  before use.
- If `pyproject.toml` changes Python bounds, dependencies, extras, entry
  points, or package version, refresh and re-run verification.
- If public APIs under `pyquil/api`, `pyquil/quil*`, `pyquil/simulation`,
  `pyquil/noise`, `pyquil/experiment`, `pyquil/quantum_processor`, or
  `pyquil/latex` change, refresh the relevant sub-skill.

The original evidence paths are provenance only. Runtime use depends on this
bundled skill tree, not on reopening the source checkout.
