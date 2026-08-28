# Evaluation and performance troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Metric import failure | Missing optional evaluation extra or incompatible package | Identify the exact metric's dependency group, install only that group, and rerun `eval list`. |
| Reference/media decode failure | Missing file, codec, PyAV/ffmpeg issue, or wrong shape | Validate paths and codecs with a tiny sample; record skipped files and use a supported decoder. |
| Benchmark reports implausibly fast time | Load/compile/warmup excluded or request was not actually processed | Verify server responses and output count; state exactly what timing includes. |
| Compile appears slower | Warmup included or shapes changed | Warm up and discard first run; repeat with identical shapes and fixed config. |
| Scores differ after backend change | Numerics, seed, precision, or resolution changed | Re-run baseline/candidate with fixed controls and report tolerance rather than assuming backend equivalence. |
| Server benchmark cannot connect | Wrong host/port, server not healthy, or route mismatch | Check `/health`, use the actual base URL, and verify task/request type before increasing concurrency. |
| Judge metric asks for a key | Remote evaluator is credentialed | Stop the local smoke, obtain explicit credentials/authorization, and isolate the remote run. |
