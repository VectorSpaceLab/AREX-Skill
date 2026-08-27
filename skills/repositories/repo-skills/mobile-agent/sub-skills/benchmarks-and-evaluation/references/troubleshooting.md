# Benchmark Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| AndroidWorld cannot find adb | SDK path not in defaults | Pass `--adb-path`/`--adb-path-env` to the command builder and verify platform tools in the runtime env. |
| Emulator connection fails | Wrong console/grpc port or unauthorized device | Compare `adb devices` with `--console_port`; keep grpc port unique per emulator. |
| AndroidWorld resumes unexpectedly | Non-empty checkpoint directory | Use a clean checkpoint dir or intentionally resume from it. |
| No trajectory files | `--traj_output_path` omitted or unwritable | Provide a private output directory and check permissions before live run. |
| OSWorld does not start | VM path/service missing | Verify VM image, OSWorld setup, display automation service, and task metadata. |
| Web benchmark cannot log in | Missing prepared account/session | Stage cookies/accounts privately; do not embed secrets in commands. |
| Browser screenshots not accepted | Wrong image mode or missing OSS | Use `base64`/`file` where supported, or configure private OSS for `oss`. |
| Judge returns auth/model errors | Missing judge API key/base/model | Separate agent model endpoint from judge model endpoint and keep credentials in env vars. |
| GUI-Critic JSONL fails validation | Empty images, bad labels, missing sections, invalid JSON | Fix the row schema before inference; use validator output line numbers. |
| Grounding/knowledge eval OOM or missing model | Checkpoint/GPU stack unavailable | Treat as live backend skip unless the user provides checkpoint/GPU and asks to verify. |

Skipped benchmark execution is not a pass. Record `SKIP_UNSAFE` for missing live services or `BLOCKED_REQUIRED_BACKEND` if the user made that backend required.
