# Transformer Optimization

## Purpose

Use this reference when a Flair model or embedding uses `TransformerWordEmbeddings`, `TransformerDocumentEmbeddings`, or combined `TransformerEmbeddings`, and the task is to reduce inference latency, memory use, or deployment surprises. These paths are optional. The verified baseline for this sub-skill is ordinary PyTorch execution on CPU.

Do not claim an ONNX provider, CUDA path, TorchScript deployment, AWS Neuron-like runtime, PEFT/quantized transformer path, or model-download path is verified unless the current environment imports the required packages, constructs the runtime object, and compares outputs against the PyTorch baseline.

## Baseline comparison first

Before changing runtime format:

1. Load the trained model or embedding in normal PyTorch form.
2. Create 2-5 representative `Sentence` examples. Include at least one longer sentence, one multi-token/subword-heavy example, and context/OCR metadata when the production path uses it.
3. Embed or predict once with the PyTorch baseline.
4. Save exact output tensors or labels for comparison.
5. Call `sentence.clear_embeddings()` between baseline and optimized passes.
6. Export, trace, optimize, or quantize only after the baseline path is stable.

Minimal token-output comparison pattern:

```python
import torch
from flair.data import Sentence

texts = ["I live in Berlin", "Berlin is to Germany as Vienna is to Austria"]
base_sentences = [Sentence(t) for t in texts]
opt_sentences = [Sentence(t) for t in texts]

base_embedding.embed(base_sentences)
optimized_embedding.embed(opt_sentences)

base_names = base_embedding.get_names()
opt_names = optimized_embedding.get_names()
for base_sentence, opt_sentence in zip(base_sentences, opt_sentences):
    for base_token, opt_token in zip(base_sentence, opt_sentence):
        assert torch.isclose(
            base_token.get_embedding(base_names),
            opt_token.get_embedding(opt_names),
            atol=1e-5,
        ).all()

for sentence in base_sentences + opt_sentences:
    sentence.clear_embeddings()
```

For document embeddings, compare `Sentence.get_embedding(names)` instead of token vectors. Use a documented looser tolerance only when provider precision changes are understood.

## Transformer knobs that affect deployment

| Knob | Runtime impact | Validation note |
| --- | --- | --- |
| `allow_long_sentences` | Enables overflow/stride tensors and dynamic axes. | Include long examples in export/tracing sets. |
| `force_max_length=True` | Pads every sequence to tokenizer max length. | Can simplify some traces/providers but increases memory/time. |
| `layers` / `layer_mean` | Concatenated layers widen IO; layer mean keeps one hidden-size width. | Use only layers required by the trained model. |
| `subtoken_pooling` | `first_last` doubles token vector width. | Decoder dimensions must match saved model. |
| `cls_pooling` | Document output can be `cls`, `mean`, or `max`. | Prefer `mean`/`max` for strided long document embeddings. |
| `use_context` | Adds neighboring sentence tokens and `[FLERT]` separators. | Examples must include context and document-boundary behavior. |
| OCR/image metadata | Layout-style models may require token `bbox` metadata and sentence `image` metadata. | Missing metadata raises before model execution. |
| `peft_config` or quantized HF load kwargs | Adds optional `peft`, bitsandbytes, and device-map complexity. | Treat as unverified unless packages and target hardware are proven. |

## ONNX export path

Flair transformer embeddings expose `export_onnx(path, example_sentences, **kwargs)`. It exports the embedding module and returns `TransformerOnnxWordEmbeddings` or `TransformerOnnxDocumentEmbeddings` depending on the embedding class.

Basic CPU-provider pattern:

```python
from flair.data import Sentence
from flair.embeddings import TransformerWordEmbeddings

examples = [
    Sentence("I live in Berlin"),
    Sentence("Berlin is to Germany as Vienna is to Austria"),
]

embedding = TransformerWordEmbeddings("distilbert-base-uncased", allow_long_sentences=False)
onnx_embedding = embedding.export_onnx(
    "artifacts/flair-embedding.onnx",
    examples,
    providers=["CPUExecutionProvider"],
    session_options={},
)
```

For a trained model, replace the model's transformer embedding only after comparing outputs:

```python
model.embeddings = model.embeddings.export_onnx(
    "artifacts/flair-embedding.onnx",
    examples,
    providers=["CPUExecutionProvider"],
    session_options={},
)
model.save("artifacts/model-with-onnx-embedding.pt")
```

### ONNX dependencies and providers

| Operation | Required packages | Optional/provider notes |
| --- | --- | --- |
| Export and run CPU ONNX | `onnxruntime` plus the PyTorch/transformers packages already needed by Flair | `CPUExecutionProvider` should be available in a normal ONNX Runtime install. |
| CUDA provider execution | Usually `onnxruntime-gpu` plus compatible CUDA/cuDNN runtime | Provider availability must be checked in the target environment. Do not infer it from `flair.device`. |
| Graph optimization | `onnxruntime`, `onnx`, and often `coloredlogs` | Flair wraps `onnxruntime.transformers.optimizer.optimize_model`. |
| Dynamic quantization | `onnxruntime` and `onnx` | Mainly CPU-oriented; CUDA provider can be unsupported or slower for quantized models. |

Check provider availability:

```python
import onnxruntime
print(onnxruntime.get_available_providers())
```

Provider examples:

```python
cpu_providers = ["CPUExecutionProvider"]

# Use only after the environment proves CUDA provider support.
cuda_providers = [
    ("CUDAExecutionProvider", {"device_id": 0}),
    "CPUExecutionProvider",
]
```

`TransformerOnnxEmbeddings` stores the ONNX file path and provider list. If the file is moved or external data files are missing, session creation fails.

## Optimize and quantize an ONNX embedding

After export and baseline comparison:

```python
onnx_embedding.optimize_model(
    "artifacts/flair-embedding-optimized.onnx",
    opt_level=2,
    use_gpu=False,
    only_onnxruntime=True,
    use_external_data_format=False,
)
```

For very large ONNX models, `use_external_data_format=True` may create multiple files next to the `.onnx` file. Deploy all generated files together.

CPU-oriented dynamic quantization:

```python
onnx_embedding.quantize_model(
    "artifacts/flair-embedding-quantized.onnx",
    extra_options={"DisableShapeInference": True},
    use_external_data_format=False,
)
```

After optimizing or quantizing, rerun output comparison and measure latency on the intended workload. Stop if the provider does not support quantization, output drift is unacceptable, or latency regresses.

## TorchScript / JIT path

TorchScript avoids ONNX Runtime provider dependencies but still requires PyTorch support for the traced operations. Flair provides `TransformerJitWordEmbeddings` and `TransformerJitDocumentEmbeddings` wrappers.

Core mechanics:

- `embedding.prepare_tensors(sentences)` returns the actual tensors required by the selected transformer model and options.
- `embedding.forward(**tensors)` returns a dictionary with `token_embeddings`, `document_embeddings`, or both.
- TorchScript tracing cannot take keyword arguments or `None`, so use a wrapper whose positional parameters match `prepare_tensors` keys.

Token tracing pattern:

```python
import torch
from flair.data import Sentence
from flair.embeddings import TransformerJitWordEmbeddings, TransformerWordEmbeddings

examples = [Sentence("I love Berlin, but Vienna is where my heart is.")]
base_embedding = TransformerWordEmbeddings(
    "distilbert-base-uncased",
    layers="-1",
    allow_long_sentences=True,
)

print(sorted(base_embedding.prepare_tensors(examples).keys()))

class JitWrapper(torch.nn.Module):
    def __init__(self, embedding):
        super().__init__()
        self.embedding = embedding

    def forward(self, input_ids, token_lengths, attention_mask, overflow_to_sample_mapping, word_ids):
        return self.embedding.forward(
            input_ids=input_ids,
            token_lengths=token_lengths,
            attention_mask=attention_mask,
            overflow_to_sample_mapping=overflow_to_sample_mapping,
            word_ids=word_ids,
        )["token_embeddings"]

wrapper = JitWrapper(base_embedding)
param_names, param_list = TransformerJitWordEmbeddings.parameter_to_list(base_embedding, wrapper, examples)
script_module = torch.jit.trace(wrapper, param_list)
jit_embedding = TransformerJitWordEmbeddings.create_from_embedding(script_module, base_embedding, param_names)
```

The required parameters differ by model and options. Adjust the wrapper after inspecting `prepare_tensors`. For document embeddings, return `forward(...)["document_embeddings"]` and use `TransformerJitDocumentEmbeddings`.

For AWS Neuron-like or other proprietary TorchScript routes, treat the provider/compiler as optional and unverified until the target environment compiles and compares outputs. Some runtimes require `force_max_length=True`; validate the memory/latency trade-off.

## Memory and speed levers before export

Try these before changing runtime format when they fit the task:

- Use a smaller transformer model.
- Use fewer layers and `layer_mean=True` to avoid wide concatenated outputs.
- Use `mini_batch_size` as high as memory allows for prediction/training, then reduce if memory fails.
- Use `mini_batch_chunk_size` in training when a desired mini-batch is too large; this slows training but can avoid memory errors.
- Use `embeddings_storage_mode="none"` when fine-tuning transformers or processing large datasets.
- For static frozen embeddings and repeated epochs, `embeddings_storage_mode="cpu"` can reduce recomputation if RAM is sufficient.
- Use `use_amp=True` only after backend support is proven.
- Use `reduce_transformer_vocab=True` only in a verified training environment where the needed plugin path and tokenizer behavior are acceptable.

## Deployment hygiene

- Store optimized artifacts under the caller's output directory, not inside this generated skill tree.
- If ONNX uses external data format, copy the `.onnx` file and all sibling external data files together.
- Do not hard-code local cache, checkout, or environment paths into saved references or model cards.
- Keep the original PyTorch model or a reproducible export recipe until the optimized model is validated on target hardware.
- Re-run comparison after changing providers, ONNX Runtime versions, transformer versions, tokenizer options, `force_max_length`, or context settings.

## When to stop

Stop and report an unverified optional optimization path if:

- `onnxruntime`, `onnx`, `coloredlogs`, a provider package, or a proprietary compiler cannot be imported.
- `onnxruntime.get_available_providers()` does not list the requested provider.
- Export/tracing succeeds but tensor or label comparison exceeds the accepted tolerance.
- The model requires OCR boxes/images and the target service cannot provide token `bbox` or sentence `image` metadata.
- Quantized output is slower or unsupported on the intended provider.
- The deployment format requires credentials, proprietary runtimes, or hardware unavailable in the current environment.
