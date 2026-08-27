# Model tool troubleshooting

## Merge adapter

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `You must specify either --output_folder or --push_to_hub` | Neither local output nor Hub push was requested | Add `--output-folder merged-model` or `--push-to-hub`. |
| Base model fails to load | Wrong model id/path, private model without token, or remote-code restriction | Verify the base path and token; check whether the model requires remote code. |
| Adapter fails to load | Wrong adapter path or incompatible PEFT artifact | Confirm the adapter directory/repo contains PEFT adapter files compatible with the base model. |
| Out-of-memory during merge | Full base model is loaded before merge | Use a larger machine, smaller model, or CPU offload strategy outside this simple tool. |
| Pushed model lands in unexpected repo | Source tool pushes to the `adapter_path` repo when `--push-to-hub` is set | Prefer `--output-folder` first if you need to inspect the merged artifact before upload. |

## Kohya conversion

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Safetensors load fails | Input path is not a safetensors file or is corrupt | Verify `--input-path` and artifact type. |
| Conversion functions fail | State dict is not a LoRA state dict compatible with diffusers conversion helpers | Confirm the source LoRA format before retrying. |
| Output path cannot be written | Parent directory does not exist or permissions are wrong | Create the output directory and retry. |

## Environment checks

- `merge-llm-adapter` needs `torch`, `transformers`, and `peft`.
- `convert_to_kohya` needs `diffusers` and `safetensors`.
- Use the root install/backend checks before large merge jobs.

## Minimal recovery sequence

```bash
python skills/disco/autotrain-advanced/scripts/check_install.py
python skills/disco/autotrain-advanced/scripts/inspect_cli.py tools merge-llm-adapter --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py tools convert_to_kohya --help
```

Run large merge/conversion jobs only after inputs and output paths are explicit.
