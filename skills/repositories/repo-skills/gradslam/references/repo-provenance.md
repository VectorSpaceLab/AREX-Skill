# GradSLAM provenance

- **Schema:** `disco.repo-provenance.v1`
- **Package/import:** `gradslam`
- **Package version:** `0.1.0`
- **Source commit:** `44470eee4484aaad703d7bf962a8f42496867a9d`
- **Source branch:** `main`
- **Source remote:** `https://github.com/gradslam/gradslam.git`
- **Source dirty state at analysis:** clean before generated skill artifacts
- **Construction scope:** public package APIs and safe, CPU-first operating
  workflows; external datasets, notebook execution, GUI display, release/CI
  infrastructure, and accelerator-specific claims are excluded or reference-only.

## Relative evidence baseline

The graph was distilled from these repository-relative evidence areas at the
commit above:

- `gradslam/` — runtime implementation and package exports;
- `setup.py`, `requirements.txt`, `gradslam/version.py` — package metadata and
  dependency declarations;
- `README.md`, `docs/`, and selected `examples/` — public intent and workflows;
- `tests/config`, `tests/datasets`, `tests/geometry`, `tests/odometry`,
  `tests/slam`, and `tests/structures` — behavior and edge-case evidence.

The generated files intentionally do not link to those checkout paths. They
contain distilled contracts and bundled safe helpers so a future Researcher
can use the skill after the source checkout is absent. Re-check this provenance
when source APIs, dependency metadata, or tensor contracts change.
