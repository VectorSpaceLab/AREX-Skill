# Training and data troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Manifest file not found or video missing | Wrong root or paths are not relative to `videos/` | Run the bundled validator, normalize paths, and verify a tiny sample before preprocessing. |
| Parquet schema mismatch | T2V/I2V fields or model-specific latent layout do not match | Confirm workload and model preset; regenerate precomputed data with the matching encoder/VAE configuration. |
| Decoder/codec import error | `torchcodec`, PyAV, torchvision, or ffmpeg variant absent | Install the decoder required by the selected loader; try a documented alternative and validate one file. |
| Preprocessing is unexpectedly slow/OOM | Too many workers, large video batch, resolution, or frame count | Reduce batch/workers/frames, use staged output, and check storage; do not launch full dataset encoding as a smoke test. |
| Trainer cannot parse config | Wrong schema version, missing required model/data fields, or wrong stack | Run `--dry-run`, inspect the config schema, and ensure the entry point matches modular versus legacy workflow. |
| Distributed initialization hangs | World-size/launcher mismatch, occupied port, or unavailable GPU count | Check `NUM_GPUS`, torchrun/Slurm allocation, ranks, and master port; test one process first. |
| OOM during training | Batch, resolution, model, optimizer, or validation too large | Use LoRA/sharding/checkpointing/accumulation or reduce dimensions; record the changed budget. |
| W&B/authentication failure | Online tracker requires credentials/network | Use offline mode for local debugging or configure credentials explicitly; never put keys in YAML or logs. |
| New code mixes train stacks | Forbidden cross-import | Move new methods/models to `fastvideo.train`; leave shipped legacy behavior in `fastvideo.training`. |
