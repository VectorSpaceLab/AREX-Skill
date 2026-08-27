# Data and Config Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| YAML parse error | Bad indentation, tuple syntax, or unquoted value. | Run the config validator; compare the specific key with known FCOS config patterns. |
| `Non-existent config key` | Override key is misspelled or not present in YACS defaults. | Inspect `configuration.md`; use exact uppercase dotted keys. |
| `DATASETS.TEST` is empty or wrong | Config family not intended for the requested split or custom dataset not registered. | Set `DATASETS.TEST` explicitly and validate catalog registration/layout. |
| `Dataset not available` | Dataset key missing from `DatasetCatalog`. | Add the key in the target code or choose an existing COCO/VOC/Cityscapes key. |
| Annotation file missing | Directory layout does not match catalog paths. | Use `validate_dataset_layout.py` and fix symlinks/paths before running train/eval. |
| Class count mismatch | Custom dataset categories differ from COCO default 80 foreground classes. | Set `MODEL.FCOS.NUM_CLASSES` to foreground classes plus background and ensure downstream evaluators expect that mapping. |
| Deformable config fails | `dcnv2` config requires compiled deformable convolution support. | Verify extension/CUDA compatibility or choose a non-deformable config. |
