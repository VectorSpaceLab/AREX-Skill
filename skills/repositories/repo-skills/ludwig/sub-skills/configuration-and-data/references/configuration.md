# Ludwig Configuration

## Minimal ECD config

```yaml
model_type: ecd
input_features:
  - name: age
    type: number
  - name: segment
    type: category
output_features:
  - name: churn
    type: binary
trainer:
  train_steps: 1
  batch_size: 8
```

`model_type: ecd` handles the standard encoder-combiner-decoder path for tabular, text, image, audio, timeseries, vector, H3, and mixed data. Omit `model_type` only when defaults are acceptable for the installed version.

## LLM/VLM config keys

Common LLM sections include `model_type: llm`, `base_model`, `input_features`, `output_features`, `prompt`, `trainer`, `adapter`, `quantization`, and `backend`. LLM/VLM training often requires GPU memory, model access, tokenizer/model downloads, and optional extras. Treat these as training/backend decisions after the config shape is valid.

## Validation and schema tools

- `ludwig export_schema --model-type ecd` prints the JSON schema for ECD configs.
- `ludwig export_schema --model-type llm` prints the LLM schema.
- `ludwig render_config --config config.yaml --output rendered.yaml` fills defaults.
- `python scripts/validate_ludwig_config.py config.yaml` performs lightweight structure checks and, when Ludwig is installed, attempts model-config validation.

## Feature declarations

Every feature should have a `name` and `type`. Use `column` only when the dataset column differs from the logical feature name. Common input feature types include `number`, `category`, `binary`, `text`, `image`, `audio`, `sequence`, `set`, `bag`, `timeseries`, `date`, `h3`, and `vector`. Output feature types overlap but not every encoder/decoder combination is meaningful.

## Generated configs

`ludwig generate_config "task description"` asks an LLM provider for a config. Use it only when credentials and provider SDKs are configured. If the task must be offline, draft a config manually or use the bundled tiny config helper as a template.
