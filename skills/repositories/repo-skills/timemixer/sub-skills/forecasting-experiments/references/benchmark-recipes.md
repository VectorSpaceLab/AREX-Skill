# Benchmark Recipes

These recipes are distilled from TimeMixer's maintained forecasting command families into self-contained presets. They are command-construction evidence, not permission to run expensive experiments. Full benchmark training requires external datasets and user approval.

## Long-term forecasting presets

Common long-term settings unless overridden: `task_name=long_term_forecast`, `is_training=1`, `model=TimeMixer`, `features=M`, `label_len=0`, `des=Exp`, `itr=1`, `down_sampling_method=avg`, `seq_len=96`, and prediction lengths usually `96, 192, 336, 720`.

| Preset | Data flag | Data file | Channels (`enc_in/dec_in/c_out`) | Pred lengths | Main hyperparameters | Safety notes |
| --- | --- | --- | --- | --- | --- | --- |
| `ettm1` | `ETTm1` | `ETTm1.csv` under an ETT-small data directory | `7/7/7` (`dec_in` is an explicit form of the CLI default) | `96, 192, 336, 720` | `e_layers=2`, `d_model=16`, `d_ff=32`, `batch_size=16`, `learning_rate=0.01`, `down_sampling_layers=3`, `down_sampling_window=2` | External ETT dataset; expensive full training. |
| `etth1` | `ETTh1` | `ETTh1.csv` under an ETT-small data directory | `7/7/7` | `96, 192, 336, 720` | `e_layers=2`, `d_model=16`, `d_ff=32`, `batch_size=128`, `learning_rate=0.01`, `train_epochs=10`, `patience=10`, `down_sampling_layers=3`, `down_sampling_window=2` | External ETT dataset; benchmark run cost. |
| `etth2` | `ETTh2` | `ETTh2.csv` under an ETT-small data directory | `7/7/7` | `96, 192, 336, 720` | `e_layers=2`, `d_model=16`, `d_ff=32`, `batch_size=16`, `learning_rate=0.01`, `down_sampling_layers=3`, `down_sampling_window=2` | External ETT dataset; uses default `train_epochs=100` and `patience=15` unless overridden. |
| `ettm2` | `ETTm2` | `ETTm2.csv` under an ETT-small data directory | `7/7/7` | `96, 192, 336, 720` | `e_layers=2`, `d_model=32`, `d_ff=32`, `batch_size=128`, `learning_rate=0.01`, `down_sampling_layers=3`, `down_sampling_window=2` | External ETT dataset; uses default `train_epochs=100` and `patience=15` unless overridden. |
| `ecl` | `custom` | `electricity.csv` under an electricity data directory | `321/321/321` | `96, 192, 336, 720` | `e_layers=3`, `d_layers=1`, `factor=3`, `d_model=16`, `d_ff=32`, `batch_size=32`, `learning_rate=0.01`, `train_epochs=20`, `patience=10`, `down_sampling_layers=3`, `down_sampling_window=2` | External electricity/ECL CSV; channel count must match CSV value columns. |
| `traffic` | `custom` | `traffic.csv` under a traffic data directory | `862/862/862` | `96, 192, 336, 720` | `e_layers=3`, `d_layers=1`, `factor=3`, `d_model=32`, `d_ff=64`, `batch_size=8`, `learning_rate=0.01`, `down_sampling_layers=3`, `down_sampling_window=2` | Large multivariate CSV; high memory pressure and long runtime. |
| `weather` | `custom` | `weather.csv` under a weather data directory | `21/21/21` | `96, 192, 336, 720` | `e_layers=3`, `d_layers=1`, `factor=3`, `d_model=16`, `d_ff=32`, `batch_size=128`, `learning_rate=0.01`, `train_epochs=20`, `patience=10`, `down_sampling_layers=3`, `down_sampling_window=2` | External weather CSV; verify `date` plus 21 value columns. |
| `solar` | `Solar` | `solar_AL.txt` under a solar data directory | `137/137/137` | `96, 192, 336, 720` | `e_layers=3`, `d_layers=1`, `factor=3`, `d_model=512`, `d_ff=2048`, `batch_size=32`, `learning_rate=0.001`, `train_epochs=10`, `patience=3`, `down_sampling_layers=2`, `down_sampling_window=2`, `use_norm=0`, `channel_independence=0` | External Solar text matrix; no calendar time marks are consumed. |
| `pems03` | `PEMS` | `PEMS03.npz` under a PEMS data directory | `358/358/358` | `12` | `e_layers=5`, `d_layers=1`, `factor=3`, `d_model=128`, `d_ff=256`, `batch_size=32`, `learning_rate=0.003`, `train_epochs=10`, `patience=10`, `down_sampling_layers=1`, `down_sampling_window=2`, `use_norm=0`, `channel_independence=0` | External PEMS `.npz`; no calendar time marks; MAE validation criterion. |
| `pems04` | `PEMS` | `PEMS04.npz` under a PEMS data directory | `307/307/307` | `12` | Same as `pems03` except channel count/file/model id. | External PEMS `.npz`; no calendar time marks; MAE validation criterion. |
| `pems07` | `PEMS` | `PEMS07.npz` under a PEMS data directory | `883/883/883` | `12` | Same as `pems03` except channel count/file/model id. | External PEMS `.npz`; large channel count can exceed memory. |
| `pems08` | `PEMS` | `PEMS08.npz` under a PEMS data directory | `170/170/170` | `12` | Same as `pems03` except channel count/file/model id. | External PEMS `.npz`; no calendar time marks. |

## M4 short-term forecasting presets

M4 uses `task_name=short_term_forecast`, `data=m4`, `features=M`, `enc_in=dec_in=c_out=1`, `e_layers=4`, `d_layers=1`, `factor=3`, `d_model=32`, `batch_size=128`, `learning_rate=0.01`, `train_epochs=50`, `patience=20`, `down_sampling_layers=1`, `down_sampling_window=2`, and `loss=SMAPE`. The experiment code derives `pred_len`, `seq_len`, and `label_len` from `seasonal_patterns`.

| Preset | Seasonal pattern | Derived `pred_len` | Derived `seq_len/label_len` | `d_ff` | Output forecast CSV | Safety notes |
| --- | --- | ---: | --- | ---: | --- | --- |
| `m4-yearly` | `Yearly` | 6 | `12/6` | 32 | `m4_results/TimeMixer/Yearly_forecast.csv` | External M4 files and long training. |
| `m4-quarterly` | `Quarterly` | 8 | `16/8` | 64 | `m4_results/TimeMixer/Quarterly_forecast.csv` | External M4 files and long training. |
| `m4-monthly` | `Monthly` | 18 | `36/18` | 32 | `m4_results/TimeMixer/Monthly_forecast.csv` | External M4 files and long training. |
| `m4-weekly` | `Weekly` | 13 | `26/13` | 32 | `m4_results/TimeMixer/Weekly_forecast.csv` | External M4 files and long training. |
| `m4-daily` | `Daily` | 14 | `28/14` | 16 | `m4_results/TimeMixer/Daily_forecast.csv` | External M4 files and long training. |
| `m4-hourly` | `Hourly` | 48 | `96/48` | 32 | `m4_results/TimeMixer/Hourly_forecast.csv` | External M4 files and long training. |

M4 averaged metrics are only computed after all six seasonal forecast CSVs exist for the same model output directory. One seasonal command alone should be treated as partial evaluation.

## Preset adaptation rules

- For multivariate `features=M`, set `enc_in`, `dec_in`, and `c_out` to the number of value channels the loader returns. For ETT/ECL/Traffic/Weather/Solar/PEMS benchmark presets, this is the channel count in the table.
- For univariate `features=S`, set all three channel fields to `1` and set `target` to the desired column.
- For multivariate-to-univariate `features=MS`, use `enc_in`/`dec_in` for all input value channels and treat `c_out` with care. The custom CSV loader moves the target column to the final data column, but the inspected long-term non-AMP path does not consistently slice `outputs` and `batch_y` after computing the MS feature index. Prefer `features=M` or `features=S` unless an approved tiny run verifies the intended MS dimensions.
- PEMS and Solar return placeholder zero marks and the forecasting experiment passes `None` marks to the model, so changing `freq` does not add time features for those data flags.
- The command builder emits explicit channel dimensions for clarity even when a source preset relied on a `run.py` default.
- Reducing `train_epochs`, `batch_size`, or adding CPU fallback changes benchmark comparability. Mark such commands as debug/adaptation commands, not reproduced benchmark results.

## Safety skip notes

- Do not call maintained shell benchmark scripts directly from the skill workflow. Use the bundled command builder to print an auditable `run.py` command.
- Do not run full benchmark training, dataset downloads, or M4 all-season evaluation unless the user explicitly approves external data use and runtime cost.
- For verification or debugging, prefer command-builder help/JSON checks and tiny synthetic data checks owned by the data-preparation sub-skill.
