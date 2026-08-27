---
name: prompt-automation
description: "Configure YiVal data generators and prompt variation generators
  for synthetic examples, document questions, chain-of-density prompts, and
  self-exemplar prompts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# YiVal prompt automation

Use this sub-skill when the task involves generating input examples, generating prompt variations, caching generated prompts/data, using `yival gen`/`yival task`, or wiring OpenAI/document/chain-of-density/self-exemplar generators into a YiVal config.

## Read first

- [Generators reference](references/generators-reference.md): built-in data and variation generators, config fields, and registry ids.
- [Prompt workflows](references/prompt-workflows.md): common auto-prompt experiment patterns.
- [Provider and cache notes](references/provider-cache-notes.md): credentials, output paths, rate limits, and offline alternatives.
- [Prompt automation troubleshooting](references/troubleshooting.md): generation-specific failures.

Useful helper:

- `python sub-skills/prompt-automation/scripts/inspect_prompt_components.py` prints built-in generator ids and default configs after importing their modules.

## Built-in generator map

| Need | YAML location | Registry id |
| --- | --- | --- |
| Generate synthetic input examples from a function/task description | `dataset.data_generators` | `openai_prompt_data_generator` |
| Generate questions from text/file/Google Drive document content | `dataset.data_generators` | `document_data_generator` |
| Generate optimized prompt strings with OpenAI | `variations[].generator_name` | `openai_prompt_based_variation_generator` |
| Use the fixed chain-of-density summarization prompt | `variations[].generator_name` | `chain_of_density_prompt_generator` |
| Use a self-exemplar prompt template | `variations[].generator_name` | `self_exemplar` |

## Minimal auto-prompt shape

```yaml
description: Auto prompt experiment
custom_function: my_task.headline
dataset:
  source_type: machine_generated
  data_generators:
    openai_prompt_data_generator:
      number_of_examples: 2
      chunk_size: 1000
      model_name: gpt-4
      output_path: generated_examples.pkl
      input_function:
        name: headline_generation
        description: Generate a landing page headline for a tech startup business.
        parameters:
          tech_startup_business: str
variations:
  - name: task
    generator_name: openai_prompt_based_variation_generator
    generator_config:
      number_of_variations: 2
      model_name: gpt-4
      output_path: generated_prompts.pkl
      variables:
        - tech_startup_business
      prompt:
        - role: system
          content: Write concise prompts for GPT-4.
    variations:
      - value_type: str
        value: Generate landing page headline for {tech_startup_business}
        instantiated_value: Generate landing page headline for {tech_startup_business}
        variation_id: null
```

The custom function should use `StringWrapper(name="task", variables={"tech_startup_business": tech_startup_business}, state=state)` so generated/manual prompt values are applied.

## Workflow guidance

1. Start with a tiny run: one or two generated examples and one or two variations.
2. Always set `output_path` for provider-backed generators so reruns load cached pickles instead of paying/calling again.
3. Keep `variables` explicit for prompt variation generation; generated prompt outputs must contain `{variable}` placeholders when configured.
4. For document generation, start with `source: text` before file or Google Drive sources.
5. Route generated outputs into [evaluation-optimization](../evaluation-optimization/SKILL.md) for evaluator, selector, and enhancer design.

## Safety and cost boundaries

- OpenAI generators call network services and can bill. Confirm credentials and budget before running.
- Document file/drive sources can invoke loaders, OCR, Google APIs, and local file reads. Use only approved documents.
- Retrieval demos that use embeddings/FAISS/OpenAI are reference patterns, not default runtime paths.
- If the user only needs a static prompt list, use manual `variations` instead of provider-backed generation.
