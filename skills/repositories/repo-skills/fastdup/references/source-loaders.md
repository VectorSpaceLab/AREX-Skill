# Source loader notes

This repo's dataset-source guidance is workflow-oriented rather than a single shared loader API. Use this self-contained summary to decide how to transform source-specific data into a fastdup-ready folder plus annotation dataframe.

## Source families

| Source family | What to prepare for fastdup | Common failure modes |
| --- | --- | --- |
| Hugging Face Datasets | materialize images to local files and build a dataframe with `filename` plus `label` when available | missing `datasets`, cache/network failure, or the helper import bug in this release line |
| Kaggle datasets | download or mount the image files locally, then build `filename`, `label`, and optional `split` columns from the dataset metadata | dataset access, cache, or download setup |
| Roboflow Universe | export/download the dataset into local image and annotation files, then normalize labels and bbox columns | network access, source package availability, or credential/setup issues |
| Labelbox | convert an exported Labelbox dataset into local image paths and label rows | credentials, download permissions, or export schema drift |
| TensorFlow Datasets | iterate the TFDS split, save image tensors to files, and build labels from the dataset features | missing `tensorflow_datasets`, cache, or network access |
| Torchvision | instantiate the dataset, copy or reference image files, and build labels from class indices | missing `torchvision` or a dataset download failure |

## Practical guidance

- Treat these as optional source adapters, not mandatory runtime dependencies for the core cleanup workflow.
- If the notebook source path is unavailable, fall back to a manually built annotation dataframe with `filename` and `label`.
- Prefer the manual dataframe path when the source package, cache, or dataset service is unstable.
