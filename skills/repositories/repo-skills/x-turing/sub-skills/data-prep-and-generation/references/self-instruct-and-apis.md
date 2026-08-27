# Self-instruct and API wrappers

This guide covers the dataset-generation helpers that build instruction data from seed tasks or from extracted documents, plus the API wrappers they depend on.

## Seed-task JSONL format

`InstructionDataset.generate_dataset(...)` expects a seed-task JSONL file. Each line should contain:

- `id`
- `name`
- `instruction`
- `instances` as a list of `{input, output}` objects
- optional `is_classification`

Example:

```jsonl
{"id":"seed_task_0","name":"addition","instruction":"Add the numbers","instances":[{"input":"2 + 2","output":"4"}],"is_classification":false}
```

## `InstructionDataset.generate_dataset(...)`

Signature shape:

```python
InstructionDataset.generate_dataset(
    path,
    engine,
    num_instructions=10,
    num_instructions_for_finetuning=5,
    num_prompt_instructions=1,
)
```

### What it does

1. Loads seed tasks from the provided JSONL file.
2. Generates more instructions with the API wrapper.
3. Filters low-similarity duplicates.
4. Builds a cached fine-tuning set.
5. Returns an `InstructionDataset` from the generated `sampled_generated.jsonl` file.

### Cache files

The helper creates a temporary cache directory named after the engine config and the requested counts. Inside that cache, the workflow writes:

- `machine_generated_instructions.jsonl`
- `is_clf_or_not.jsonl`
- `filtered_instructions.jsonl`
- `all_generated.jsonl`
- `sampled_generated.jsonl`
- `finetuning.jsonl`

If the cache directory already exists, the helper reuses it instead of starting from scratch.

## `InstructionDataset.generate_dataset_from_dir(...)`

This helper first extracts text from a directory of documents, then generates seed tasks, and optionally runs self-instruct on them.

### Important caveat

The document-extraction path depends on `textract` and external system libraries. If `textract` is missing, the helper prints installation guidance and exits.

### Output behavior

- It writes `generated_tasks.jsonl` in the current working directory.
- If `use_self_instruct=True`, it routes back through `generate_dataset(...)`.
- If `use_self_instruct=False`, it constructs a dataset with `instruction`, `text`, and `target`, where `text` is empty and `target` comes from the first generated instance.

### Practical engine note

`generate_dataset_from_dir(...)` reaches through `prepare_seed_tasks(...)` and calls `engine.get_completion(...)`.

In the current runtime, that makes the documented `ChatGPT` wrapper the practical choice for this path.

## API wrapper overview

All generation wrappers return a list of dictionaries with at least:

- `prompt`
- `response`
- `created_at`

### OpenAI wrappers

Classes:

- `OpenAITextGenerationAPI`
- `Davinci`
- `ChatGPT`

Behavior notes:

- `OpenAITextGenerationAPI` stores `engine`, `api_key`, `organization`, and `request_batch_size`.
- It retries `openai` calls on `OpenAIError`.
- If the error message says the prompt is too long, it shrinks `max_tokens` and retries.
- If all retries fail, the returned `response` entry can be `None`.
- `Davinci` is a convenience wrapper for the `davinci` engine.
- `ChatGPT` targets `gpt-3.5-turbo`.
- `ChatGPT.get_completion(...)` uses the chat-completions API and is not a general batch API.

### Cohere wrappers

Classes:

- `CohereTextGenerationAPI`
- `Medium`

Behavior notes:

- `CohereTextGenerationAPI` uses `cohere.Client(self.api_key)`.
- It retries on `CohereError` with backoff.
- It currently consumes only the first prompt in the `prompts` list.
- The final response assembly does not guard the fully-failed case, so a totally exhausted retry path can still bubble up as an exception.
- `Medium` is a convenience wrapper for the `medium` engine.

### Claude wrappers

Classes:

- `ClaudeTextGenerationAPI`
- `ClaudeSonnet`

Behavior notes:

- `ClaudeTextGenerationAPI` requires the `anthropic` SDK.
- If `anthropic` is missing, initialization raises `ModuleNotFoundError` with an install hint.
- It creates `Anthropic(api_key=api_key)` and calls `messages.create(...)`.
- It retries on rate-limit, API, and connection errors.
- If retries are exhausted, the returned `response` entry is `None`.
- `ClaudeSonnet` targets `claude-3-sonnet-20240229`.
- Claude responses are re-rendered from text blocks into a single text string.

## Credentials and network requirements

These helpers are network-backed. They need:

- a valid API key for the chosen provider
- outbound network access
- the provider package installed in the environment

If any of those are missing, generation may fail before any dataset is written.

## Text extraction caveats

The directory-based helper uses `extract_text_from_directory(...)`.

Important constraints:

- the input must be a directory
- only supported file extensions are processed
- unsupported files are skipped
- if `textract` is unavailable, the helper prints a dependency warning and exits

## Generated-file interpretation

The final dataset returned by the self-instruct helpers is still an `InstructionDataset` with the standard three columns:

- `instruction`
- `text`
- `target`

Use the troubleshooting guide if you need to diagnose a cache hit, a missing API credential, or a document-extraction failure.
