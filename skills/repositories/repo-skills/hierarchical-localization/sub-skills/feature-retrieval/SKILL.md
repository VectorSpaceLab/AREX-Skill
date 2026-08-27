---
name: feature-retrieval
description: "Feature extraction, retrieval descriptors, matching, and HDF5
  feature/match formats for hloc."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Feature Retrieval for Hierarchical-Localization

Use this sub-skill when a task needs `hloc` feature files, global retrieval descriptor files, retrieval pairs, sparse match files, dense LoFTR-derived match files, or guidance for choosing built-in extractor/matcher configurations.

## Route here for

- Local feature extraction with `hloc.extract_features.main`, `ImageDataset`, and `extract_features.confs`.
- Global image retrieval descriptors from the extractor configs `dir`, `netvlad`, `openibl`, or `megaloc`, followed by `hloc.pairs_from_retrieval.main`.
- Sparse matching with `hloc.match_features.main`, including SuperGlue, LightGlue, nearest-neighbor, and AdaLAM config families.
- Dense/semi-dense matching with `hloc.match_dense.main` and LoFTR config families.
- HDF5 feature, global descriptor, and match file naming/schema diagnostics.

## Route elsewhere

- SfM reconstruction, triangulation, pair generation beyond retrieval descriptors, and localization execution: use `../mapping-localization/`.
- Benchmark/dataset pipeline scripts and large dataset preparation: use `../dataset-pipelines/`.
- Implementing custom extractors/matchers or exporting external feature/match files: use `../custom-interop/`.

## Start with these references

1. Read [`references/api-and-cli.md`](references/api-and-cli.md) for verified signatures, CLI options, exact built-in config names, output naming, and config-family selection.
2. Read [`references/hdf5-feature-match-formats.md`](references/hdf5-feature-match-formats.md) before reading or writing `.h5` feature, global descriptor, or match files.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when extraction, retrieval, matching, model download, CUDA/CPU, or HDF5 schema errors occur.
4. Run [`scripts/inspect_hloc_configs.py`](scripts/inspect_hloc_configs.py) in the user's active Python environment to list available installed configs without running neural models.

## Minimal safe patterns

### Extract local features

```python
from pathlib import Path
from hloc import extract_features

images = Path("images")
outputs = Path("outputs")
feature_conf = extract_features.confs["superpoint_aachen"]
feature_path = extract_features.main(feature_conf, images, outputs)
# Usually: outputs / "feats-superpoint-n4096-r1024.h5"
```

### Extract global descriptors and produce retrieval pairs

```python
from pathlib import Path
from hloc import extract_features, pairs_from_retrieval

images = Path("images")
outputs = Path("outputs")
retrieval_conf = extract_features.confs["netvlad"]
descriptor_path = extract_features.main(retrieval_conf, images, outputs)
pairs = outputs / "pairs-netvlad.txt"
pairs_from_retrieval.main(descriptor_path, pairs, num_matched=20)
```

### Match sparse features for a pairs file

```python
from pathlib import Path
from hloc import extract_features, match_features

outputs = Path("outputs")
pairs = outputs / "pairs-netvlad.txt"
feature_conf = extract_features.confs["superpoint_aachen"]
matcher_conf = match_features.confs["superglue"]
feature_path = outputs / f"{feature_conf['output']}.h5"
match_path = match_features.main(matcher_conf, pairs, feature_conf["output"], outputs)
# Usually: outputs / "feats-superpoint-n4096-r1024_matches-superglue_pairs-netvlad.h5"
```

### Match with dense LoFTR

```python
from pathlib import Path
from hloc import match_dense

images = Path("images")
outputs = Path("outputs")
pairs = outputs / "pairs-netvlad.txt"
dense_conf = match_dense.confs["loftr_aachen"]
features_path, matches_path = match_dense.main(dense_conf, pairs, images, export_dir=outputs)
```

Do not assume a feature or match path from memory: compute it from the selected config and pair-file stem, or pass explicit paths via the Python API.
