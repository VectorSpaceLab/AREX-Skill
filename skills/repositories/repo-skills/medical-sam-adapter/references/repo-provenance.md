# Repository provenance

- **Schema:** `disco.repo-provenance.v1`
- **Source project:** Medical-SAM-Adapter
- **Source branch:** `main`
- **Source commit:** `5888e722876511f177e8e762498a7986753b7f7d7`
- **Tag/version evidence:** no source tag was observed during extraction; the README announces `v0.1.0-alpha` as a historical release, not as the inspected checkout's package version.
- **Package metadata:** no normal Python package metadata was present; `environment.yml` and the repository scripts are the dependency/entry-point evidence.
- **Observed source state:** source behavior was read from the commit above.
- **Dirty state:** `true` for the working tree because this local production added the runtime skill and review artifacts; generated Python cache files from private import inspection were removed. The source snapshot itself remains identified by the commit above, and no private environment or checkout path is required at runtime.
- **Backend evidence:** CUDA is required for actual core training/evaluation and standalone MobileSAMv2 inference; CPU checks are diagnostics only.

## Relative evidence paths

- `README.md` — requirements, dataset recipes, 2D/3D examples, checkpoints, and limitations.
- `environment.yml` — historical dependency specification and conflicting CPU/CUDA pins.
- `cfg.py` — shared CLI flags and defaults.
- `train.py`, `val.py` — training and independent evaluation entry points.
- `function.py`, `utils.py` — training/evaluation loops, data loading, metrics, model selection, and CUDA behavior.
- `dataset/__init__.py` and registered `dataset/*.py` modules — adapter registry and sample/layout evidence.
- `models/sam/`, `models/efficient_sam/`, `models/ImageEncoder/`, `models/common/` — model registries and Adapter/LoRA/AdaLoRA implementation evidence.
- `models/MobileSAMv2/Inference.py` and `models/MobileSAMv2/mobilesamv2/` — standalone inference CLI/import/weight behavior.
- `guidance/Dataset.md`, `guidance/efficient_sam.ipynb`, `guidance/lora.ipynb`, and `guidance/mobile_sam.ipynb` — workflow intent and examples used as read-only evidence.

## Extraction boundary

The runtime skill distills the documented data, training, evaluation, and
MobileSAMv2 inference workflows. It intentionally excludes source checkout
scripts as launchers, notebook execution, dataset/checkpoint downloaders,
legacy unregistered models, generated caches, and vendored maintainer internals.
Bundled helpers are read-only preflight/inspection adaptations; they do not
implicitly import or execute the source repository.
