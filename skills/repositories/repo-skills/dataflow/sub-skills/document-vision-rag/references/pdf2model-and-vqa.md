# PDF2Model and PDF VQA

This note covers the CLI choices and dataset shapes for PDF-to-model and PDF VQA work.

## Decision matrix

| Need | Use | Why | Stop when |
| --- | --- | --- | --- |
| Set up a PDF VQA training path | `dataflow pdf2model init --qa vqa --train-backend base` | VQA only supports the base backend | the input is not a PDF manifest or the environment lacks the document pipeline dependencies |
| Set up PDF KBC training | `dataflow pdf2model init --qa kbc --train-backend base` or `dataflow pdf2model init --qa kbc --train-backend dataflex-less` | KBC is the only mode that can use DataFlex backends | `qa` is not `kbc`, or the DataFlex backend is unavailable |
| Train an adapter | `dataflow pdf2model train` | launches the generated training config and writes adapter artifacts | `train_config.yaml` or the required runtime packages are missing |
| Chat with the trained adapter | `dataflow pdf2model chat` or `dataflow chat` | reuses the adapter and base model | adapter files or the base model cannot be resolved |

## CLI catalog

| Command | Purpose | Side effects |
| --- | --- | --- |
| `dataflow pdf2model init` | initialize the pdf2model workspace | copies a customizable pipeline script, writes `.cache/train_config.yaml`, and records state for later training |
| `dataflow pdf2model train` | run the training job | may launch `torchrun`, writes adapter checkpoints under `.cache/saves/`, and can create DataFlex sidecar YAML files when the DataFlex backend is chosen |
| `dataflow pdf2model chat` | open a chat session with a trained adapter | resolves the base model, verifies adapter files, and launches chat |
| `dataflow chat` | auto-detect a base model or adapter and dispatch to the right chat path | may call the pdf2model chat bridge or `llamafactory-cli chat` |

## Mode-specific input contracts

### PDF VQA path

- The manifest uses `input_pdf_paths` plus `name`.
- `input_pdf_paths` may be a string or a list of strings.
- The local paths should point at PDFs.
- The downstream data shape is ShareGPT-style: `messages` and `images`.
- This path is not CPU-verified for OCR or VLM behavior.

### KBC path

- The source manifest usually uses `source` rows for the document URLs or local files.
- KBC output is later reshaped to Alpaca-style `instruction`, `input`, `output` rows.
- `input` may be empty, but the column should still exist when you are validating a training dataset.

### pdf2model training datasets

- KBC training expects `instruction`, `input`, `output`.
- VQA training expects `messages`, `images`.
- Those are the rows that the validator script should check when you pass a JSON or JSONL file.

## Generated artifacts to expect

- `.cache/train_config.yaml`
- `.cache/pdf2model_state.json`
- `.cache/data/qa.json`
- `.cache/data/dataset_info.json`
- `.cache/saves/pdf2model_cache_<timestamp>`
- When a DataFlex backend is chosen, also expect DataFlex YAML sidecars and a backend-specific output folder name.

## Backend rules

- `qa=vqa` only allows `--train-backend base`.
- `dataflex-*` backends are only valid when `qa=kbc`.
- The known DataFlex backend in this tree is `dataflex-less`.
- Do not assume a CPU-only environment can verify VLM, OCR, or distributed training behavior.

## Minimal command sequence

```bash
dataflow pdf2model init --qa kbc --train-backend base
dataflow pdf2model train
dataflow pdf2model chat
```

```bash
dataflow pdf2model init --qa vqa --train-backend base
```

## Stop conditions

- Stop if the base model cannot be resolved from the training config or adapter metadata.
- Stop if the expected adapter files are missing in the saved model folder.
- Stop if the selected backend is incompatible with the chosen `qa` mode.
- Stop if the training backend needs packages or hardware that are not installed.
