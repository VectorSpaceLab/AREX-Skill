# TimeMixer Universal Task Workflows

This reference distills the non-forecast `run.py` branches into task-specific operating facts: which loader is used, which flags matter, how the model is called, and which outputs and metrics are written.

## Task and data compatibility

| Task | Compatible `--data` keys | Loader branch | Notes |
| --- | --- | --- | --- |
| Imputation | `ETTh1`, `ETTh2`, `ETTm1`, `ETTm2`, `custom`, `m4`, `PEMS`, `Solar` | Generic `data_provider(..., flag)` path | Uses `seq_len`, `label_len`, `pred_len`, `features`, `target`, `freq`, and `seasonal_patterns` from the CLI. |
| Anomaly detection | `PSM`, `MSL`, `SMAP`, `SMD`, `SWAT` | Special anomaly branch | Uses `win_size=args.seq_len` and dataset-specific file conventions. |
| Classification | `UEA` | Special classification branch | Uses UEA `.ts` files and a padding collate function. |

## Command generation contract

The bundled command builder prints a `python run.py ...` command and never launches training.

- `--task` maps to `--task_name`.
- `--no-use-gpu` is translated into a `CUDA_VISIBLE_DEVICES=""` shell prefix instead of `--use_gpu False`; the source parser types `use_gpu` as `bool`, so passing a literal `False` string would not disable CUDA reliably.
- For these non-forecast branches, the builder normalizes `pred_len=0` and `label_len=max(1, seq_len // 2)` so the command stays self-consistent.
- The builder sets `channel_independence=1` for imputation and anomaly detection, and `channel_independence=0` for classification to avoid the multivariate UEA embedding pitfall.
- `c_out` should match `enc_in` for imputation and anomaly detection because both branches reconstruct the input channel count.

## Imputation workflow

### Source path

- `run.py` routes `task_name=imputation` to `Exp_Imputation`.
- `data_provider.data_factory` uses the generic dataset classes, so the data key can be one of the forecasting-style loaders or `custom`, `m4`, `PEMS`, `Solar`.

### Core loop

1. Load `batch_x`, `batch_y`, `batch_x_mark`, `batch_y_mark` from the generic loader.
2. Replace zero entries in `batch_x` with the mean of the non-zero values in that batch.
3. Sample a random mask with shape `(B, T, N)` and convert values `<= mask_rate` to `0` and the rest to `1`.
4. Set masked entries to zero and call `self.model(inp, batch_x_mark, None, None, mask)`.
5. Slice the outputs with `f_dim = -1 if features == 'MS' else 0`.
6. Train and validate on `MSELoss(outputs[mask == 0], batch_x[mask == 0])`.

### Mask rate behavior

- `mask_rate` is a fraction, not a percent.
- `mask_rate=0.125` means roughly 12.5% of values are hidden.
- The loss is computed only on masked positions.
- If all values in a batch are zero or every value is masked, the batch mean/std can become invalid and propagate NaNs.

### Outputs and metrics

- Training/validation uses `torch.nn.MSELoss` on masked positions.
- Test metrics come from `utils.metrics.metric`, which returns `MAE`, `MSE`, `RMSE`, `MAPE`, and `MSPE`.
- The test routine writes:
  - `result_imputation.txt` at repo root
  - `results/<setting>/metrics.npy`
  - `results/<setting>/pred.npy`
  - `results/<setting>/true.npy`
  - PDF visualizations under `test_results/<setting>/` every 20 batches

## Anomaly detection workflow

### Source path

- `run.py` routes `task_name=anomaly_detection` to `Exp_Anomaly_Detection`.
- `data_provider.data_factory` selects one of the anomaly segment loaders:
  - `PSM`: `train.csv`, `test.csv`, `test_label.csv`
  - `MSL`: `MSL_train.npy`, `MSL_test.npy`, `MSL_test_label.npy`
  - `SMAP`: `SMAP_train.npy`, `SMAP_test.npy`, `SMAP_test_label.npy`
  - `SMD`: `SMD_train.npy`, `SMD_test.npy`, `SMD_test_label.npy`
  - `SWAT`: `swat_train2.csv`, `swat2.csv` with labels in the last column

### Core loop

1. Train the model as a reconstruction network on the training windows.
2. During test, compute point-wise reconstruction energies for the train split and the test split.
3. Concatenate train and test energies.
4. Compute the threshold with `np.percentile(combined_energy, 100 - anomaly_ratio)`.
5. Mark predictions where energy exceeds the threshold.
6. Run `utils.tools.adjustment(gt, pred)` to expand detections across contiguous anomaly segments.
7. Compute accuracy, precision, recall, and F-score.

### Anomaly ratio behavior

- `anomaly_ratio` is used as a percentile percentage in the threshold expression.
- The source comment says it is a percent value, so `25` means 25%, not 0.25.
- The default source value is `0.25`, which therefore means 0.25%.
- A too-small ratio makes the threshold overly strict; a too-large ratio makes the detector overfire.

### Outputs and metrics

- Training/validation uses `MSELoss` on the reconstructed window.
- Test prints and writes accuracy, precision, recall, and F-score.
- The test routine writes `result_anomaly_detection.txt` at repo root.
- `test_results/<setting>/` is created, but the source code does not save additional arrays there.

## Classification workflow

### Source path

- `run.py` routes `task_name=classification` to `Exp_Classification`.
- The UEA loader reads `.ts` files through `sktime.datasets.load_from_tsfile_to_dataframe`.
- `data_provider.data_factory` calls `UEAloader(root_path, flag=...)` with `flag='TRAIN'` or `flag='TEST'`.

### Loader and collate behavior

- The loader keeps all features, normalizes them, and subsamples variable-length series where needed.
- `max_seq_len` is taken from the longest series observed in the train/test pair.
- The collate function pads or truncates every batch to `max_len=args.seq_len`.
- The collate output is `(X, labels, padding_mask)`.
- `padding_mask` uses `1` for valid steps and `0` for padded steps.
- In the model, the padding mask is multiplied into the embeddings so padded positions are zeroed before flattening.

### Model and metric behavior

- `_build_model` sets:
  - `args.seq_len = max(train_data.max_seq_len, test_data.max_seq_len)`
  - `args.pred_len = 0`
  - `args.enc_in = train_data.feature_df.shape[1]`
  - `args.num_class = len(train_data.class_names)`
- The optimizer is `RAdam` and the loss is `CrossEntropyLoss`.
- Validation and test accuracy come from `softmax` + `argmax` + `utils.tools.cal_accuracy`.
- The source uses the test split for both validation and testing; there is no separate validation loader in the UEA path.

### Outputs

- `results/<setting>/result_classification.txt`
- `checkpoints/<setting>/checkpoint.pth`
- `test_results/<setting>/` is created but not populated by the source code.

## Result summary

| Task | Loss / score used in training | Final reported metrics | Text result file |
| --- | --- | --- | --- |
| Imputation | Masked `MSELoss` | MAE, MSE, RMSE, MAPE, MSPE | `result_imputation.txt` |
| Anomaly detection | Reconstruction `MSELoss` | Accuracy, precision, recall, F-score | `result_anomaly_detection.txt` |
| Classification | `CrossEntropyLoss` | Accuracy | `results/<setting>/result_classification.txt` |
