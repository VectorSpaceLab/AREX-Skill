# Generators reference

## `openai_prompt_data_generator`

YAML location: `dataset.data_generators.openai_prompt_data_generator`

Config class: `OpenAIPromptBasedGeneratorConfig`

Important fields:

| Field | Meaning |
| --- | --- |
| `model_name` | OpenAI model name; code uses `openai.ChatCompletion.create`. |
| `prompt` | String or chat-message list instructing generation. |
| `input_function` | Dict with `name`, `description`, and `parameters`; generated examples must match `parameters`. |
| `number_of_examples` | Number of examples to collect. |
| `chunk_size` | Yield chunk size. |
| `output_path` | Pickle cache path; if it exists, generator loads examples instead of calling the provider. |
| `output_csv_path` | Optional CSV export path. |
| `diversify` | When true, generation prompts include recent examples to avoid duplicates. |
| `single_shot` | Ask for a list of examples in one response. |
| `expected_param_name` | Field to extract from generated examples into `InputData.expected_result`. |
| `fixed_input` | Extra key/values merged into every generated example. |

Output parsing extracts dictionary-shaped model output and keeps only keys listed in `input_function.parameters`.

## `document_data_generator`

YAML location: `dataset.data_generators.document_data_generator`

Config class: `DocumentDataGeneratorConfig`

Important fields:

| Field | Meaning |
| --- | --- |
| `source` | `text`, `file`, or `drive`. |
| `document` | Text body, local file path, or Google Drive file id according to `source`. |
| `document_chunk_size` | Intended chunk size for document splitting. |
| `num_questions_per_chunk` | Number of questions requested per chunk. |
| `question_gen_query` | Prompt query appended to context. |
| `text_question_template` | Optional question template. |
| `model_name`, `prompt`, `output_path`, `output_csv_path` | Provider and caching controls. |

Use `source: text` for the first smoke test. File/drive modes can require unstructured parsing, OCR, or Google credentials.

## `openai_prompt_based_variation_generator`

YAML location: `variations[].generator_name: openai_prompt_based_variation_generator`

Config class: `OpenAIPromptBasedVariationGeneratorConfig`

Important fields:

| Field | Meaning |
| --- | --- |
| `number_of_variations` | Number of `WrapperVariation` strings to generate. |
| `model_name` | OpenAI model name. |
| `prompt` | String or chat-message list. |
| `variables` | Required placeholders, e.g. `[tech_startup_business]`; generated output must include `{tech_startup_business}`. |
| `diversify` | If true, prompts include recent generated outputs and use higher-temperature completion. |
| `max_tokens` | Provider max token limit. |
| `output_path` | Pickle cache of generated `WrapperVariation` objects. |

Generated variations are strings with `value_type: str`.

## `chain_of_density_prompt_generator`

YAML location: `variations[].generator_name: chain_of_density_prompt_generator`

Config class: `BaseVariationGeneratorConfig`

Behavior: returns one fixed chain-of-density summarization prompt as a `WrapperVariation`. It is offline and deterministic.

## `self_exemplar`

YAML location: `variations[].generator_name: self_exemplar`

Config class: `SelfExemplarConfig`

Fields include:

- `start_prompt`
- `problem_prompt`
- `relevant_problems_prompt`
- `core_concept_prompt`
- `tutorial_prompt`
- `end_prompt`

Behavior: constructs one prompt that asks the model to recall relevant problems, identify concepts, optionally include a tutorial, then solve the initial problem.
