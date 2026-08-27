# API reference

## Verified signatures

```python
encode_prompt(prompt_instructions)
post_process_gpt3_response(num_prompt_instructions, response)
generate_instruction_following_data(output_dir='./', seed_tasks_path='./seed_tasks.jsonl', num_instructions_to_generate=100, model_name='text-davinci-003', num_prompt_instructions=3, request_batch_size=5, temperature=1.0, top_p=1.0, num_cpus=16)
```

```python
class OpenAIDecodingArguments:
    max_tokens: int = 1800
    temperature: float = 0.2
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    stop: Optional[Sequence[str]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    suffix: Optional[str] = None
    logprobs: Optional[int] = None
    echo: bool = False
```

```python
openai_completion(prompts, decoding_args, model_name='text-davinci-003', sleep_time=2, batch_size=1, max_instances=sys.maxsize, max_batches=sys.maxsize, return_text=False, **decoding_kwargs)
```

## `encode_prompt(prompt_instructions)`

Input shape:
- a list of dictionaries with `instruction`, `input`, and `output`
- `input` may be empty, in which case the source prompt uses `<noinput>`

Behavior:
- loads the prompt template
- normalizes whitespace and trims trailing `:` from each instruction
- emits numbered `Instruction` / `Input` / `Output` blocks
- ends with `###` and the next `Instruction:` slot

## `post_process_gpt3_response(num_prompt_instructions, response)`

Input shape:
- `response` is an OpenAI completion choice-like object with `text` and `finish_reason`

Behavior:
- splits the generated text on `###`
- parses numbered triples
- discards the last chunk when `finish_reason == 'length'`
- filters too-short or too-long instructions
- rejects blacklisted content, `Write a program...`, punctuation starts, and non-ASCII starts

Return value:
- a list of `{instruction, input, output}` records

## `generate_instruction_following_data(...)`

Source defaults:
- `output_dir='./'`
- `seed_tasks_path='./seed_tasks.jsonl'`
- `num_instructions_to_generate=100`
- `model_name='text-davinci-003'`
- `num_prompt_instructions=3`
- `request_batch_size=5`
- `temperature=1.0`
- `top_p=1.0`
- `num_cpus=16`

Internal live-run behavior:
- seed instructions come from `seed_tasks.jsonl`
- machine instructions are loaded from `regen.json` if it exists
- the loop batches prompt renders, calls the OpenAI completion helper, parses the response, and deduplicates with ROUGE-L against all known instructions
- candidates with max ROUGE-L f-measure above `0.7` are dropped
- accepted records receive `most_similar_instructions` and `avg_similarity_score` metadata before being written back to `regen.json`

## `OpenAIDecodingArguments`

Defaults matter because the live generator overrides them per request:
- `temperature` from the function argument
- `n=1`
- `max_tokens=3072`
- `top_p` from the function argument
- `stop=["\n20", "20.", "20."]`

## `openai_completion(...)`

Important caveats:
- uses the legacy `openai.Completion.create` API surface
- retries on `openai.error.OpenAIError`
- reduces `max_tokens` when the error says to reduce prompt length
- sleeps between retries on rate-limit style errors
- batches prompts only for the non-chat completion path
- can return text-only output when `return_text=True`

## Seed-task schema

A `seed_tasks.jsonl` record has this shape:

```json
{
  "instruction": "...",
  "name": "optional_label",
  "instances": [
    {
      "input": "...",
      "output": "..."
    }
  ],
  "is_classification": false
}
```

Required facts used by this sub-skill:
- `instruction` is the primary prompt example text.
- the first `instances` entry carries the example `input` and `output`.
- empty inputs may be represented as `""` and are rendered as `<noinput>`.

## `regen.json` record schema

Accepted machine-generated records typically include:
- `instruction`
- `input`
- `output`
- `most_similar_instructions`
- `avg_similarity_score`

## Compatibility notes

- This workflow is pinned to the older OpenAI completion model family used by the source repository.
- If you only have the modern OpenAI SDK, use the bundled offline scripts for prompt debugging and completion parsing, and treat live generation as a separate compatibility task.
