# CLI and config workflows

## Top-level command inventory

The inspected checkout registers these top-level CLI families:

- `app`
- `api`
- `llm`
- `setup`
- `text-classification`
- `image-classification`
- `tabular`
- `spacerunner`
- `seq2seq`
- `token-classification`
- `tools`
- `text-regression`
- `object-detection`
- `sentence-transformers`
- `image-regression`
- `extractive-qa`

`run_vlm.py` exists in the source tree, but the top-level CLI registration does not expose `autotrain vlm`; use app/API/config for VLM.

## Inspect a command safely

```bash
python skills/disco/autotrain-advanced/scripts/inspect_cli.py --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py llm --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py text-classification --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py tools merge-llm-adapter --help
```

The helper uses `python -m autotrain.cli.autotrain`, so it checks the package installed in the active Python environment.

## Config parser flow

1. Parse without running training:

   ```bash
   python skills/disco/autotrain-advanced/scripts/validate_config.py path/to/config.yml
   ```

2. Read the reported `task`, `backend`, and parsed keys.
3. Route to the owning sub-skill.
4. Use the owning sub-skill to validate task-specific data columns or image metadata.
5. Only after the user explicitly wants execution, run one of:

   ```bash
   autotrain --config path/to/config.yml
   autotrain <task-command> --train ...
   ```

## Task-to-owner mapping

| Parsed task / command | Owner |
| --- | --- |
| `llm`, `llm-sft`/`llm-dpo`/`llm-orpo`/`llm-reward`/`llm-generic`, app/API `llm:*` | `llm-training` |
| `text-classification`, `text-regression` | `text-and-tabular` |
| `token-classification` | `text-and-tabular` |
| `seq2seq` | `text-and-tabular` |
| `extractive-qa` | `text-and-tabular` |
| `sentence-transformers` / `st` | `text-and-tabular` |
| `tabular` | `text-and-tabular` |
| `image-classification` | `vision-multimodal` |
| `image-regression` / `image-scoring` | `vision-multimodal` |
| `object-detection` / `image-object-detection` | `vision-multimodal` |
| `vlm`, `vlm:*` | `vision-multimodal` through app/API/config |
| `app`, `api`, `spacerunner`, backend names | `app-backends` |
| `tools` | `model-tools` |

## Setup command behavior

`autotrain setup` has two meaningful flags in this checkout:

- `--colab`: installs `xformers==0.0.24`; without it, the command uninstalls `xformers`.
- `--update-torch`: installs `torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`.

Treat setup as a mutating environment operation, not a validation step.
