# Training/Evaluation/Inference Troubleshooting

- **`Config use_gpu cannot be set as true while using paddlepaddle cpu version`**: install a CUDA Paddle build or set `use_gpu=false` for CPU smoke checks.
- **Training downloads data unexpectedly**: the dataset reader could not find local data and called its download path. Stop and set explicit dataset paths or approve network access.
- **`Permission denied` or output overwrite confusion**: set a unique `save_dir`, `output_dir`, `output_eval`, or export directory outside protected paths.
- **Metrics are zero/NaN**: validate annotation schema, label order, `num_classes`, metric type, and whether predictions use the same category IDs as ground truth.
- **Resume does not continue expected epoch**: distinguish `-r/--resume` checkpoint paths from `-o weights=...`; resume is for training state, weights are for model parameters.
- **AMP/fleet/distributed hangs**: verify visible devices, Paddle CUDA build, NCCL/fleet environment, IP list, and port settings; retry on one GPU before distributed launch.
- **VisualDL or W&B errors**: VisualDL is a local dependency/log directory issue; W&B may require credentials and should not be enabled in unattended runs unless configured.
- **Slice inference misses or duplicates boxes**: check slice size, overlap ratio, combine method, match threshold, and match metric; compare with ordinary inference on a small image.
- **Remote weights fail to download**: use a local file or retry only after confirming the URL/version. Do not treat a network failure as a model/config failure.
