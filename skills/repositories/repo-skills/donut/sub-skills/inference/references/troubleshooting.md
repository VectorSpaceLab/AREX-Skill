# Troubleshooting

Use this guide for the inference CLI, prompt formatting, checkpoint loading, and Gradio launch problems.
It focuses on the failure modes that the bundled scripts can surface quickly.

## Quick diagnosis table

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError` for `torch`, `transformers`, `timm`, `gradio`, or `PIL` | The active environment does not have the Donut runtime stack | Activate the environment that has the Donut package and its dependencies installed before running the scripts. |
| `OSError`, `HFValidationError`, or a Hub download error during `from_pretrained` | The checkpoint ID is wrong, the network is unavailable, or the repo is gated | Verify the model ID, or point to a local checkpoint directory and use `--local-files-only`. |
| `FileNotFoundError` or an error about missing files in a local model path | The path is not a checkpoint directory | Point `--model` at the folder that contains the model config, tokenizer files, and weights. |
| The output is text but not the expected JSON structure | The prompt/task token family does not match the checkpoint | Use the exact task prompt the checkpoint was trained with, such as `<s_cord>` or the DocVQA question/answer template. |
| DocVQA output is wrong or empty | The question slot or answer slot is missing, or the checkpoint expects a different DocVQA prompt | Use `<s_docvqa><s_question>...</s_question><s_answer>` and keep the question text in the question tag. |
| The raw token string looks correct but JSON parsing is poor | The generated tokens do not match the JSON grammar the model learned | Inspect the raw output with `--raw-token`, then adjust the prompt rather than the decoder settings. |
| The GPU is available but you want a CPU fallback | The CLI auto-selected CUDA | Pass `--device cpu` to force float32 CPU inference. |
| `CUDA error` or `device not available` | The machine has no usable CUDA runtime even if the host has a GPU | Use `--device cpu`, or fix the CUDA/PyTorch installation first. |
| Gradio fails to start or says the address is already in use | Port conflict | Pick another `--port`. |
| The demo starts locally but is not reachable from another machine | The bind address is too narrow | Set `--host 0.0.0.0` and choose an open port. |
| The demo import fails before launch | `gradio` is missing or broken | Install or repair the runtime environment, then re-run the launcher help check. |

## Local checkpoint checklist

Before treating a local path as a usable Donut checkpoint, confirm that it is a checkpoint directory and not a single weight file.
A healthy directory should normally contain the model config, tokenizer assets, and weights file(s).

If you need an offline run, the safe pattern is:

```bash
python scripts/run_inference.py \
  --model /path/to/checkpoint \
  --image /path/to/document.png \
  --task cord \
  --local-files-only
```

## Prompt mismatch checklist

When the model loads but the result is wrong, check these in order:

1. Did you choose the correct task family for the checkpoint?
2. For DocVQA, did you provide a question text and the `<s_question>...</s_question>` wrapper?
3. Did you accidentally compare two prompt variants without noticing that one of them does not match the fine-tune family?
4. Does the checkpoint expect a custom task token rather than a generic one like `cord`?

If the answer to any of those is yes, fix the prompt first.
Do not try to solve a prompt mismatch by changing beam search or generation length first.

## CPU versus CUDA expectations

The inference path is intentionally asymmetric:

- CUDA: the helper converts image tensors to half precision and moves them to GPU.
- CPU: the helper keeps float32 and avoids half precision.

That means CPU debugging is a valid fallback for model loading and prompt checks, but it is not a performance-equivalent substitute for GPU runs.
If you are running on a GPU host and want to test CPU behavior, force `--device cpu`.

## Gradio launch checklist

If the launcher does not start:

1. Confirm that `gradio` is installed in the active environment.
2. Try a different `--port`.
3. If you need remote access, use `--host 0.0.0.0`.
4. If you only need the CLI parser check, run `python scripts/launch_demo.py --help` first.

## When to escalate

Escalate to the broader Donut skill when the failure is not specific to inference, for example:

- training config or Lightning errors
- dataset JSONL or metric issues
- SynthDoG resource or template issues
- repository refresh or import/export questions
