# Promptify Troubleshooting

## Purpose

Read this when Promptify fails to install, import, call a provider, parse output, or when older examples mention APIs that no longer exist.

## Install or import fails

### Symptoms
- `ModuleNotFoundError: promptify`
- `ImportError` for `pydantic`, `litellm`, `jinja2`, or `tenacity`
- `pip check` reports broken dependencies

### Likely causes
- The package was not installed into the active environment.
- The evaluation extra was skipped when ROUGE or dataset helpers are needed.
- An editable install was interrupted or mixed with a different Python environment.

### Recovery
- Reinstall with `python -m pip install -e '.[eval]'` for the full skill surface.
- Re-run `python -m pip check`.
- Confirm the import comes from the intended environment, not the working tree.

## Legacy tutorial API mismatch

### Symptoms
- `ImportError: cannot import name Prompter`
- `ImportError: cannot import name OpenAI`
- `ImportError: cannot import name Pipeline`

### Likely causes
- The user is following the older notebook or tutorial material.
- The repository still contains archived examples that do not match the current public API.

### Recovery
- Use the current task classes: NER, Classify, QA, Summarize, Task, ExtractRelations, ExtractTable, GenerateQuestions, GenerateSQL, NormalizeText, and ExtractTopics.
- For dataset scoring, switch to evaluate and load_dataset from the evaluation route.

## Provider, auth, and network errors

### Symptoms
- `ModelAuthenticationError`
- `ModelConnectionError`
- `ModelRateLimitError`
- `ModelResponseError`
- LiteLLM or provider-specific messages about invalid model names, missing API keys, or timeout failures

### Likely causes
- The model string does not match the configured provider.
- The provider API key is missing or invalid.
- The network is unavailable or rate limited.
- The model returned a response that did not match the expected structured schema.

### Recovery
- Verify the model name and provider prefix.
- Pass api_key explicitly when the environment variable is not set.
- Retry after backoff for rate limits.
- For offline development, replace the engine with a mock that returns deterministic JSON.

## JSON parse or schema problems

### Symptoms
- `ParserError: Failed to parse LLM output`
- Pydantic validation errors after the model returns text
- Incomplete JSON that stops halfway through a structured answer

### Likely causes
- The model returned prose instead of JSON.
- The output schema does not match the model response.
- The prompt is missing examples or the right template variables.

### Recovery
- Add or tighten examples and labels.
- Check that the task class matches the intended output shape.
- Verify the custom Pydantic model fields and types.
- Use the bundled smoke script to confirm the prompt and parser path offline.

## Template path or variable problems

### Symptoms
- `TemplateNotFoundError`
- A custom Jinja template renders unexpected blanks or incomplete instructions

### Likely causes
- The template name does not match a bundled file.
- A custom path is wrong.
- The template expects variables that the task never passes.

### Recovery
- Use one of the bundled template names or a verified filesystem path.
- Confirm the variables exposed by the task: text_input, domain, labels, examples, and task-specific kwargs such as question, schema, rules, num_questions, num_topics, max_length, or key_points.
- Prefer the built-in templates when possible.

## Binary classification looks inverted

### Symptoms
- The wrong label is predicted in the binary template path

### Likely causes
- The labels list was passed in the wrong order.
- A binary task was created with labels that do not correspond to the intended positive and negative class ordering.

### Recovery
- Recreate the classifier with the desired labels order.
- Use the bundled smoke script to confirm the rendered prompt before calling a live provider.

## When to stop

If the failure needs a real provider key, network access, or live model access, stop after confirming the prompt or parser path. For offline debugging, use the structured-tasks route with a mock engine and the shared smoke script.
