# Data Preparation Troubleshooting

- **Images are missing**: resolve `dataset_dir` plus `image_dir`/`file_name` exactly as the reader does; check case sensitivity and symlinks.
- **COCO `KeyError: image_id/category_id`**: validate IDs and ensure every annotation points to an image/category entry. Do not use one-based category assumptions without checking the config reader.
- **VOC produces zero objects**: check XML label names, box ordering, and the selected `label_list.txt`; corner coordinates must be inside the image.
- **Wrong mAP or all predictions are background**: compare `num_classes`, class order, category IDs, and `use_default_label`/label-list settings.
- **MOT identities are wrong**: verify normalized coordinates, class ID 0 convention, identity numbering, and `images` to `labels_with_ids` path substitution.
- **Keypoint metrics are implausible**: verify joint order, visibility values, person boxes, and whether the selected top-down/bottom-up reader matches the annotation format.
- **`Unable to use sahi`**: install `sahi` only for selected slicing workflows, or disable slicing and use ordinary inference. A missing optional dependency is not a data corruption signal.
- **x2coco output is empty**: inspect the converter's dataset-type value, JSON/image filename alignment, label mapping, and split proportions; run the bundled validator on the output before training.
- **Data download repeatedly fails**: stop retrying if the URL/cache/version is wrong. Acquire the data separately with approval, verify the archive, and point the config at the local root.
