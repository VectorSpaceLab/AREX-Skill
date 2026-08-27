# Training and alignment troubleshooting

## Dataset schema errors

These come from the dataset validators and usually mean the input file or dict does not match the expected training mode.

### Text fine-tuning

- `The dataset should have a train split`
- `The dataset should have a column named text`
- `The dataset should have a column named target if there is more than one column`
- `The dataset should have only two columns, text and target`

Fix: provide a train split and only the columns required by `TextDataset`.

### Instruction fine-tuning

- `The dataset should have a train split`
- `The dataset should have a column named text`
- `The dataset should have a column named target`
- `The dataset should have a column named instruction`
- `The dataset should have only three columns, instruction, text and target`
- `The jsonl file should have keys text, instruction and target`

Fix: normalize the schema to `instruction`, `text`, `target` with no extra columns.

### Preference / DPO fine-tuning

- `The dataset should have a train split`
- `The dataset should have a column named prompt`
- `The dataset should have a column named chosen`
- `The dataset should have a column named rejected`
- `The dataset should have only three columns: prompt, chosen, and rejected`
- `The jsonl file should have keys: prompt, chosen, and rejected`
- `Please provide a PreferenceDataset for DPO training`

Fix: use `PreferenceDataset` and rename any alternative keys such as `accepted`, `response`, or `negative` before calling `model.dpo_finetune(...)`.

## Quantization and hardware issues

### CPU + int8

- `Int8 models are not supported on CPU`

Fix: move to a CUDA-backed environment or switch to a non-int8 model variant.

### 8-bit LoRA without bitsandbytes

- To use Lora with 8-bit quantization, install the `bitsandbytes` package. You can install it with `pip install bitsandbytes`.

Fix: install the quantization backend that matches your platform and verify the package can load before launching training.

### k-bit / LoRA quantization on CPU

LoRA int8 and k-bit training are CUDA-oriented paths in this project. If you only have CPU, use a non-quantized model key instead.

## DeepSpeed and optimizer issues

### CPU Adam without DeepSpeed

- `DeepSpeed is required for optimizer 'cpu_adam'. Install it with \`pip install deepspeed\`.`

### LoRA / DeepSpeed path without DeepSpeed

- `use_deepspeed=True requires DeepSpeed. Install it with \`pip install deepspeed\`.`

Fix: either install DeepSpeed or choose a non-DeepSpeed configuration.

### Custom DeepSpeed config problems

If `deepspeed_config_path` points to a missing or invalid file, the trainer cannot build the strategy.

Fix: verify the JSON exists and is readable before starting training.

## LoRA target module mismatches

- `Target modules [...] not found in the base model. Please check the target modules and try again.`

Fix: choose module names that exist in the backbone. For Qwen3, the preset model key already wires the expected projection modules. For generic LoRA, adjust `target_modules` to match the architecture you are actually fine-tuning.

## Memory pressure

DPO keeps both the policy model and a frozen reference copy in memory. If you hit OOM:

- use a LoRA or k-bit variant
- reduce `batch_size`
- increase `gradient_accumulation_steps`
- shorten `max_length`
- prefer a smaller base model

## Save / reload mistakes

If a run saved a plain checkpoint without xTuring metadata, `BaseModel.load(...)` cannot infer the training preset from the directory alone.

Fix: save with `model.save(...)` from xTuring and reload from the saved output directory, or use the matching model class for a non-xTuring checkpoint.
