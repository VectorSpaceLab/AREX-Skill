# xparl Troubleshooting

## Purpose

Use this reference to diagnose common PARL distributed execution failures. Start
with the safe CLI checker, then narrow by symptom. Do not start or stop cluster
processes as a default diagnostic unless the user has explicitly approved that
operation.

```bash
python scripts/check_xparl_cli.py
```

## Symptom matrix

| Symptom or error fragment | Likely cause | Recovery steps |
| --- | --- | --- |
| `xparl: command not found` | PARL package entry point is not installed in the active environment, or the environment is not on `PATH`. | Verify package installation and environment activation; run the bundled checker in `--mode module` only if PARL and its dependencies import correctly. Use `core-framework` for import/backend checks. |
| Import errors for serialization, ZeroMQ, gRPC, Requests, Click, Flask, protobuf, or PARL modules | Incomplete or incompatible PARL distributed dependencies. | Install/repair PARL's runtime dependencies in the intended environment. Keep master, workers, and clients aligned. Re-run help-only checks before starting a cluster. |
| `Client can not connect to the master` or worker says it cannot connect | Master not started, wrong `HOST:PORT`, blocked network, stale master, or untrusted/public routing blocked by policy. | Confirm `xparl start --port ...` is running on a trusted host; use a private address reachable by workers; check firewall/security group rules; avoid public exposure. |
| `Please input address in {ip}:{port} format` | `parl.connect` address is missing a host or port. | Use `parl.connect("localhost:6006")` or `parl.connect("MASTER_IP:PORT")`. |
| Assertion asking whether `parl.connect` was called | A decorated actor was created before a global client existed in that process. | Call `parl.connect(...)` before constructing any `@parl.remote_class` object. In multiprocessing code, connect in each process that creates remote actors. |
| `Only class can be decorated by parl.remote_class` | A function or non-class object was decorated. | Move remote behavior into a class and decorate the class. |
| Unsupported `@parl.remote_class` keyword | Keyword is not one of `max_memory`, `wait`, or `n_gpu`. | Remove or rename the argument; put application configuration in the actor constructor instead. |
| Remote method raises `RemoteError` or a future fails on `get()` | Exception occurred inside worker initialization or method execution. | Read the actor log URL or monitor job log. Reproduce locally by temporarily removing the decorator when safe, then redeploy. |
| No `print()` output appears in the client terminal | Actor code runs on worker processes. | Use the log URL emitted after `parl.connect` or the cluster monitor. For quick logic debugging, run the class locally before redecorating. |
| `no local file is matched with ...` | A `distributed_files` glob matched nothing. | Fix the relative pattern and verify files exist before `parl.connect`. Use small explicit globs. |
| Remote worker cannot import a relative submodule | Only top-level `.py` files near the main script were sent by default. | Add the package/subdirectory to `distributed_files`, for example `distributed_files=["./policy/*.py", "./policy/*.ini"]`. |
| `Please do not distribute a file with absolute path` | `distributed_files` included an absolute path. | Use paths relative to the client working directory. Do not ship machine-specific absolute paths. |
| Version mismatch mentioning PARL and Python versions | Client and master environments disagree on PARL version or Python major/minor version. | Align PARL package version and Python major/minor across client, master, and workers before debugging user code. |
| Master, monitor, or log-server port already in use | Chosen port conflicts with another service or stale xparl process. | Pick explicit free ports; avoid overlapping master, monitor, and log ranges. If a stale xparl process is confirmed, coordinate before `xparl stop`. |
| Log server fails to start | Port range invalid, ports unavailable, local HTTP blocked, or worker startup failed. | Use `--log_server_port_range START-END` with a private free range; avoid the master and monitor ports; inspect worker startup logs. |
| Monitor fails to start or status has no monitor URL | Monitor port conflict or monitor subprocess failed. | Provide `--monitor_port` explicitly; verify local host policy allows the HTTP monitor; retry only after cleaning stale processes. |
| `CPU` or `GPU` request rejected | Cluster mode does not match actor resource request, or insufficient resources are available. | Use CPU actors (`n_gpu=0`) on CPU clusters and GPU actors on `--gpu_cluster`; add workers or reduce `n_gpu`. |
| Remote calls appear to hang waiting for resources | No vacant CPU/GPU job slots or dead worker heartbeat. | Reduce actor count, add trusted workers, check monitor worker status, and clean stale dead workers after approval. |
| Large arrays or custom objects are slow or fail to serialize | Payload too large or not reliably serializable across workers. | Prefer native Python types and NumPy arrays; send small configs via `distributed_files`; avoid large model/data payloads in method arguments. |
| Stale xparl processes after interruption | Ctrl-C, notebook restart, or network failure left local master/worker/job/monitor/log processes. | Use `xparl status` to inspect. Run `xparl stop` only on the affected host and only after confirming no other trusted job depends on those processes. |

## Triage order for future agents

1. Read the safety gate in `security-and-operations.md`.
2. Run the help-only checker. If CLI/imports fail, fix the environment before
   starting processes.
3. For code failures, confirm `parl.connect` is called before actor creation and
   that `distributed_files` contains all relative submodules/configs.
4. For cluster failures, verify private network reachability and port choices.
5. For runtime exceptions, read remote logs rather than relying on local stdout.
6. For resource failures, check CPU/GPU cluster mode and worker availability.
7. Stop or kill processes only after explicit approval and host-local impact
   review.
