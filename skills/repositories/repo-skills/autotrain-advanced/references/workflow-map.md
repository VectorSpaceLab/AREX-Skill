# Workflow map

This repository exposes several distinct user-facing workflows. Use this map to choose the right sub-skill quickly.

| User request | Primary surface | Owning sub-skill | Notes |
| --- | --- | --- | --- |
| "Install AutoTrain Advanced" / "Why does import fail?" | package install and import | `cli-config` | Use the root install/check scripts first.
| `autotrain --help` / `--version` / `--config` | top-level CLI and config parser | `cli-config` | `autotrain --config` runs the config parser and task router.
| "Run AutoTrain LLM" / `autotrain llm` | LLM finetuning CLI | `llm-training` | Covers sft, orpo, dpo, reward, and generic LLM variants.
| "Train text classifier/regressor" | text CLI | `text-and-tabular` | Covers text, token, seq2seq, extractive QA, sentence-transformers, and tabular routes.
| "Train image classifier / detector" | vision CLI or config | `vision-multimodal` | Covers image classification, image regression, and object detection.
| "Run VLM" | app/API/config path | `vision-multimodal` | There is no top-level `autotrain vlm` command; use the UI/API/config flow.
| "Open the AutoTrain app" / "Run the API" | FastAPI service | `app-backends` | Covers the local UI, API, and hosted backends.
| "Launch on Spaces / endpoints / NGC / NVCF" | backend runners | `app-backends` | Includes `spacerunner` and the backend selection surface.
| "Merge adapter" / "Convert to Kohya" | utility commands | `model-tools` | Use for the two `autotrain tools` commands.

## Supported task families

- LLM finetuning: YAML aliases `llm-sft`, `llm-dpo`, `llm-orpo`, `llm-reward`, `llm-generic`; app/API keys `llm:sft`, `llm:dpo`, `llm:orpo`, `llm:reward`, `llm:generic`
- Text tasks: `text-classification`, `text-regression`, `token-classification`, `seq2seq`, `extractive-qa`
- Embeddings and tabular: `sentence-transformers`, `tabular`
- Vision tasks: `image-classification`, `image-regression`, `image-object-detection`, `vlm`
- Deployment/UI: `app`, `api`, `spacerunner`
- Utilities: `tools merge-llm-adapter`, `tools convert_to_kohya`

## Key exception

The VLM path is reachable from the app/API/config workflow and task registry, but not as a registered top-level CLI command. If a user says `autotrain vlm`, redirect them to `vision-multimodal` and `app-backends`.
