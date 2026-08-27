# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Unknown dataset type!` | the config uses an unsupported `data.*.name` | switch to `CocoDataset`, `XMLDataset`, or `YoloDataset` |
| `timm is not installed` | a backbone config uses `TIMMWrapper` | install `timm` before building the model |
| `num_classes` mismatch error | head class count does not match `class_names` | make the head config and class list agree |
| `FileNotFoundError` while loading data | annotation or image path is wrong | verify the config paths and the dataset layout |
| some XML/YOLO boxes disappear | class names or coordinates are invalid | fix the annotation contents or the config class list |
| model build downloads weights | config uses a pretrained backbone default | allow the download, cache it, or disable pretrained loading when offline |

## Recovery pattern

1. Load the config with the skill-owned config checker.
2. Inspect the dataset section and class list.
3. Build the model from the same config.
4. Run the dataset smoke helper against the real dataset layout.
