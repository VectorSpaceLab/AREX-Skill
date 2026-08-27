# Model And Backend Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named 'tf_keras'` | TensorFlow/Keras compatibility requirement. | Install `tf-keras` or use a compatible stack. |
| `Invalid model_name passed` or `unimplemented task` | Wrong model/task identifier. | Check `references/api-reference.md` or run the inventory helper. |
| Optional detector import error | Additional detector dependency missing. | Install only the package required by the requested detector. |
| Weight download/load failure | Network blocked, interrupted download, or wrong cache file. | Ask before retrying network or deleting a specific cached weight. |
| CUDA not used | CPU-only framework wheel, driver/runtime mismatch, or CUDA not required. | Use CPU unless acceleration is required; otherwise verify a compatible accelerator stack. |
| Encrypted embedding not returned | Embedding has negative values or lacks L2 normalization. | Set `minmax_normalize=True` and `l2_normalize=True` where suitable. |
