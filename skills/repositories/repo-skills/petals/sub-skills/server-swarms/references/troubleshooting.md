# Server and Swarm Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `--public_ip` rejected | missing fixed `--port` or conflicting announce args | use a non-zero port and no explicit announce multiaddrs |
| client sees no private blocks | mismatched `initial_peers`, `dht_prefix`, model id, or block range | compare server/client values and DHT readiness |
| identity collision | same identity file reused | give each peer its own identity unless intentionally stable |
| public reachability fails | firewall/NAT/port/relay issue | decide whether to use relay, public IP, or private swarm |
| cache fills disk | unlimited model/block cache | use `--cache_dir` and `--max_disk_space` |
| speedtest module error | wrong package named `speedtest` installed | install/use `speedtest-cli` expected by Petals |
| bitsandbytes setup fails | incompatible Torch/CUDA/Triton/bitsandbytes stack | use `--quant_type none` or repair backend versions |
| tensor parallel underperforms | uneven GPUs or unsupported model family | inspect devices and route internals to `distributed-blocks` |
| stale server ports | old DHT/server process survived | clean exact PIDs and verify ports before rerun |
