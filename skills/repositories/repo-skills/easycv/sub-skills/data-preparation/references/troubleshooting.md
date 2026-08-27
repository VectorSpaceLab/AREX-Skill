# Data-preparation troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `access_oss` fails | OSS credentials or endpoint configuration is missing | Configure OSS before any remote file access. |
| File list loads but training still fails | The data layout does not match the config's expected family | Re-check the dataset family and the required root / annotation paths. |
| TFRecord data does not load | The `.idx` files are missing or paired incorrectly | Keep each record and index file together. |
| COCO or VOC annotations are not found | The annotation directory name or split file is wrong | Compare the layout with the data-format reference. |
| Table mode cannot read the image column | The table schema or column names do not match the CLI arguments | Re-read the batch-prediction reference and fix the schema. |
| nuScenes prep is incomplete | The generated info files were not produced | Run the dataset helper and confirm the output files before training. |

## Recovery checklist

1. Decide which dataset family you are targeting.
2. Compare the current directory tree with the expected layout.
3. Confirm OSS or ODPS credentials if the data is remote.
4. Only then adjust the training or prediction command.

