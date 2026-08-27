# Workflow overview

## 1. Dataset curation
Use this family when the goal is to audit or clean a visual corpus.

Typical sequence:
1. Create a dataset object with `fastdup.create(...)`.
2. Run `fd.run(...)` or `fastdup.run(...)` on a folder or file list.
3. Inspect `fd.similarity()`, `fd.outliers()`, `fd.img_stats()`, and `fd.connected_components()`.
4. Generate galleries with `fd.vis.*`.
5. Use `fastdup.remove_duplicates(...)` when you want the tool to delete or preview duplicates.

## 2. Structured labeled data
Use this family when the input already has annotations.

Typical sequence:
1. Build a dataframe with `filename`, `label`, `split`, and bbox columns as needed.
2. Run `fd.run(annotations=df_annot, ...)`.
3. Visualize with `fd.vis.component_gallery(...)`, `fd.vis.similarity_gallery(...)`, and `fd.vis.outliers_gallery(...)`.
4. Export to external tools only after the run succeeds.

## 3. Embeddings and search
Use this family when you want to reuse a feature representation or search over a corpus.

Typical sequence:
1. Save vectors with `fastdup.save_binary_feature(...)` or compute them with a model helper.
2. Run `fastdup.run(..., run_mode=2)` or the object API on a precomputed feature file.
3. Initialize search with `fastdup.init_search(...)`.
4. Query with `fastdup.search(...)` or `fastdup.vector_search(...)`.

## 4. Model enrichment
Use this family when you want captions, zero-shot labels, OCR, or open-vocabulary predictions.

Typical sequence:
1. Choose the model helper that matches the task.
2. Confirm the dependency set for that helper is installed.
3. Run the helper on a small subset before scaling up.
4. Keep the outputs in a dataframe and inspect the new columns before exporting.

## 5. Video and exchange
Use this family when the inputs are videos, archives, cloud paths, or when you need interchange with another tool.

Typical sequence:
1. Resolve the input source and any archive/cloud tooling first.
2. For videos, confirm ffmpeg and codec support.
3. For archives, decide whether the run should extract frames first or resume from stored features.
4. For CVAT/LabelImg/TensorBoard exports, write the helper outputs to a clean local directory.

## Known separation rules

- Local image cleanup and gallery generation belong to `dataset-curation`.
- Annotation schemas and dataset-source adapters belong to `structured-datasets`.
- Timm/ONNX/search/captions/zero-shot/OCR belong to `model-enrichment`.
- Video, tar/webdataset, cloud sync, and export plumbing belong to `media-and-exchange`.
