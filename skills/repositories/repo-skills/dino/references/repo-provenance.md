# Repository provenance

Schema: `disco.repo-provenance.v1`

- **Project:** DINO — DETR with Improved DeNoising Anchor Boxes for End-to-End Object Detection
- **Source commit:** `d84a491d41898b3befd8294d1cf2614661fc0953`
- **Branch:** `main`
- **Exact tag:** none at the source commit
- **VCS state:** generated from a dirty checkout; the source tree had generated skill/log material under `skills/` during production. The source implementation commit itself was clean before generated output was added.
- **Package version:** no repository distribution metadata or release version was declared; the README identifies the implementation as the official DINO code release.
- **Public source identity:** `IDEA-Research/DINO`, Apache 2.0 license.
- **Evidence paths relative to source root:** `README.md`, `requirements.txt`, `main.py`, `engine.py`, `run_with_submitit.py`, `config/DINO/`, `datasets/`, `models/dino/`, `util/`, `tools/benchmark.py`, `tools/README.md`, `scripts/DINO_*.sh`, and `inference_and_visualization.ipynb`.
- **Bundled replacements:** `scripts/run_dino_eval.py` replaces the source evaluation shell wrappers; `scripts/run_dino_benchmark.py` is the bounded benchmark route for `tools/benchmark.py`; `scripts/build_dino_extension.py` replaces the source build launcher; the training planner, COCO validator, environment checker, and one-image inference helper are bundled under their owning sub-skills.
- **Excluded evidence:** figures, generated logs, downloaded checkpoints/data, build/cache outputs, destructive data-copy helpers, and cluster/release internals not needed for the selected user workflows.

Refresh this skill when the DINO source changes in the model builder, configs,
COCO loader, CUDA operator, CLI parser, launcher behavior, or output/checkpoint
schema. The generated runtime skill does not depend on a private checkout,
Python prefix, or local cache path.
