# Custom Model Backends

Use this guide when a future agent needs to wrap a non-standard local model, a framework model, or a specialized inference engine directly in the harness.

## Required Interface

All concrete model backends subclass `lm_eval.api.model.LM`. The core methods receive `list[Instance]` and return results in the same order:

| Method | `Instance.args` shape | Return shape | Used by |
| --- | --- | --- | --- |
| `generate_until` | `(context: str, gen_kwargs: dict)` | `list[str]` | Generative tasks |
| `loglikelihood` | `(context: str, continuation: str)` | `list[tuple[float, bool]]` | Multiple-choice/classification/scoring tasks |
| `loglikelihood_rolling` | `(text: str,)` | `list[float]` in current API implementation | Perplexity-style tasks |

For `loglikelihood`, the float is the log probability of the continuation conditioned on the context, and the boolean indicates whether the continuation would be produced by greedy decoding. Be careful with token offsets: the final continuation token is predicted by the previous input position and must not be scored from logits that have already seen it.

## Minimal Registration Pattern

```python
from lm_eval.api.model import LM
from lm_eval.api.registry import register_model

@register_model("my-backend", "my-backend-alias")
class MyBackend(LM):
    def __init__(self, pretrained=None, batch_size=1, **kwargs):
        super().__init__()
        self.pretrained = pretrained
        self.batch_size = int(batch_size)

    def generate_until(self, requests):
        outputs = []
        for instance in requests:
            context, gen_kwargs = instance.args
            outputs.append(self._generate(context, gen_kwargs))
        return outputs

    def loglikelihood(self, requests):
        outputs = []
        for instance in requests:
            context, continuation = instance.args
            outputs.append(self._score(context, continuation))
        return outputs

    def loglikelihood_rolling(self, requests):
        return [self._score_document(instance.args[0]) for instance in requests]
```

If adding the model inside the package, also expose it for discovery. Current source uses a lazy `MODEL_MAPPING` in `lm_eval.models.__init__`, mapping each alias to `module.path:ClassName`. Older docs mention importing the module in `lm_eval/models/__init__.py`; in this checkout, adding the lazy mapping is the registry path to preserve low startup cost.

## Constructor and `model_args`

`LM.create_from_arg_string()` parses comma-separated `key=value` pairs and calls the constructor as keyword arguments. `LM.create_from_arg_obj()` accepts a dictionary, which is how newer CLI config paths can pass `model_args` without string parsing. Design constructors to:

- Accept `**kwargs` for forward-compatible CLI/config options.
- Convert numeric and boolean strings carefully when the model class needs typed values.
- Avoid doing expensive downloads or GPU allocation before validating required arguments.
- Avoid relying on global current working directory for model files; accept explicit paths.

For users, recommend the bundled helper to build strings safely:

```bash
python scripts/model_args_builder.py --set pretrained=org/model --set dtype=float16 --set trust_remote_code=True
```

## Chat Template Support

A backend that supports `--apply_chat_template`, `--fewshot_as_multiturn`, or `--system_instruction` must implement:

- `tokenizer_name`: stable cache fingerprint for the tokenizer/template/system format.
- `chat_template(chat_template: bool | str = False)`: returns the selected template string for reproducibility in results.
- `apply_chat_template(chat_history: list[dict[str, str]], add_generation_prompt=True)`: converts chat messages to model input.

If these methods are absent, the base class raises `NotImplementedError` when chat template flags are used.

For Hugging Face-like tokenizers, delegate to `tokenizer.apply_chat_template(..., tokenize=False, add_generation_prompt=...)`. For custom engines, keep message roles explicit and include system prompts in the same format the model saw during instruction tuning.

## Thinking Token Support

Backends can support reasoning trace stripping by accepting `enable_thinking` and `think_end_token` model arguments. Evidence from `hf`, `vllm`, `sglang`, and `trtllm` shows two critical constraints:

- `enable_thinking=True` requires `think_end_token`.
- `enable_thinking=True` is rejected for loglikelihood tasks because thinking-mode generation does not expose a valid likelihood score for fixed continuations.

`hf` accepts `think_end_token` as a string or integer token ID. `vllm` and `sglang` accept string delimiters.

## Performance and Correctness Patterns

- Preserve request order even when batching, sorting, or dispatching asynchronously.
- Support empty context in `loglikelihood` by using a BOS/EOS/prefix token when the model requires one.
- Add a cache hook call for expensive deterministic operations if adapting an existing pattern that supports caching.
- Consider descending input-length batching for local models so runtime estimates are conservative and memory fragmentation is reduced.
- Implement distributed properties (`rank`, `world_size`, `all_gather`, `gather_object`, `barrier`) only when the backend internally manages distributed execution. The base class defaults to single-process behavior.

## Tests to Request or Add

For a contributed backend, ask for focused tests covering:

- `generate_until` returns one string per request and honors stop sequences.
- `loglikelihood` returns one `(float, bool)` tuple per request and handles empty contexts.
- `loglikelihood_rolling` returns floats for multiple document lengths.
- Chat-template flags either work or raise a clear `NotImplementedError`.
- Missing optional dependencies fail with a narrow install message rather than a generic import crash.
