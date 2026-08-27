# API Reference for Generation and Model Components

This reference covers public Haystack component APIs used for generation, prompting, embeddings, classification, sampling, and validation. It is intentionally scoped to model-facing components; pipeline wiring details belong in `../pipelines-and-components/SKILL.md`.

## Prompt Builders

| Component | Import | Main input | Main output | Use when |
| --- | --- | --- | --- | --- |
| `PromptBuilder` | `from haystack.components.builders import PromptBuilder` | Jinja variables as keyword inputs, optional runtime `template`, optional `template_variables` | `{"prompt": str}` | A text generator expects a single string prompt. |
| `ChatPromptBuilder` | `from haystack.components.builders import ChatPromptBuilder` | Jinja variables, optional runtime `template`, optional `template_variables` | `{"prompt": list[ChatMessage]}` | A chat generator expects `list[ChatMessage]`. |
| `AnswerBuilder` | `from haystack.components.builders import AnswerBuilder` | `query`, `replies`, optional `meta`, `documents` | `{"answers": list[GeneratedAnswer]}` | Convert generator replies into answer objects and attach cited documents. |

`PromptBuilder(template, required_variables=None, variables=None)` infers variables from Jinja syntax. Variables are optional by default and missing values render as empty strings. Use `required_variables=["query", "documents"]` or `required_variables="*"` when missing values should raise `ValueError`. At runtime, pass `template="..."` to replace the template or `template_variables={...}` to override variables.

`ChatPromptBuilder(template=None, required_variables=None, variables=None)` accepts either a list of `ChatMessage` objects or a string template using the chat-message Jinja extension. For list templates, user and system messages can contain Jinja expressions; non-user/system messages pass through. String templates can emit structured chat messages with `{% message role="system" %}...{% endmessage %}` blocks and can use `templatize_part` for mixed content. Avoid `templatize_part` inside a list of `ChatMessage` objects; that combination raises `ValueError`.

`AnswerBuilder(pattern=None, reference_pattern=None, last_message_only=False, return_only_referenced_documents=True, expand_reference_ranges=False)` accepts string replies or `ChatMessage` replies. Use `pattern` to extract answer text with at most one capture group. Use `reference_pattern` to parse 1-based document citations such as `[1]` or, with `expand_reference_ranges=True`, ranges such as `[2-4]`. Metadata from generator replies and explicit `meta` inputs are merged into `GeneratedAnswer.meta`.

## Text and Chat Generators

| Component | Import | Input | Output | Notes |
| --- | --- | --- | --- | --- |
| `OpenAIChatGenerator` | `from haystack.components.generators.chat import OpenAIChatGenerator` | `messages: list[ChatMessage]` | `replies: list[ChatMessage]` | Default model is `gpt-5-mini`; supports `generation_kwargs`, tools, async, streaming, structured output. |
| `AzureOpenAIChatGenerator` | `from haystack.components.generators.chat import AzureOpenAIChatGenerator` | `messages: list[ChatMessage]` | `replies: list[ChatMessage]` | Uses Azure endpoint, deployment, API version, API key or Azure AD token. |
| `HuggingFaceAPIChatGenerator` | `from haystack.components.generators.chat import HuggingFaceAPIChatGenerator` | `messages: list[ChatMessage]` | `replies: list[ChatMessage]` | Uses Hugging Face serverless/provider or endpoint chat-completion APIs. |
| `HuggingFaceLocalChatGenerator` | `from haystack.components.generators.chat import HuggingFaceLocalChatGenerator` | `messages: list[ChatMessage]` | `replies: list[ChatMessage]` | Loads local Transformers models; call `warm_up()` before first timed run. |
| `FallbackChatGenerator` | `from haystack.components.generators.chat import FallbackChatGenerator` | `messages: list[ChatMessage]` | `replies: list[ChatMessage]`, `meta` | Tries a list of chat generators until one succeeds. |
| `OpenAIGenerator` | `from haystack.components.generators import OpenAIGenerator` | `prompt: str` | `replies: list[str]`, `meta` | Text generator wrapper around OpenAI chat completions; deprecated in favor of chat generator for new work. |
| `AzureOpenAIGenerator` | `from haystack.components.generators import AzureOpenAIGenerator` | `prompt: str` | `replies: list[str]`, `meta` | Text generator for Azure; deprecated in favor of `AzureOpenAIChatGenerator`. |
| `HuggingFaceAPIGenerator` | `from haystack.components.generators import HuggingFaceAPIGenerator` | `prompt: str` | `replies: list[str]`, `meta` | API text generation; current Hugging Face generative serverless support favors chat completion. |
| `HuggingFaceLocalGenerator` | `from haystack.components.generators import HuggingFaceLocalGenerator` | `prompt: str` | `replies: list[str]` | Local Transformers text generation; deprecated in favor of local chat generator for new chat work. |
| `DALLEImageGenerator` | `from haystack.components.generators import DALLEImageGenerator` | image prompt | `images`, `revised_prompt` | OpenAI image generation, not a text/chat generator slot. |

Prefer chat generators for new LLM workflows because they preserve role, metadata, tool calls, multimodal content, and structured responses as `ChatMessage` objects. Text generators are still useful when an existing component slot or simple script expects `str` in and `list[str]` out.

Common OpenAI/Azure chat constructor parameters include `model` or Azure `azure_deployment`, `api_key`, `streaming_callback`, `generation_kwargs`, `timeout`, `max_retries`, `tools`, `tools_strict`, and HTTP client options. OpenAI credentials default to `Secret.from_env_var("OPENAI_API_KEY")`; Azure components use `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_AD_TOKEN`, and provider-specific API-version/deployment settings.

Common Hugging Face local parameters include `model`, `task`, `device`, `token`, `generation_kwargs`, `huggingface_pipeline_kwargs`, `stop_words`, and `streaming_callback`. Local components usually lazily load models in `warm_up()` or the first `run()` call; optional dependencies and hardware matter.

## Embedders

| Component family | Imports | Input and output | Key options |
| --- | --- | --- | --- |
| OpenAI text/document | `OpenAITextEmbedder`, `OpenAIDocumentEmbedder` from `haystack.components.embedders` | text -> `embedding`; documents -> documents with embeddings plus `meta` | `model`, `dimensions`, `prefix`, `suffix`, `timeout`, `max_retries`, async methods. |
| Azure OpenAI text/document | `AzureOpenAITextEmbedder`, `AzureOpenAIDocumentEmbedder` | same shape as OpenAI embedders | `azure_endpoint`, `azure_deployment`, `api_version`, API key or Azure AD token. |
| Hugging Face API text/document | `HuggingFaceAPITextEmbedder`, `HuggingFaceAPIDocumentEmbedder` | text/document embeddings via API | `api_type`, `api_params`, `token`, provider/model URL settings, async methods. |
| Sentence Transformers dense | `SentenceTransformersTextEmbedder`, `SentenceTransformersDocumentEmbedder` | local dense embeddings | `model`, `device`, `batch_size`, `normalize_embeddings`, `trust_remote_code`, `local_files_only`, `backend`, `precision`, `warm_up()`. |
| Sentence Transformers sparse | `SentenceTransformersSparseTextEmbedder`, `SentenceTransformersSparseDocumentEmbedder` | sparse embeddings | local optional dependencies; useful for sparse retrievers or hybrid search. |

Text embedders expect a single string. Document embedders expect `list[Document]`. If you get a type error suggesting a document embedder, switch families instead of wrapping a list in a string. Some local Sentence Transformers components are scheduled to move to integration packages in Haystack 3.0; for Haystack 2.31 use the public imports above, but mention integration-package migration in long-lived docs or upgrade plans.

## Classifiers and Samplers

| Component | Import | Input | Output | Use when |
| --- | --- | --- | --- | --- |
| `DocumentLanguageClassifier` | `from haystack.components.classifiers import DocumentLanguageClassifier` | `documents` | documents with language metadata | Detect document language using local language identification dependencies. |
| `TransformersZeroShotDocumentClassifier` | `from haystack.components.classifiers import TransformersZeroShotDocumentClassifier` | `documents`, optional `batch_size` | documents with `classification` metadata | Classify documents into configured labels using a Hugging Face zero-shot model. |
| `TopPSampler` | `from haystack.components.samplers import TopPSampler` | `documents`, optional runtime `top_p` | filtered documents | Keep high-probability documents by cumulative softmax over `Document.score` or `doc.meta[score_field]`. |

`TransformersZeroShotDocumentClassifier(model, labels, multi_label=False, classification_field=None, device=None, token=None, huggingface_pipeline_kwargs=None)` classifies `Document.content` unless `classification_field` names a metadata field. It raises `ValueError` if a required metadata classification field is missing. It requires Transformers/Torch optional dependencies.

`TopPSampler(top_p=1.0, score_field=None, min_top_k=None)` requires `0 <= top_p <= 1`. It falls back to returning the original documents when no valid scores are found, and returns at least one highest-scoring document when a low `top_p` would select none.

## JSON Validation and Structured Outputs

`JsonSchemaValidator` is imported with `from haystack.components.validators import JsonSchemaValidator`. It validates the text of the last `ChatMessage` in `messages` against a JSON schema and returns exactly one of:

- `validated`: the original last message when it contains valid JSON conforming to the schema.
- `validation_error`: a user `ChatMessage` containing a repair prompt when the text is not valid JSON or fails schema validation.

Instantiate with `JsonSchemaValidator(json_schema=None, error_template=None)` or pass `json_schema` and `error_template` at runtime. The schema can be a normal JSON schema or an OpenAI function-calling schema containing `name`, `description`, and `parameters`; in the latter case the `parameters` schema is validated.

For OpenAI and Azure chat generators, you can also use provider structured outputs via `generation_kwargs={"response_format": ...}`. Newer models support Pydantic models or strict JSON schema. For structured outputs with streaming, use JSON schema rather than a Pydantic model.

## Minimal Code Patterns

Plain prompt to text generator:

```python
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

builder = PromptBuilder(template="Answer in {{ language }}: {{ question }}", required_variables="*")
generator = OpenAIGenerator(api_key=Secret.from_env_var("OPENAI_API_KEY"), model="gpt-5-mini")
prompt = builder.run(language="English", question="What is Haystack?")["prompt"]
reply = generator.run(prompt=prompt, generation_kwargs={"max_completion_tokens": 80})["replies"][0]
```

Chat prompt to chat generator:

```python
from haystack.components.builders import ChatPromptBuilder
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage

messages = [
    ChatMessage.from_system("Answer as a concise {{ role }}."),
    ChatMessage.from_user("Question: {{ question }}"),
]
builder = ChatPromptBuilder(template=messages, required_variables=["question", "role"])
llm = OpenAIChatGenerator(model="gpt-5-mini")
rendered = builder.run(question="What is a component?", role="teacher")["prompt"]
result = llm.run(messages=rendered)
```

Schema validation after a chat reply:

```python
from haystack.components.validators import JsonSchemaValidator
from haystack.dataclasses import ChatMessage

schema = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]}
validator = JsonSchemaValidator(json_schema=schema)
result = validator.run(messages=[ChatMessage.from_assistant('{"answer": "Berlin"}')])
assert "validated" in result
```
