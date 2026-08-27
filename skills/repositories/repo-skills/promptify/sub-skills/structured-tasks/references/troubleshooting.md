# Structured Task Troubleshooting

## Purpose

Read this when task construction or live provider calls fail.

## Missing or invalid provider credentials

### Symptoms
- `ModelAuthenticationError`
- provider errors about invalid API keys or unauthorized access
- a task works with a mock engine but fails with a real model string

### Likely causes
- The provider key is missing, stale, or set for a different account.
- The model string does not match the provider prefix that LiteLLM expects.

### Recovery
- Confirm the provider and model string.
- Pass `api_key=` explicitly if the environment variable is not set.
- Use the bundled smoke script with a mock engine to separate prompt issues from provider issues.

## Rate limits or connectivity issues

### Symptoms
- `ModelRateLimitError`
- `ModelConnectionError`
- timeout failures
- intermittent provider 429 or network errors

### Likely causes
- The provider is throttling requests.
- The network path to the provider is unstable.
- The configured timeout is too aggressive.

### Recovery
- Retry with backoff.
- Increase `timeout` or reduce concurrency.
- If you are debugging prompt logic, switch to a mock engine first.

## Malformed or non-JSON model output

### Symptoms
- `ParserError`
- structured parse fallback fails even though the provider returned text
- the model returns prose, incomplete JSON, or mismatched field names

### Likely causes
- The prompt is too loose.
- The task class does not match the requested output shape.
- Examples or template variables are missing.

### Recovery
- Use the correct built-in task class.
- Add examples that show the target JSON shape.
- Check the output schema and verify the model response against it.
- Run the smoke script with a deterministic payload to confirm the parser path.

## Template not found

### Symptoms
- `TemplateNotFoundError`
- a custom template path cannot be resolved

### Likely causes
- The template name does not match a bundled file under promptify/prompts/templates.
- The custom path is wrong.

### Recovery
- Use a verified built-in template name when possible.
- If using a custom file, pass a real filesystem path to the .jinja file.
- Keep the template file self-contained and renderable with the variables Promptify passes.

## Template renders blank or incomplete content

### Symptoms
- The prompt is generated, but a custom template seems to ignore fields.

### Likely causes
- The template expects variables the task never passes.
- A variable name does not match the task kwargs.

### Recovery
- Confirm the available variables: text_input, domain, labels, examples, and task-specific kwargs such as question, schema, rules, num_questions, num_topics, max_length, and key_points.
- Prefer the built-in templates if you only need the standard task family.

## Binary classification gives the wrong ordering

### Symptoms
- The model appears to choose the wrong side of a binary decision.

### Likely causes
- The labels list was passed in the wrong order.
- The binary task should have been modeled as a multilabel or multiclass task instead.

### Recovery
- Recreate the classifier with the desired label order.
- If the task has more than two semantic outcomes, use the multiclass path.

## Custom schema validation fails

### Symptoms
- Pydantic validation errors after parsing
- fields are missing, wrong type, or nested incorrectly

### Likely causes
- The output schema is stricter than the prompt.
- The model response does not match the exact shape.

### Recovery
- Simplify the schema or add examples.
- Ensure the instruction asks for valid JSON.
- Check the parsed payload against the schema before running a live provider.

## Async or batch behavior feels odd

### Symptoms
- Confusion about `batch()` in an async app
- batch work appears to hang or behave differently in a notebook or notebook-like environment

### Likely causes
- `batch()` manages its own async execution and thread handoff.
- The code is running inside an already-active loop.

### Recovery
- Use `acall()` directly inside async code when you only need one call.
- Use `batch()` from sync code or after confirming the loop behavior.

## When to stop

If the remaining failure needs a real provider, live model, or network access, stop after you have validated the prompt and parser path with the shared smoke script.
