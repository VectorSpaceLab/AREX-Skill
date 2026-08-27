# Data Troubleshooting

## Symptoms and likely causes

| Symptom | Likely cause | First check |
|---|---|---|
| Empty dataloader | wrong split file, class filtering, or point cloud range filters all samples | Inspect `DATA_SPLIT`, `ImageSets`/split files, `CLASS_NAMES`, `POINT_CLOUD_RANGE` |
| Missing info file error | dataset converter not run or `INFO_PATH` name mismatch | Check generated pickle names under the dataset root |
| Database sampler file missing | ground-truth database not generated or wrong `DB_INFO_PATH` | Confirm `*_dbinfos_*.pkl` and database object folder |
| Label/class mismatch | `CLASS_NAMES` differs from annotation labels or checkpoint classes | Compare config class list with annotation names and checkpoint origin |
| Waymo converter slow/fails | large raw sequences, too many workers, missing converted sequence folders | Reduce workers, verify raw/processed folders and disk space |
| NuScenes/Lyft metadata failures | wrong version folder or missing devkit metadata | Verify versioned folders and official metadata files |
| Argo2 import/conversion failure | incompatible kornia/av2 stack or wrong sensor layout | Runtime inspector and Argo2 layout checks |
| CustomDataset shape errors | point feature dimension or info schema mismatch | Validate point arrays and custom info fields |

## Safe sequence before training

1. Summarize the target config with the root config summarizer.
2. Check raw dataset layout with the sub-skill layout checker.
3. Generate infos/database products with a printed command first.
4. Re-check expected info/database products.
5. Only then launch train/test.

## Do not patch around missing data

Avoid setting paths to arbitrary existing folders just to pass file existence checks. OpenPCDet converters and dataloaders expect precise schema fields, split names, point shapes, labels, and calibration/metadata for each dataset.
