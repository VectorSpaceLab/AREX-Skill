# ESPnet3 Stage Runner

ESPnet3 templates use a Python stage runner rather than ESPnet2 shell recipes. The ASR template stage order is:

```text
create_dataset -> train_tokenizer -> collect_stats -> train -> infer -> measure -> pack_model -> upload_model -> pack_demo -> upload_demo
```

`--stages all` expands to the default ordered list. A user can request a subset, for example:

```bash
python run.py --stages infer measure --inference_config infer.yaml --metrics_config metrics.yaml --dry_run
```

## Required config flags

| Stage | Required config flags |
| --- | --- |
| `create_dataset`, `train_tokenizer`, `collect_stats`, `train` | `--training_config` |
| `infer` | `--inference_config` |
| `measure` | `--metrics_config` |
| `pack_model` | `--training_config`, `--publication_config` |
| `upload_model` | `--publication_config` |
| `pack_demo`, `upload_demo` | `--demo_config` |

Use the bundled stage inspector before launching stages:

```bash
python sub-skills/espnet3-workflows/scripts/inspect_espnet3_stages.py --stages infer measure --inference-config infer.yaml --metrics-config metrics.yaml --json
```

The inspector checks stage/config wiring only; it does not instantiate systems, load datasets, run inference, start demos, or upload artifacts.
