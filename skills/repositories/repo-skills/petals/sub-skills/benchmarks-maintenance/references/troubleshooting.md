# Benchmark and Maintenance Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| missing model/peer variables | distributed check lacks required context | set model id, reference id, optional adapter id, and private peer multiaddr |
| hang before model creation | download/auth/cache/DHT readiness | verify model access and private peers before execution |
| stale peers or ports | previous DHT/server survived | clean exact PIDs and verify ports |
| wrong speedtest module | package named `speedtest` shadows `speedtest-cli` | install expected `speedtest-cli` and remove wrong module |
| fork/multiprocessing issue | platform proxy/fork safety | use platform fork-safety env vars and external timeout |
| `n_processes=n_gpus` surprise | expands to visible CUDA device count | avoid for CPU smoke |
| tiny CPU numbers look poor | smoke is not performance benchmark | report as wiring health only |
| timeout | model download or remote retry loop | add explicit phase budgets and `PETALS_MAX_RETRIES` |
