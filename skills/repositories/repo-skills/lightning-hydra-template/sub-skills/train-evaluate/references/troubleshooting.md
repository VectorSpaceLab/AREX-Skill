# Training and Evaluation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Eval exits with missing value or assertion | `configs/eval.yaml` requires `ckpt_path`. | Pass `ckpt_path=/path/to/checkpoints/last.ckpt`; verify the file exists and matches the model/data config. |
| Test after training uses current weights | `trainer.checkpoint_callback.best_model_path` is empty. | Ensure `callbacks=default` or a checkpoint callback is enabled and its monitor metric exists. |
| `ModelCheckpoint` monitor not found | Custom model does not log the callback monitor key. | Update callback `monitor` or log the expected metric in the LightningModule. |
| `Metric value not found` after training | `optimized_metric` does not match a metric in `trainer.callback_metrics`. | Use `val/acc_best` only for the default MNIST module or update `hparams_search`/model logging together. |
| Online logger import or auth failure | Optional logger package or token is missing. | Use `logger=null`/`logger=csv` for smoke; install the specific logger and configure env vars only for real runs. |
| Training downloads data unexpectedly | MNIST datamodule downloads in `prepare_data()`. | Use config instantiation or `pytest tests/test_configs.py` for no-network smoke; allow network/cache before training. |
| Batch size divisibility error | DataModule divides batch size by `trainer.world_size`. | Make `data.batch_size` divisible by total devices/processes. |
| DDP hangs or fails on local machine | Multiprocessing, data download, logger, or CUDA environment issue. | First run CPU config checks, then `trainer=ddp_sim`, then real `trainer=ddp` only with GPUs/data/loggers ready. |
| Checkpoints are not where expected | Hydra changed the output working directory. | Inspect `${paths.output_dir}` in the composed config or the terminal output path logged by `task_wrapper`. |
| Resume does not reconnect the logger run | Template notes logger experiment resume is not supported by current Lightning behavior. | Resume weights with `ckpt_path`; configure logger run IDs separately only if the logger supports it. |

## Safe fallback commands

```bash
# Inspect only.
python <this-skill>/scripts/check_lightning_hydra_project.py --repo-root . --config-name train.yaml --instantiate

# Minimal debug training, if data/cache/network is acceptable.
python src/train.py debug=fdr logger=null callbacks=null

# Evaluation from checkpoint without online logger.
python src/eval.py ckpt_path=/path/to/checkpoints/last.ckpt logger=null
```
