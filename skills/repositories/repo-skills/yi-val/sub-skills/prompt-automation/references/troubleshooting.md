# Prompt automation troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Generated examples ignored | Model output did not parse as dict/list of dicts or keys did not match `input_function.parameters`. | Tighten the prompt to return only a Python/JSON dict and verify parameter names. |
| Expected results missing | `expected_param_name` not set or generated output omitted that field. | Set `expected_param_name` and include it in `input_function.parameters`; generator will move it to `InputData.expected_result`. |
| Variation generator loops | Generated prompts do not include required `{variables}` placeholders. | Simplify prompt, reduce `variables`, or add explicit instruction to include every placeholder. |
| Cached stale prompts reused | `output_path` already exists from an older task. | Delete or rename the cache when changing schema/task semantics. |
| `openai.ChatCompletion` error | Incompatible OpenAI SDK version or missing credential. | Use the package-pinned OpenAI SDK style and set `OPENAI_API_KEY`; run offline fixture first. |
| Document generator raises loader errors | `source: file`/`drive` needs unstructured/OCR/Google dependencies or auth. | Smoke-test with `source: text`; then prepare file/drive dependencies explicitly. |
| Too many provider calls | Cartesian product of generated examples and variations is large. | Estimate `number_of_examples * total_variation_combinations` before running; start tiny. |

## Safe fallback

If provider generation is blocked, convert the plan to manual YAML:

```yaml
variations:
  - name: task
    variations:
      - value_type: str
        value: "Answer concisely: {question}"
        instantiated_value: "Answer concisely: {question}"
        variation_id: null
```

Then use a small static CSV dataset and `string_expected_result` evaluator to verify the rest of the run pipeline.
