# Text2Model workflow

`dataflow text2model` is the text-to-QA and adapter-training path. It is useful when you want to turn local text files into QA-style supervision and then train a LlamaFactory adapter.

## What the workflow expects

- Local JSON or JSONL files in the working directory
- A `text` field for the merge stage
- Enough disk space for `.cache/` output
- A model backend available for the text-to-QA stage

## CLI stages

| Stage | What it does | Main files | Side effects |
| --- | --- | --- | --- |
| `dataflow text2model init` | Verifies the environment, copies the editable `text_to_qa_pipeline.py`, and writes a default training config | `.cache/train_config.yaml` | May require `llamafactory` and `pyyaml` |
| `dataflow text2model train` | Merges local JSON/JSONL inputs, runs text-to-QA generation, converts QA to LlamaFactory format, and starts training | `.cache/gpu/text_input.jsonl`, `.cache/gpu/text2qa_step_step3.json`, `.cache/data/qa.json`, `.cache/data/dataset_info.json` | Can download a local model, launch vLLM, and start training |
| `dataflow chat` | Opens the latest adapter or base model if available | `.cache/saves/text2model_cache_<timestamp>` | Starts an interactive chat session |

## File contracts

### Input merge stage

The merge stage creates a compact JSONL file that feeds the QA generator.

Expected minimum field:
- `text`

Recommended extra fields:
- `source`
- `lang`
- `topic`
- `id`

### QA conversion stage

The conversion stage writes a LlamaFactory-compatible dataset.

`qa.json` rows should look like:
- `instruction`
- `input`
- `output`

`dataset_info.json` maps those fields to:
- `prompt` -> `instruction`
- `query` -> `input`
- `response` -> `output`

## Editable script

The generated `text_to_qa_pipeline.py` is the main customization point.

Use it when you need to:
- change the text chunking policy
- change the local model name or serving settings
- adapt the QA extractor to a different response shape
- tune the post-processing before `qa.json` is created

## Safe adaptation rules

- Keep the stage order: merge -> QA generation -> QA conversion -> training.
- Keep the conversion schema stable unless you also update the training config.
- Do not run the training stage until the generated `qa.json` has the expected columns and at least one sample.
- Treat `.cache/` as disposable runtime state, not as source data.

## Practical warnings

- The QA generation stage is model-backed and usually downloads or loads a local model.
- The training stage is side-effecting and may take a long time.
- If you are only validating the workflow shape, stop after the merge or QA conversion stage.
- Run from the directory that holds the input JSON / JSONL files unless you intentionally rewrite the helper scripts.
