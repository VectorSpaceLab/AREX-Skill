# Multimodal Understanding Workflows

## Purpose

Use these recipes to convert a user's image-understanding request into a Janus-family model call or a safe dry-run validation.

## Safe dry-run workflow

Use dry-run mode when you need to validate prompt structure without downloading weights:

```bash
python sub-skills/multimodal-understanding/scripts/janus_understanding.py \
  --family janus-pro \
  --model-id deepseek-ai/Janus-Pro-1B \
  --image ./sample.png \
  --question "What is in this image?"
```

Expected validation:

- Exactly one image placeholder is planned.
- The model family, role tokens, dtype, and device choices are printed.
- No Hugging Face download or model execution happens.

## Janus / Janus-Pro understanding

1. Install the base package and compatible torch/torchvision stack.
2. Load the processor and tokenizer:

   ```python
   from transformers import AutoModelForCausalLM
   from janus.models import MultiModalityCausalLM, VLChatProcessor
   from janus.utils.io import load_pil_images

   model_path = "deepseek-ai/Janus-Pro-1B"
   vl_chat_processor = VLChatProcessor.from_pretrained(model_path)
   tokenizer = vl_chat_processor.tokenizer
   vl_gpt = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
   ```

3. Move the model to the intended dtype/device:

   ```python
   vl_gpt = vl_gpt.to(torch.bfloat16).cuda().eval()
   ```

   Use CPU only for tiny diagnostics or explicit CPU experiments; real model usage is much slower and many examples assume CUDA.

4. Build the conversation:

   ```python
   conversation = [
       {"role": "<|User|>", "content": "<image_placeholder>\nConvert this formula to LaTeX.", "images": [image_path]},
       {"role": "<|Assistant|>", "content": ""},
   ]
   ```

5. Load and batch images:

   ```python
   pil_images = load_pil_images(conversation)
   prepare_inputs = vl_chat_processor(
       conversations=conversation,
       images=pil_images,
       force_batchify=True,
   ).to(vl_gpt.device)
   ```

6. Generate the answer:

   ```python
   inputs_embeds = vl_gpt.prepare_inputs_embeds(**prepare_inputs)
   outputs = vl_gpt.language_model.generate(
       inputs_embeds=inputs_embeds,
       attention_mask=prepare_inputs.attention_mask,
       pad_token_id=tokenizer.eos_token_id,
       bos_token_id=tokenizer.bos_token_id,
       eos_token_id=tokenizer.eos_token_id,
       max_new_tokens=512,
       do_sample=False,
       use_cache=True,
   )
   answer = tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
   ```

## JanusFlow understanding

JanusFlow understanding uses the JanusFlow model package but follows the same high-level flow:

```python
from janus.janusflow.models import MultiModalityCausalLM, VLChatProcessor
from janus.utils.io import load_pil_images

model_path = "deepseek-ai/JanusFlow-1.3B"
vl_chat_processor = VLChatProcessor.from_pretrained(model_path)
vl_gpt = MultiModalityCausalLM.from_pretrained(model_path, trust_remote_code=True)
```

Then build a conversation, load images, batch with `vl_chat_processor`, call `prepare_inputs_embeds`, and generate from `language_model.generate`.

For JanusFlow text-to-image generation, route to [`../../janusflow-workflows/SKILL.md`](../../janusflow-workflows/SKILL.md); it uses a different rectified-flow path.

## Validation checklist

Before running a real model:

- Confirm the model id matches the family.
- Confirm the number of `<image_placeholder>` tokens matches the image list.
- Confirm images are RGB and openable.
- Confirm the package imports `janus.models` or `janus.janusflow.models` as needed.
- Confirm `torch.cuda.is_available()` if you intend to use the README's `.cuda()` patterns.
- Print the formatted prompt and inspect role tokens when output is surprising.

## Output interpretation

The decoded answer may include the formatted prompt prefix in some snippets. If you want only the assistant answer, post-process conservatively: first inspect the raw decoded string, then remove only known prompt prefixes for the model family.
