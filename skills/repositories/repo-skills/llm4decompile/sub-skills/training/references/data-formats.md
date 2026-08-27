# Training Data Formats

## LLaMA-Factory example JSON

`train/llama_factory_llm4decompile/data/llm4binary_v1_example.json` is a JSON list.
Each item has:

- `instruction`: often empty for the repo example,
- `input`: prompt text containing assembly and the `# What is the source code?` suffix,
- `output`: target C snippet.

The matching registry entry in `dataset_info.json` is:

```json
{
  "llm4binary_v1": {
    "file_name": "llm4binary_v1_example.json"
  }
}
```

## Supervised fine-tuning JSON

`train/finetune.py` expects a JSON list of objects with at least:

- `instruction`
- `output`

The script constructs the prompt internally using the assembly banner and then tokenizes prompt + answer pairs.

## `compile.py` JSONL output

Each line is a JSON object with fields similar to:

- `name`: source file path,
- `input`: processed source used for training,
- `input_ori`: raw source,
- `output`: map from optimization state to assembly text.

The `output` object uses keys such as `opt-state-O0`, `opt-state-O1`, `opt-state-O2`, and `opt-state-O3`.

## ColossalAI pretraining shards

`prepare_pretrain_dataset.py` consumes JSONL files and emits:

- spliced JSONL shards,
- Arrow datasets under a `data_output_dirs` tree.

The script expects each input row to contain a tokenizable source/target pair after preprocessing by the ColossalAI dataset utilities.

## Practical validation checks

Before launching a long training job, verify:

1. The dataset file exists and is readable.
2. The dataset registry name matches the config or CLI argument.
3. The prompt template matches the model family.
4. The output directory does not already contain an unintended checkpoint unless resume behavior is desired.
