# Troubleshooting

## Fast checks

Run the bundled config inspector first when the problem looks structural. It can confirm the dataset tree, registry hits, and pipeline order without building the dataset or reading image files.

## Common failures

| Symptom | Likely cause | What to check | Fix |
| --- | --- | --- | --- |
| Labels look shifted or out of range | Class ids do not start at 0, or label ids do not match the class list | Annotation labels, `classes`, folder order | Renumber labels from 0 and make the class order explicit. |
| Annotation file is not found | `ann_file` is relative to the wrong root | `data_root` and the `ann_file` string | Keep `ann_file` relative to `data_root`, or make the path absolute and remove the root guesswork. |
| Images are not found | `data_prefix` points to the wrong directory or is missing | The sample paths after prefix resolution | Make `data_prefix` match the annotation file layout. |
| Labels are ignored or missing | `with_label` does not match the annotation format | Whether the annotation lines contain labels | Use `with_label=True` only when labels exist in the file; use `False` for image-only lists or scan-only folders. |
| Pipeline fails before augmentation | `LoadImageFromFile` is missing | The first pipeline step and the sample keys | Add `LoadImageFromFile` before crop/resize/augment steps when samples only store `img_path`. |
| A few files fail to decode | The image file exists but is unreadable or corrupted | Permissions, corruption, or a bad extension | Replace or repair the image, or remove the broken file. |
| `classes` and metadata do not match | `METAINFO/classes` is absent or ordered differently from the labels | `classes`, `metainfo`, or `categories` | Provide the correct class names and keep the label order fixed. |
| A custom type is not registered | The module was never imported, or another scope shadows the name | `custom_imports`, package import path, type name | Import the module before build time and use a unique type name if scopes may collide. |
| `Albumentations` fails to build | Optional dependency is missing | Whether the `albumentations` package is installed | Install the optional dependency or replace the transform with built-in alternatives. |

## Special notes

- Folder-scanned `CustomDataset` class ids follow sorted folder names, not folder creation order.
- `ImageNet` test data is label-free; the built-in dataset switches to image-only mode for that split.
- `PackInputs` should usually be the last step in a single-task classification pipeline.
- The config inspector is validation-only. It will not open image bytes or detect corruption inside the files themselves.

## When to route away

If the dataset and pipeline look correct but you now need to launch training, test the model, or resume a run, continue in `../training-and-evaluation/SKILL.md`.
