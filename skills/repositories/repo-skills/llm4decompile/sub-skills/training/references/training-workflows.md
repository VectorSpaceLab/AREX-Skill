# Training Workflows

This sub-skill covers training and dataset-preparation flows for the LLM4Decompile model families.

## Route Summary

Use this route when the user wants to:

- fine-tune a checkpoint on the `decompile-ghidra-100k` or `llm4binary_v1` style data,
- prepare a training dataset from raw C sources,
- build continual-pretraining shards with ColossalAI,
- adjust or reuse the LLaMA-Factory YAML examples,
- diagnose DeepSpeed or multi-GPU training problems.

## Main Training Surfaces

### Raw supervised fine-tuning

`train/finetune.py` is the direct Transformers + DeepSpeed path.

Typical command shape:

```bash
deepspeed --master_port=11000 train/finetune.py \
  --model_name_or_path <base-model> \
  --data_path <training.json> \
  --output_dir <output-dir> \
  --num_train_epochs 1 \
  --model_max_length 4096 \
  --per_device_train_batch_size 16 \
  --gradient_accumulation_steps 16 \
  --bf16 True
```

Use this route when you want explicit control over the `transformers.Trainer` path.

### LLaMA-Factory fine-tuning

`train/llama_factory_llm4decompile/data/dataset_info.json` currently registers `llm4binary_v1`.
The example YAML files show the expected `pseudo2norm` and `norm2code` training shapes.

Typical command shape:

```bash
llamafactory-cli train train/llama_factory_llm4decompile/train/pseudo2norm-example.yaml
```

Use this route when the user specifically wants the repo's LLaMA-Factory integration or its dataset registry.

### Continual pretraining / spliced dataset prep

`train/colossalai_llm4decompile/prepare_pretrain_dataset.py` converts input JSONL collections into a spliced Arrow + JSONL layout for ColossalAI.

Typical command shape:

```bash
python train/colossalai_llm4decompile/prepare_pretrain_dataset.py \
  --data_input_dirs <comma-separated-jsonl-dirs> \
  --tokenizer_dir <tokenizer-path> \
  --data_output_dirs <output-dir> \
  --max_length 8192
```

Use this route when the user wants large-scale continual pretraining rather than supervised instruction tuning.

### AnghaBench-style dataset compilation

`train/compile.py` compiles source files at O0-O3 and writes JSONL records containing the input source and an optimization-level map of assembly outputs.

Typical command shape:

```bash
python train/compile.py --root <anghabench-root> --output <dataset.jsonl>
```

## Data Expectations

- `llm4binary_v1_example.json` is a JSON list with `instruction`, `input`, and `output` fields.
- `dataset_info.json` maps logical dataset names to example files.
- `compile.py` emits one JSONL record per C source file with a name, original source, processed source, and optimization-keyed assembly outputs.

## Decision Points

- Use the direct DeepSpeed path when the user wants code-level control or custom dataset handling.
- Use the LLaMA-Factory path when the user already has a dataset entry in `dataset_info.json` or wants the repo's example YAML structure.
- Use the ColossalAI path when the user wants the spliced pretraining pipeline.
- Use `compile.py` only when the user wants to derive a dataset from raw C sources.

## Read Next

- [`data-formats.md`](data-formats.md)
- [`troubleshooting.md`](troubleshooting.md)
- [`../../../references/model-overview.md`](../../../references/model-overview.md)
