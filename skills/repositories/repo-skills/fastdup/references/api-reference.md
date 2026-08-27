# API reference

This reference summarizes the public Python surface that the repo skill routes to. Use it when you need exact entry points, output names, or method families.

## Top-level functions

- `fastdup.create(work_dir=None, input_dir=None)`
  - Returns a `Fastdup` object with a `.vis` gallery helper.
  - Use this for the object-oriented workflow.

- `fastdup.run(...)`
  - One-shot run that computes features, nearest neighbors, similarity/outlier outputs, and connected components.
  - Key controls: `input_dir`, `work_dir`, `test_dir`, `num_images`, `distance`, `threshold`, `lower_threshold`, `model_path`, `run_mode`, `nn_provider`, `bounding_box`, `turi_param`, `verbose`.

- `fastdup.remove_duplicates(input_dir, work_dir=None, distance=0.96, dry_run=False, license="")`
  - Convenience helper for duplicate removal from disk.
  - Internally runs fastdup, collects components, and deletes matching files unless `dry_run=True`.

- `fastdup.save_binary_feature(save_path, filenames, np_array, save_prefix="")`
  - Writes `atrain_features.dat` and `atrain_features.dat.csv` for precomputed feature workflows.
  - `np_array` must be `float32` and row-aligned with `filenames`.

- `fastdup.load_binary_feature(filename, d=576)`
  - Reads the binary feature file and matching filename CSV.
  - `d` must match the feature width that was saved.

- `fastdup.init_search(k, work_dir, d=576, model_path=..., verbose=False, license="", store_int=0, turi_param="", threshold=0.7, high_accuracy=False)`
  - Prepares a search index for image or vector search.

- `fastdup.search(filename, img=None, verbose=False)`
  - Searches the current index for a query image.

- `fastdup.vector_search(filename="query_vector", vec=None, verbose=False)`
  - Searches using a feature vector instead of an image.

## Gallery helpers

- `fastdup.create_duplicates_gallery(...)`
- `fastdup.create_duplicate_videos_gallery(...)`
- `fastdup.create_outliers_gallery(...)`
- `fastdup.create_components_gallery(...)`
- `fastdup.create_component_videos_gallery(...)`
- `fastdup.create_kmeans_clusters_gallery(...)`
- `fastdup.create_similarity_gallery(...)`
- `fastdup.create_stats_gallery(...)`

These accept a work directory, a dataframe, or a CSV path and write HTML galleries.

## Object API

`Fastdup = fastdup.engine.Fastdup`

Key methods on the returned object:

- `fd.run(...)` for end-to-end analysis from an input folder or annotations dataframe.
- `fd.similarity()`, `fd.outliers()`, `fd.img_stats()`, `fd.connected_components()`.
- `fd.summary(...)` for a compact text summary.
- `fd.enrich(...)` and `fd.caption(...)` for model-assisted workflows.
- `fd.vis.duplicates_gallery(...)`
- `fd.vis.outliers_gallery(...)`
- `fd.vis.similarity_gallery(...)`
- `fd.vis.stats_gallery(...)`
- `fd.vis.component_gallery(...)`

## Common result files

- `similarity.csv`
- `outliers.csv`
- `stats.csv`
- `component_info.csv`
- `connected_components.csv`
- `features.dat`
- `features.dat.csv`
- `features.bad.csv`
- `nnf.index`
- `config.json`
- `galleries/*.html`

## Notes

- The repo docs describe fastdup as CPU-only for ordinary usage.
- `fd.vis.*` methods are the preferred way to generate gallery HTML from a completed run.
