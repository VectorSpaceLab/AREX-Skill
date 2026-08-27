# LitGPT Inference Workflows

Use these workflows when an agent needs concrete steps for local text generation, chat, Python API inference, prompt-style diagnosis, quantization, or multi-device generation.

## Workflow: Offline Local Generation

Goal: generate from an already-local LitGPT checkpoint without downloads.

1. Validate the checkpoint layout and options:

   ```bash
   python sub-skills/inference-chat/scripts/check_inference_inputs.py \
     --checkpoint-dir CHECKPOINT_DIR \
     --prompt "Write one sentence about llamas." \
     --max-new-tokens 80 \
     --top-k 50 \
     --top-p 0.9 \
     --temperature 0.8
   ```

2. If the checker reports missing `lit_model.pth`, `model_config.yaml`, or tokenizer files, route to `../../checkpoint-conversion/`.
3. Run generation:

   ```bash
   litgpt generate CHECKPOINT_DIR \
     --prompt "Write one sentence about llamas." \
     --max_new_tokens 80 \
     --top_k 50 \
     --top_p 0.9 \
     --temperature 0.8
   ```

4. If the output repeats the prompt format or ignores instructions, inspect prompt-style compatibility using the prompt-style workflow below.

## Workflow: Interactive Chat

Goal: use a local checkpoint in a terminal chat loop.

```bash
litgpt chat CHECKPOINT_DIR --max_new_tokens 100 --top_k 50 --top_p 0.95 --temperature 0.8
```

For multi-line user input:

```bash
litgpt chat CHECKPOINT_DIR --multiline true
```

Operational notes:

- Empty prompt exits single-line mode.
- In multiline mode, submit with `!submit`; quit with `!quit` or `!exit`.
- Chat works with any valid checkpoint, but base/pretraining checkpoints usually continue text rather than behave like assistants.
- Instruction/chat-tuned checkpoints produce better dialogue if the tokenizer and prompt style match the checkpoint.

## Workflow: Python API Without Accidental Network

Goal: write Python code that does not download model files.

Preferred pattern:

```python
from pathlib import Path
from litgpt import LLM

checkpoint_dir = Path("checkpoints/example-model")
if not checkpoint_dir.is_dir():
    raise FileNotFoundError(f"Expected local checkpoint: {checkpoint_dir}")

llm = LLM.load(str(checkpoint_dir))
print(llm.generate("Give two LitGPT inference tips.", max_new_tokens=80, top_k=1))
```

Avoid this for offline workflows unless the user explicitly wants download behavior:

```python
LLM.load("microsoft/phi-2", init="pretrained")
```

If `"microsoft/phi-2"` is not a local directory, LitGPT treats it as a model identifier and can access the Hugging Face Hub. To use random weights for tests, require a tokenizer:

```python
llm = LLM.load("pythia-160m", init="random", tokenizer_dir="path/to/local-tokenizer")
```

## Workflow: Prompt Style And Tokenizer Mismatch Diagnosis

Symptoms:

- The model echoes raw chat template markers.
- The model never stops at expected assistant/user boundaries.
- A chat-tuned model behaves like a base continuation model.
- Decoding contains many unexpected special tokens.

Steps:

1. Check for a bundled prompt style file in the checkpoint. LitGPT prefers it when present.
2. If no prompt style file exists, LitGPT derives one from `model_config.yaml` using `PromptStyle.from_config`.
3. Verify the tokenizer files belong to the same model/checkpoint family. Common tokenizer indicators are `tokenizer.json`, `tokenizer.model`, `tokenizer_config.json`, `tokenizer.yaml`, or `vocab.json` plus `merges.txt`.
4. If the prompt style was saved with a finetuned checkpoint, keep that file next to the generated checkpoint for inference.
5. If prompt style is absent and the model family is supported, use the default style from config; otherwise use `Default`-style prompting and avoid forcing instruct/chat templates.
6. Re-run a short deterministic prompt with `--top_k 1`, low `--max_new_tokens`, and a simple instruction to compare behavior.

Decision rule: fix tokenizer/prompt-style files before tuning sampling parameters. Sampling changes cannot repair a mismatched prompt template.

## Workflow: Quantized Inference

Goal: reduce GPU memory for inference.

1. Confirm CUDA/Linux-compatible runtime and optional `bitsandbytes` availability:

   ```bash
   python sub-skills/inference-chat/scripts/check_inference_inputs.py \
     --checkpoint-dir CHECKPOINT_DIR \
     --quantize bnb.nf4-dq \
     --precision bf16-true \
     --require-cuda
   ```

2. Use a true precision, not mixed precision:

   ```bash
   litgpt generate CHECKPOINT_DIR \
     --prompt "List two memory optimizations." \
     --quantize bnb.nf4-dq \
     --precision bf16-true \
     --max_new_tokens 128
   ```

3. If `bf16-true` is unsupported on the GPU, try `16-true`.
4. If `bitsandbytes` is missing or the machine is CPU-only, remove `--quantize` or run on a compatible CUDA environment.

## Workflow: Sequential Multi-GPU Generation

Goal: fit a large checkpoint across multiple CUDA devices when one GPU is too small.

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 litgpt generate_sequentially CHECKPOINT_DIR \
  --prompt "Summarize the tradeoff of sequential inference." \
  --max_new_tokens 256 \
  --num_samples 1
```

Use sequential generation when:

- The model does not fit on a single GPU.
- Lower throughput is acceptable.
- The number of layers is at least the number of visible devices.

Memory levers:

- Reduce `--max_new_tokens`.
- Try `--quantize bnb.nf4-dq` with a true precision.
- Restrict visible devices intentionally with `CUDA_VISIBLE_DEVICES`.

## Workflow: Tensor Parallel Generation

Goal: speed up multi-GPU inference for compatible model dimensions.

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 litgpt generate_tp CHECKPOINT_DIR \
  --prompt "Explain top-p sampling in one paragraph." \
  --max_new_tokens 128
```

Use tensor parallel when:

- CUDA multi-GPU is available.
- Model attention/MLP dimensions divide evenly by the number of devices.
- Running a distributed process is acceptable.

Avoid tensor parallel in interactive notebooks; use a script entrypoint. If divisibility errors appear, reduce or change the number of visible devices.

## Workflow: Speculative Decoding

Goal: use a small draft checkpoint to accelerate a larger target checkpoint.

```bash
litgpt generate_speculatively DRAFT_CHECKPOINT_DIR TARGET_CHECKPOINT_DIR \
  --prompt "Give one practical speculative decoding caveat." \
  --speculative_k 3 \
  --max_new_tokens 100
```

Checklist:

- Both directories pass checkpoint layout checks.
- Draft model is smaller/faster than target model.
- Tokenizer vocab sizes match.
- `--speculative_k` is at least `1`.
- Compare acceptance rate and total latency; a poor draft model can reduce benefit.

## Workflow: Adapter Or Full-Finetuned Inference

Goal: generate from a model produced by training workflows.

- Full finetune: use `litgpt generate_full BASE_CHECKPOINT_DIR --finetuned_path PATH_TO_FINETUNED_PTH`.
- Adapter: use `litgpt generate_adapter BASE_CHECKPOINT_DIR --adapter_path PATH_TO_ADAPTER`.
- Adapter v2: use `litgpt generate_adapter_v2 BASE_CHECKPOINT_DIR --adapter_path PATH_TO_ADAPTER_V2`.

Do not use adapter-specific generation for LoRA unless the output is truly an adapter/adapter-v2 artifact. For LoRA, merge or choose the appropriate checkpoint-conversion route first.

## Workflow: Sampling Triage

Use this progression when output quality is unstable:

1. Start deterministic: `--top_k 1 --temperature 0 --top_p 1.0` or `top_p=0` in API calls.
2. Confirm prompt style/tokenizer behavior with a short known prompt.
3. Increase `max_new_tokens` only after the model starts correctly.
4. Add controlled diversity: `temperature=0.7` to `0.9`, `top_k=40` to `50`, `top_p=0.9` to `0.95`.
5. If output is still malformed, return to checkpoint/prompt-style validation instead of widening sampling.
