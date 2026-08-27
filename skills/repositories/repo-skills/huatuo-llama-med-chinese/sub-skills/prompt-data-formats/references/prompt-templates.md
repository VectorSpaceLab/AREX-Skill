# Prompt Templates and Prompter Behavior

This repository uses a small JSON-template layer to turn instruction records into the text passed to a causal language model. The behavior is simple but has several sharp edges that matter for data preparation and inference debugging.

## Prompter lookup model

The `Prompter` class accepts a `template_name` and builds a filename as:

```text
templates/<template_name>.json
```

Important consequences:

- The lookup is relative to the current working directory, not relative to the Python file that defines `Prompter`.
- Running a script from outside an asset root that contains `templates/` can fail with a message equivalent to `Can't read templates/<name>.json`.
- An empty template name is replaced with `alpaca`, but the bundled template set covered here contains `med_template`, `literature_template`, and `bloom_deploy`; it does not include an `alpaca.json` template.
- `generate_prompt(instruction, input, label)` uses `prompt_input` only when `input` is truthy. Empty strings, `None`, and other falsey values use `prompt_no_input`.
- `get_response(output)` splits generated text on `response_split` and returns the text after the first split marker. If the marker is absent, has the wrong colon variant, or appears in the prompt differently than in the model output, response extraction fails.

## Template schema

A usable no-input template has these required keys:

| Key | Meaning | Validation note |
| --- | --- | --- |
| `description` | Human-readable template description. | Non-empty string. |
| `prompt_no_input` | Prompt format used when the record has no usable `input`. | Must contain `{instruction}`. |
| `response_split` | Exact separator used to strip the prompt from decoded model output. | Must match the answer marker, including Chinese/full-width punctuation. |

`prompt_input` is optional for this asset set, because `literature_template` is no-input only. If a template may be used with non-empty `input`, it must also define `prompt_input`; otherwise `generate_prompt(..., input='...')` raises a key error.

## Bundled template behavior

### `med_template`

Use for ordinary medical instruction data and the LoRA medical model prompt style.

```json
{
  "description": "Template used by Med Instruction Tuning",
  "prompt_input": "下面是一个问题，运用医学知识来正确回答提问.\n### 问题:\n{instruction}\n### 回答:\n",
  "prompt_no_input": "下面是一个问题，运用医学知识来正确回答提问.\n### 问题:\n{instruction}\n### 回答:\n",
  "response_split": "### 回答:"
}
```

Notes:

- `prompt_input` and `prompt_no_input` are effectively the same; neither includes an `{input}` placeholder.
- The response marker uses an ASCII colon: `### 回答:`.

### `bloom_deploy`

Use for BLOOM-style deployment prompts in the bundled assets.

```json
{
  "description": "Template used by Med Instruction Tuning",
  "prompt_input": "下面是一个问题，运用医学知识来正确回答提问.\n{instruction}\n\n\n### 回答：\n",
  "prompt_no_input": "下面是一个问题，运用医学知识来正确回答提问.\n{instruction}\n### 回答：\n",
  "response_split": "### 回答："
}
```

Notes:

- The response marker uses a full-width Chinese colon: `### 回答：`.
- Do not mix this marker with the ASCII-colon marker from `med_template` when extracting responses.

### `literature_template`

Use for literature-dialogue records whose prompt is stored entirely in `instruction` and whose `input` field is empty.

```json
{
  "description": "Template used by Alpaca-LoRA.",
  "prompt_no_input": "以下是描述任务的说明，编写适当地回复完成请求的响应。\n\n ### 说明:\n{instruction}\n\n### 回复:\n",
  "response_split": "### 回复:"
}
```

Notes:

- There is no `prompt_input` key. Use this template only with empty `input` values unless you add and validate a `prompt_input` variant.
- The answer marker is `### 回复:`, not `### 回答:`.

## Prompt assembly examples

For an instruction record:

```json
{"instruction": "麻风病和儿童哮喘的病因是否一致？", "input": "", "output": "不一致，麻风病的病因是麻风分枝杆菌，而儿童哮喘的病因是气候、药物、吸入过敏原等。"}
```

`med_template` produces:

```text
下面是一个问题，运用医学知识来正确回答提问.
### 问题:
麻风病和儿童哮喘的病因是否一致？
### 回答:
```

During training, the label/output is appended directly after the prompt. During inference, the model is expected to generate text after the answer marker, and response extraction splits on that same marker.

## Safe template edits

- Keep `{instruction}` exactly where the instruction should appear.
- Keep `response_split` byte-for-byte consistent with the final answer marker in the prompt strings.
- Add `prompt_input` before using non-empty `input` with a no-input-only template.
- Test punctuation variants explicitly; ASCII `:` and Chinese `：` are different separators.
- Avoid putting additional copies of `response_split` inside the expected answer text, because extraction returns the text after the first split marker.
