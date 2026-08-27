# Server CLI Reference

Main server command shape:

```bash
python -m petals.cli.run_server MODEL_ID [OPTIONS]
```

Key options:

- Model selection: positional `MODEL_ID` or `--converted_model_name_or_path`.
- Identity and public display: `--public_name`, `--identity_path`.
- Authentication: `--token` or `--use_auth_token`.
- Block ownership: `--num_blocks`, `--block_indices START:END`, `--dht_prefix`.
- Networking: `--port`, `--public_ip`, `--host_maddrs`, `--announce_maddrs`, `--initial_peers`, `--new_swarm`, `--skip_reachability_check`.
- Device/backend: `--device`, `--torch_dtype {auto,bfloat16,float16,float32}`, `--quant_type {none,int8,nf4}`, `--tensor_parallel_devices ...`, `--adapters ...`.
- Performance/cache: `--cache_dir`, `--max_disk_space`, `--throughput`, `--attn_cache_tokens`, `--max_chunk_size_bytes`, `--inference_max_length`, `--min_batch_size`, `--max_batch_size`, `--max_alloc_timeout`, `--stats_report_interval`.
- Config: `-c`/`--config` reads a config file.

Important parser conflicts and invariants:

- `--port` is a shortcut for default host multiaddrs; do not combine it with explicit `--host_maddrs`.
- `--public_ip` requires a fixed non-zero `--port` and conflicts with explicit `--announce_maddrs`.
- `--initial_peers` and `--new_swarm` are mutually exclusive.
- `--num_blocks` and `--block_indices` select different block strategies; do not pass both.
- CPU servers should pin `--device cpu`, `--torch_dtype float32` or `bfloat16`, and explicit block counts/ranges.

Use the bundled command builder to validate common combinations before launching anything.
