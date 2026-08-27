# TimeMixer data formats

This reference matches the dataset loaders used by the TimeMixer data provider.

## Time-feature conventions

| `timeenc` | Behavior | Shape |
| --- | --- | --- |
| `0` | Manual calendar fields are built from the `date` column. | `[rows, fields]` |
| `1` | `time_features(...)` is built from `freq` using pandas offsets. | `[rows, fields]` after transpose |

### Manual calendar fields
- Hourly CSVs: `month`, `day`, `weekday`, `hour`
- Minute CSVs: `month`, `day`, `weekday`, `hour`, `minute // 15`
- Custom CSVs reuse the same manual fields when `timeenc=0`

### Supported `freq` families for `time_features`
- `Y` yearly: no features
- `M` monthly: `MonthOfYear`
- `W` weekly: `DayOfMonth`, `WeekOfYear`
- `D` / `B` daily or business day: `DayOfWeek`, `DayOfMonth`, `DayOfYear`
- `H` hourly: `HourOfDay`, `DayOfWeek`, `DayOfMonth`, `DayOfYear`
- `T` / `min` minute: `MinuteOfHour`, `HourOfDay`, `DayOfWeek`, `DayOfMonth`, `DayOfYear`
- `S` secondly: `SecondOfMinute`, `MinuteOfHour`, `HourOfDay`, `DayOfWeek`, `DayOfMonth`, `DayOfYear`
- `ms` milliseconds: `MillisecondOfMinute`, `SecondOfMinute`, `MinuteOfHour`, `HourOfDay`, `DayOfWeek`, `DayOfMonth`, `DayOfYear`

Unsupported strings raise a runtime error from pandas frequency parsing.

## Dataset map

| Data key | Loader | Required files / columns | Split and shape behavior | Notes |
| --- | --- | --- | --- | --- |
| `ETTh1`, `ETTh2` | `Dataset_ETT_hour` | CSV with `date` plus numeric columns; default target `OT` | Fixed train/val/test split by row count: 12 months / 4 months / 8 months, with monthly windows approximated as 30 days. Sliding windows use `seq_len`, `label_len`, `pred_len`. | `features` can be `S`, `M`, or `MS`. `timeenc=0` uses manual hourly calendar fields; `timeenc=1` uses `freq='h'` or a compatible offset string. |
| `ETTm1`, `ETTm2` | `Dataset_ETT_minute` | CSV with `date` plus numeric columns; default target `OT` | Same split logic as hourly, but every count is multiplied by 4 because the source is 15-minute data. Sliding windows use `seq_len`, `label_len`, `pred_len`. | Manual time features include a 15-minute bucket via `minute // 15`. Default `freq='t'`. |
| `custom` | `Dataset_Custom` | CSV with a `date` column, a target column, and numeric feature columns | Row split is 70% train / 20% val / 10% test. The loader reorders columns to `date + other columns + target`. | `features='M'` or `MS` uses every non-date column; `S` uses the target only. The scaler is fit on train rows only. |
| `m4` | `Dataset_M4` | Directory containing `M4-info.csv`, `training.npz`, and `test.npz` | No row-based train/val/test split inside the loader. The `SP` column in `M4-info.csv` selects the seasonal subset. Each item samples a window from one series and pads with masks when needed. | Seasonal patterns are `Yearly`, `Quarterly`, `Monthly`, `Weekly`, `Daily`, `Hourly`. `pred_len` follows the seasonal horizon convention. No time marks are used. |
| `PEMS` | `Dataset_PEMS` | `.npz` file with a `data` array key | The loader reads `data['data'][:, :, 0]`, then splits rows 60% / 20% / 20%. Test windows advance by 12 rows at a time. | No time marks are used. `enc_in`, `dec_in`, and `c_out` must match the node/channel count after slicing. |
| `Solar` | `Dataset_Solar` | Plain text file where each line is a comma-separated list of floats | The file is read into a numeric matrix, then split 70% / 20% / 10% by rows. Sliding windows use `seq_len`, `label_len`, `pred_len`. | No date column and no time marks. Every row must already be numeric. |
| `PSM` | `PSMSegLoader` | `train.csv`, `test.csv`, `test_label.csv` | The first column is dropped from all three files. Train data fits the scaler; test data and labels are transformed or reused as needed. Sliding windows use `win_size` and `step=1`. | `test_label.csv` must align row-for-row with `test.csv` after the first column is dropped. |
| `MSL` | `MSLSegLoader` | `MSL_train.npy`, `MSL_test.npy`, `MSL_test_label.npy` | Train and test are loaded as arrays and standardized. Sliding windows use `win_size` and `step=1`. | Validation reuses the test split. |
| `SMAP` | `SMAPSegLoader` | `SMAP_train.npy`, `SMAP_test.npy`, `SMAP_test_label.npy` | Same behavior as MSL. | Validation reuses the test split. |
| `SMD` | `SMDSegLoader` | `SMD_train.npy`, `SMD_test.npy`, `SMD_test_label.npy` | Train and test are loaded as arrays and standardized. Validation is the last 20% of the train split. Train windows use `step=100`; val/test use the configured step. | Same label file naming convention as the other `.npy` anomaly loaders. |
| `SWAT` | `SWATSegLoader` | `swat_train2.csv`, `swat2.csv` | The last column is treated as the label column in the test file. Train and test features are standardized after dropping the last column. | Unlike PSM, there is no separate label file. |
| `UEA` | `UEAloader` | One valid `.ts` file per split, usually `*_TRAIN.ts` and `*_TEST.ts` | The loader searches the root directory for `.ts` files whose names match the requested flag. Variable-length series are supported and later padded or clipped by the collate function. | Relies on a valid UEA / sktime `.ts` archive format. Labels are encoded to integer class IDs. |

## Split and window reminders
- Forecasting loaders require enough rows for at least one window: `rows >= seq_len + pred_len`.
- Anomaly loaders require enough rows for at least one `win_size` window.
- `PEMS`, `Solar`, and custom CSVs do not create time marks from dates.
- `UEA` classification data is not forecasted; sequence length is handled by padding and collate logic instead of date features.

## Benchmark-specific conventions worth remembering
- ETT and custom CSVs rely on a `date` column.
- PEMS uses a `.npz` archive with a `data` key and channel count in the second dimension.
- Solar is a plain numeric matrix with no header.
- M4 is organized around seasonal-pattern subsets instead of row splits.
- UEA classification files are `.ts` archives, not CSV files.
