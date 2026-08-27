# Structured Task API Reference

## Purpose

Read this when you need the exact Promptify task signatures, the shared runtime objects behind them, or the rule that separates model kwargs from template kwargs.

## Verified public signatures

### Task constructors

- NER(model: str, domain: Optional[str] = None, labels: Optional[List[str]] = None, examples: Optional[List[Tuple[str, str]]] = None, instruction: Optional[str] = None, **kwargs: Any)
- Classify(model: str, labels: List[str], multi_label: bool = False, domain: Optional[str] = None, examples: Optional[List[Tuple[str, str]]] = None, instruction: Optional[str] = None, **kwargs: Any)
- QA(model: str, domain: Optional[str] = None, examples: Optional[List[Tuple[str, str]]] = None, instruction: Optional[str] = None, **kwargs: Any)
- Summarize(model: str, max_length: Optional[int] = None, key_points: bool = False, domain: Optional[str] = None, instruction: Optional[str] = None, **kwargs: Any)
- Task(model: str, output_schema: Type[BaseModel], instruction: str, **kwargs: Any)
- ExtractRelations(model: str, domain: Optional[str] = None, examples: Optional[List[Tuple[str, str]]] = None, instruction: Optional[str] = None, **kwargs: Any)
- ExtractTable(model: str, examples: Optional[List[Tuple[str, str]]] = None, instruction: Optional[str] = None, **kwargs: Any)
- GenerateQuestions(model: str, num_questions: int = 3, domain: Optional[str] = None, instruction: Optional[str] = None, **kwargs: Any)
- GenerateSQL(model: str, schema: Optional[str] = None, examples: Optional[List[Tuple[str, str]]] = None, instruction: Optional[str] = None, **kwargs: Any)
- NormalizeText(model: str, rules: Optional[List[str]] = None, examples: Optional[List[Tuple[str, str]]] = None, instruction: Optional[str] = None, **kwargs: Any)
- ExtractTopics(model: str, num_topics: int = 5, domain: Optional[str] = None, instruction: Optional[str] = None, **kwargs: Any)

### Shared runtime objects

- ModelConfig(*, model: str, api_key: Optional[str] = None, temperature: float = 0.0, top_p: float = 1.0, max_tokens: Optional[int] = None, stop: Optional[Union[str, List[str]]] = None, presence_penalty: float = 0.0, frequency_penalty: float = 0.0, timeout: Optional[float] = None, max_retries: int = 3, extra_params: Dict[str, Any] = <factory>)
- CacheConfig(*, enabled: bool = True, backend: Literal['memory', 'disk', 'redis'] = 'memory', maxsize: int = 128, ttl: Optional[int] = 3600, redis_url: Optional[str] = None)
- LLMEngine(config: ModelConfig)
- Parser()
- PromptBuilder(template: Optional[str] = None)

### Evaluation-adjacent helpers

- get_cost_summary() -> Dict[str, Any]
- setup_logging(level: int = logging.INFO) -> logging.Logger

## How the task stack works

### BaseTask call flow

Every task object follows the same sequence:

1. Build the prompt messages from instruction, text input, domain, labels, examples, and task-specific kwargs.
2. Call LiteLLM through LLMEngine.
3. Prefer the parsed Pydantic response when LiteLLM returns one.
4. Fall back to Parser.parse when the raw text still needs to be turned into structured JSON.

### Async and batch behavior

- `acall()` mirrors `__call__()` but awaits LiteLLM.
- `batch()` uses async concurrency under the hood and accepts `max_concurrent`.
- If `batch()` runs inside an already-running event loop, the implementation offloads to a short-lived thread so sync callers do not have to manage the loop themselves.

## Kwarg routing rule

Promptify separates kwargs into two buckets inside BaseTask:

- Model kwargs are passed to ModelConfig and LiteLLM.
- Everything else is preserved as template kwargs and can be rendered by the Jinja template.

### Model kwargs recognized by BaseTask

- temperature
- top_p
- max_tokens
- stop
- presence_penalty
- frequency_penalty
- timeout
- max_retries

### Template kwargs commonly consumed by built-in templates

- domain
- labels
- examples
- question
- schema
- rules
- num_questions
- num_topics
- max_length
- key_points
- description

If a user passes a kwarg that is not in the model bucket, it is available to the prompt template. This is the main mechanism for task-specific prompt customization.

## PromptBuilder notes

- Built-in template names resolve under promptify/prompts/templates.
- A filesystem path ending in .jinja is treated as a custom template.
- With a template, PromptBuilder renders a user message and places the instruction in the system message.
- Without a template, PromptBuilder creates a generic instruction-based prompt and can inject examples directly into the message list.
- The output schema, when present, is summarized as a JSON hint in the system prompt.

## Parser notes

Parser.parse(text, output_schema=None) tries JSON, then Python literal parsing, then incomplete JSON completion.
It never uses eval().

## Advanced note on cache support

CacheConfig and PromptCache exist in the source tree, but task execution does not automatically use a cache. Treat caching as an advanced integration point rather than a built-in workflow.
