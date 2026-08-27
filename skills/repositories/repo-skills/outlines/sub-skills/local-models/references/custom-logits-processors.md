# Custom logits processors

Use custom logits processors only when a built-in output type (`JsonSchema`, `Regex`, `Choice`, `CFG`, etc.) cannot express the local steering rule.

## Contract

A custom processor subclasses `OutlinesLogitsProcessor` and implements:

```python
from outlines.processors.base_logits_processor import OutlinesLogitsProcessor

class MyProcessor(OutlinesLogitsProcessor):
    def process_logits(self, input_ids, logits):
        # mutate or return logits using the tensor adapter
        return logits
```

Instantiate it with the local model's tensor library:

```python
processor = MyProcessor(model.tensor_library_name)
generator = outlines.Generator(model, processor=processor)
raw = generator(prompt, max_new_tokens=32)
```

Rules:

- Use local steerable models only.
- Do not pass an `output_type` at the same time as `processor`.
- The base class normalizes logits/input shape before calling `process_logits`; keep returned tensor type compatible with the underlying library.
- If the processor has sequence state, implement `reset()` or use a fresh processor/generator.

## Tensor-library implications

- Transformers uses `torch` tensors.
- llama.cpp uses NumPy-compatible arrays.
- MLX-LM uses MLX tensors.
- vLLM offline uses vLLM guided decoding parameters; do not assume the same custom processor path applies.

## Safe development sequence

1. Prototype the allowed token/regex/schema rule outside a model call.
2. Build a tiny unit test for the processor using synthetic logits.
3. Run one short local generation after the target model is already loaded.
4. Verify the output against a deterministic parser or regex.
5. Document backend/model constraints next to the processor.

## Common mistakes

- Using a processor with `from_openai`, `from_tgi`, or other server wrappers.
- Returning a CPU tensor when the model expects GPU logits.
- Failing to mask all batch rows.
- Holding matcher state across unrelated generations without reset.
- Trying to implement a grammar that could be expressed more safely as a `Regex` or `CFG` output type.
