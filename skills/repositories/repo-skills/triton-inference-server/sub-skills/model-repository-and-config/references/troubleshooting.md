# Model Repository Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Model is `UNAVAILABLE` at startup | Missing backend file, invalid config, bad version directory, or wrong model name | Run the validator and compare the config against backend docs. |
| Config parse fails | Missing required fields, invalid dims, unsupported backend syntax, or mismatch between model name and directory | Fix the `config.pbtxt` and re-run static validation before starting Triton. |
| CPU launch cannot load model | Model/backend requires GPU or unavailable accelerator | Route to runtime planning and confirm a CPU-compatible model/backend first. |
| `--load-model=*` plus another model name errors | Invalid startup flag combination | Use `*` alone or list explicit model names. |
| Poll mode reload surprises | Incomplete repository edits or non-atomic config/file changes | Stage the update in a separate directory and swap atomically. |
| Model update behaves inconsistently | Files modified while model is loading or backend libraries changed in place | Wait for the load cycle to finish, then stage changes carefully and reload. |
