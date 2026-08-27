# Repository Provenance

This file records the source state used to build the Graphormer repo skill.
It is public skill metadata and should stay free of machine-specific paths.

## Source snapshot

- repository: Graphormer
- source commit: `a04573c40705fb174db261bb746a8258d00992f5`
- source branch: `main`
- exact tag at HEAD: none
- working tree state: clean at capture time
- remote URL: `https://github.com/microsoft/Graphormer.git`
- package version: unavailable from root package metadata; Graphormer is consumed as a fairseq user-dir source checkout rather than as a standalone root distribution
- bundled fairseq submodule commit: `98ebe4f1ada75d006717d84f9d603519d8ff5579`

## Relative evidence paths used

- `README.md`
- `install.sh`
- `docs/Installation-Guide.rst`
- `docs/Quick-Start.rst`
- `docs/Parameters.rst`
- `docs/Datasets.rst`
- `docs/Overview.rst`
- `docs/Tutorisals.rst`
- `docs/Pretrained-Models.rst`
- `examples/customized_dataset/customized_dataset.py`
- `examples/property_prediction/*.sh`
- `examples/oc20/oc20.sh`
- `graphormer/`
- `distributional_graphormer/`
- `.gitmodules`
- `skills/Graphormer.log`

## Refresh baseline

Use this snapshot to decide whether the skill needs refresh or extension:

- if Graphormer code, docs, examples, or the fairseq submodule move forward,
  the skill may need `refresh-repo-skill`
- if only a new workflow is needed, `extend-repo-skill` may be enough
- if the repository and evidence paths still match this snapshot, the current
  skill remains aligned

## Notes

- This skill was built from a source checkout that contains a fairseq
  submodule and multiple optional DiG research subprojects.
- The generated runtime skill must remain self-contained; it should not depend
  on reopening the original checkout.
