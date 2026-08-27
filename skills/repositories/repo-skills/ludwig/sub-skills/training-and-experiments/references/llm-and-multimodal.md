# LLM, VLM, and Multimodal Training Notes

## LLM config shape

Common LLM keys:

```yaml
model_type: llm
base_model: some/model
input_features:
  - name: prompt
    type: text
output_features:
  - name: output
    type: text
trainer:
  type: finetune
adapter:
  type: lora
quantization:
  bits: 4
backend:
  type: local
```

## Backend caveats

- Quantized LLM generation and many large model paths need CUDA GPU memory. CPU imports do not prove these workflows.
- Hugging Face models may require network, cache space, license acceptance, or tokens.
- PEFT, torchao, FAISS, accelerate, and related libraries may require `ludwig[llm]` or focused installs.
- Distributed LLM fine-tuning may require Ray/DeepSpeed/FSDP/Accelerate compatibility beyond the base package.

## Multimodal notes

Images, audio, timeseries, tabular, and text can be mixed with appropriate feature encoders. Media workflows often need file paths, decoding libraries, and memory planning. Use tiny fixtures first and do not run benchmark-scale examples as smoke tests.

## Alignment and preference training

Trainer types such as DPO, KTO, ORPO, and GRPO require data columns and prompt/output structures matching the selected trainer. Validate config/data columns before launching long runs.
