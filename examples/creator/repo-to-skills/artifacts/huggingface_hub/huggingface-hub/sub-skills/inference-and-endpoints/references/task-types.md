# Task Types And Payload Shapes

The package's inference types are generated from the Hugging Face task schemas.
They are permissive `BaseInferenceType` dataclasses that also behave like dicts:
missing fields become `None`, nested generated objects are parsed, keys are
normalized (`content-type` to `content_type`), and unknown response fields are
retained. Treat `src/huggingface_hub/inference/_generated/` and
`inference_types.md` as generated evidence; import public types from
`huggingface_hub` and do not edit or regenerate them in a runtime workflow.

## Choose a family, not a generated catalog

| Family | Representative client methods | Input shape | Typical output |
|---|---|---|---|
| Text generation | `text_generation`, `summarization`, `translation`, `text2text_generation`, `fill_mask`, QA, classification | string or task-specific dict | string, generated output, or list of typed predictions |
| Chat/conversational | `chat_completion` / `chat.completions.create` | list of role/content messages | `ChatCompletionOutput` or stream chunks |
| Embeddings/similarity | `feature_extraction`, `sentence_similarity` | string or list of strings; similarity pair where applicable | float32 `numpy.ndarray` or scores |
| Image/vision | image classification, segmentation, detection, captioning, VQA, zero-shot vision, image transforms | bytes, binary file, `Path`, URL, or PIL image as supported | typed labels/boxes/captions, bytes, or PIL image |
| Audio/video | ASR, audio classification/separation, speech/audio/video generation and classification | binary media or text prompt | typed transcription/predictions or media bytes |
| Tabular/document | table QA, tabular classification/regression, document QA | dict/table plus media where required | typed answers, labels, or numeric results |

The generated schema modules include such public types as
`ChatCompletionInputMessage`, `ChatCompletionInputTool`,
`ChatCompletionInputResponseFormatJSONSchema`, `ChatCompletionOutput`,
`ChatCompletionStreamOutput`, `TextGenerationOutput`,
`TextGenerationStreamOutput`, and task-specific `*Input`/`*Output` classes.
The method's docstring and `inspect.signature` are authoritative when a
provider adds or removes options.

## Text payloads

```python
from huggingface_hub import InferenceClient

client = InferenceClient(
    model="<MODEL_ID>",
    provider="<PROVIDER_OR_auto>",
    token="<HF_TOKEN_OR_PROVIDER_KEY>",
)
text = client.text_generation(
    "<PROMPT>",
    max_new_tokens=64,
    temperature=0.2,
    stream=False,
)
```

The string result is the default. `details=True` asks for token/finish
metadata where the backend supports it; `stream=True` changes the return to an
iterable. `stop`, `max_new_tokens`, `temperature`, `top_p`, and `seed` are
common parameters, not universal provider guarantees. `grammar` is a separate
TGI-style constraint surface; validate its JSON/regex form before sending.

## Chat messages

Plain dictionaries are accepted. A message has a `role` and string content,
or multimodal content chunks such as:

```python
messages = [
    {"role": "system", "content": "<SYSTEM_INSTRUCTION>"},
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "<QUESTION>"},
            {"type": "image_url", "image_url": {"url": "<HTTPS_OR_DATA_URL>"}},
        ],
    },
]
```

For a tool definition, use the OpenAI-shaped schema (only functions are
currently represented by the generated input type):

```python
tools = [{
    "type": "function",
    "function": {
        "name": "lookup_weather",
        "description": "Read weather for a named city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}]
response = client.chat.completions.create(
    model="<CHAT_MODEL_ID>",
    messages=[{"role": "user", "content": "<QUESTION>"}],
    tools=tools,
    tool_choice="auto",
)
```

The model's tool call is data in `response.choices[0].message.tool_calls`;
parse its `function.arguments`, validate against the same schema, authorize
side effects, and append a correctly formed tool result only after execution.
Never treat a model-generated function name or arguments as trusted code.

## JSON mode and structured outputs

The generated response-format types are:

```python
json_mode = {"type": "json_object"}
structured = {
    "type": "json_schema",
    "json_schema": {
        "name": "<SCHEMA_NAME>",
        "description": "<OPTIONAL_DESCRIPTION>",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    },
}
```

`json_object` asks for syntactically valid JSON. `json_schema` asks for schema
adherence, but only if the selected model/provider implements it. The response
still arrives as message content; call `json.loads` and a real schema
validator when correctness matters. JSON schema must be under
`json_schema.schema`, not directly under `response_format`. In HF Inference,
the provider helper maps a JSON-schema format to its grammar-compatible JSON
form; this is not evidence that every provider honors `strict` identically.

## Embeddings

```python
vectors = client.feature_extraction(
    ["<DOCUMENT>", "<QUERY>"],
    normalize=True,
    model="<EMBEDDING_MODEL_ID>",
)
# vectors is a float32 numpy.ndarray when numpy is installed.
```

A list input is preserved as a batch by the client. `normalize`, `truncate`,
`prompt_name`, `dimensions`, and `encoding_format` are backend/provider
specific; TEI and OpenAI-compatible embedding endpoints do not expose exactly
the same options. Do not assume vector dimensionality without inspecting the
model/provider contract.

## Binary media

The shared `ContentT` annotation includes raw `bytes`, `bytearray`,
`memoryview`, a binary file-like object, `Path`, string path/URL, and PIL image,
but concrete provider helpers accept different subsets. In 1.29.0 the
`hf-inference` binary request helper directly accepts `bytes`, `Path`, or
string path/URL; other helpers that call the shared media converters can also
accept file-like, byte-like, or PIL inputs. Normalize to `bytes` or `Path` for
portable HF binary calls instead of assuming every annotated form reaches every
provider. A local string is interpreted as a path and an HTTP(S) string can be
downloaded by the client. To send raw content represented by a string, encode
it first. When parameters are present for HF binary tasks, the helper
base64-wraps inputs in JSON; without parameters it sends raw bytes with a
guessed MIME type. This distinction is provider-specific.

```python
from pathlib import Path

result = client.image_classification(Path("<LOCAL_IMAGE_PATH>"))
transcript = client.automatic_speech_recognition(Path("<LOCAL_AUDIO_PATH>"))
image = client.text_to_image("<IMAGE_PROMPT>")  # PIL.Image.Image; requires Pillow
```

Do not put private media URLs or base64 data in logs. Verify file existence,
MIME type, and size before a paid request. A URL input can cause a second
network fetch before inference; use bytes or an opened file when that behavior
is not acceptable.

## Typed parsing and compatibility

Generated dataclasses are intentionally forward-compatible. For a known type,
use `Type.parse_obj_as_instance(response)` or `Type.parse_obj_as_list(response)`
and assert whether a server response is singular or a list. Unknown fields are
retained as attributes, so do not use their presence as proof of a stable API.
If a provider returns a shape that cannot be parsed, first inspect the raw
mocked response and provider helper; do not edit generated types to hide a
provider mismatch.
