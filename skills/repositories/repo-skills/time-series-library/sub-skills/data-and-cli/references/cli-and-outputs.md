# CLI and Output Guide

## Minimal command skeleton

```bash
python -u run.py \
  --task_name long_term_forecast \
  --is_training 1 \
  --model_id tiny_custom \
  --model DLinear \
  --data custom \
  --root_path ./dataset/tiny-custom/ \
  --data_path tiny.csv \
  --features M \
  --target OT \
  --seq_len 8 --label_len 4 --pred_len 4 \
  --enc_in 3 --dec_in 3 --c_out 3 \
  --train_epochs 1 --batch_size 4 --num_workers 0 \
  --no_use_gpu
```

Required arguments are `--task_name`, `--is_training`, `--model_id`, `--model`, and `--data`. The rest depend on task/data/model.

## GPU controls

- `run.py` defaults to `use_gpu=True`; add `--no_use_gpu` for CPU.
- `--gpu_type cuda` selects CUDA when available; `--gpu_type mps` selects Apple MPS when available.
- `--gpu 0` chooses one GPU after `CUDA_VISIBLE_DEVICES` remapping.
- `--use_multi_gpu --devices 0,1,2,3` enables `nn.DataParallel` in model build.
- Upstream shell recipes often start with `export CUDA_VISIBLE_DEVICES=<id>`; treat that as a template value, not a safe default.

## Setting names

For most tasks, `run.py` builds a long `setting` string from task, model id, model, data, feature mode, sequence lengths, model dimensions, embedding/distilling flag, description, and iteration number. This setting determines checkpoint and result folder names.

MambaSingleLayer classification has a custom setting string that includes time-variant flags.

## Output folders and files

| Task | Main outputs |
| --- | --- |
| Long-term forecast | `checkpoints/<setting>/checkpoint.pth`, `test_results/<setting>/*.pdf`, `results/<setting>/metrics.npy`, `pred.npy`, `true.npy`, and `result_long_term_forecast.txt` |
| Zero-shot forecast | `test_results/<setting>/*.pdf`, `results/<setting>/metrics.npy`, `pred.npy`, `true.npy`, and `result_zero_shot_forecast_search.txt` |
| Short-term/M4 forecast | `checkpoints/<setting>/checkpoint.pth`, `test_results/<setting>/*.pdf`, `m4_results/<model>/<SeasonalPattern>_forecast.csv`; M4 averaged metrics print only after all six seasonal files exist |
| Imputation | `checkpoints/<setting>/checkpoint.pth`, `test_results/<setting>/*.pdf`, `results/<setting>/metrics.npy`, `pred.npy`, `true.npy`, `mask.npy`, and `result_imputation.txt` |
| Anomaly detection | `checkpoints/<setting>/checkpoint.pth`, `result_anomaly_detection.txt`, stdout threshold/accuracy/precision/recall/F-score |
| Classification | `checkpoints/<setting>/checkpoint.pth`, `results/<setting>/result_classification.txt`, stdout accuracy |

## Safe command-edit checklist

Before running a copied command:

1. Replace dataset paths with real local paths or validate that Hub download is intended.
2. Replace `CUDA_VISIBLE_DEVICES` and `--gpu` for the host.
3. Add `--no_use_gpu` for CPU smoke tests.
4. Reduce `--train_epochs`, `--batch_size`, `--seq_len`, and `--pred_len` for smoke tests.
5. Ensure `--enc_in`, `--dec_in`, and `--c_out` match the data columns.
6. Confirm optional model dependencies for `--model`.
