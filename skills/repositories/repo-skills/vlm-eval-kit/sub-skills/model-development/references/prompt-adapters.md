# Prompt adapters and model-specific payload hooks

Prompt adapters let an API transport stay generic while preserving model-family-specific prompt construction, media ordering, payload fields, and output postprocessing. This reference is distilled from `vlmeval/api/adapters/base.py`, `vlmeval/api/adapters/__init__.py`, `vlmeval/api/adapters/internvl2.py`, `vlmeval/api/adapters/internvl3.py`, `vlmeval/api/adapters/interns1_1.py`, `vlmeval/api/openai_sdk.py`, `vlmeval/api/lmdeploy.py`, `run.py`, `README.md`, and `docs/en/Quickstart.md`.

## Adapter registry

`vlmeval/api/adapters/base.py` defines a global adapter registry:

| Function | Purpose |
| --- | --- |
| `register_adapter(name, factory=None)` | Register a class or factory under a string name; usable as a decorator. |
| `build_adapter(name, **kwargs)` | Instantiate the registered adapter or raise `KeyError` listing available names. |
| `get_adapter_registry()` | Return a copy of the registry for inspection. |

Adapter modules are imported in `vlmeval/api/adapters/__init__.py`, so a new adapter must be imported there if it should be available by name.

## `ModelAdapter` hooks

Subclass `ModelAdapter` and override only the hooks you need:

| Hook | Default | Override when |
| --- | --- | --- |
| `dump_image(line, dataset)` | Calls injected `dump_image_func`. | You need custom sample-to-image path handling. |
| `override_model_args(dataset, gen_kwargs)` | `{}` | A dataset needs different `system_prompt`, `temperature`, token limits, or provider kwargs. |
| `use_custom_prompt(dataset, system_prompt=None)` | `False` | The adapter should replace dataset prompt construction for selected datasets. |
| `build_prompt(line, dataset=None)` | raises `NotImplementedError` | `use_custom_prompt` can return `True`; must return a VLMEvalKit message list. |
| `process_inputs(inputs, dataset=None)` | identity | The provider needs reordered images/text, image-token replacement, resized images, or video prompt conversion. |
| `process_payload(payload, dataset=None)` | identity | The HTTP payload needs extra media fields, max patches, reasoning flags, or provider-specific body changes. |
| `postprocess(response, dataset=None)` | identity | The answer needs thinking-strip, MPO postprocess, summary extraction, or formatting cleanup. |

`OpenAISDKWrapper` wires adapters into runtime behavior:

1. `use_custom_prompt()` and `build_prompt()` delegate to the adapter when present.
2. `set_dump_image()` injects the dataset image dump callback into the adapter.
3. `generate_inner()` calls `override_model_args()`, `process_inputs()`, provider `prepare_inputs()`, `process_payload()`, the HTTP request, and finally `postprocess()`.

`LMDeployAPI` accepts adapters through the `custom_prompt` kwarg; `run.py --base-url ... --custom-prompt NAME` passes the name through to `LMDeployAPI`.

## Minimal adapter skeleton

```python
from vlmeval.api.adapters.base import ModelAdapter, register_adapter

@register_adapter('my_adapter')
class MyAdapter(ModelAdapter):
    def use_custom_prompt(self, dataset, system_prompt=None):
        return dataset in {'MMBench_DEV_EN', 'MMVet'}

    def build_prompt(self, line, dataset=None):
        image_paths = self.dump_image(line, dataset)
        prompt = line['question']
        return [*(dict(type='image', value=p) for p in image_paths), dict(type='text', value=prompt)]

    def process_inputs(self, inputs, dataset=None):
        return inputs

    def process_payload(self, payload, dataset=None):
        return payload

    def postprocess(self, response, dataset=None):
        return response.strip()
```

After adding the file, import `MyAdapter` in `vlmeval/api/adapters/__init__.py` so `build_adapter('my_adapter')` can find it.

## InternVL adapter patterns

The InternVL adapters show how to make prompt behavior dataset-aware without hard-coding it into `LMDeployAPI`.

### `InternVL2Adapter`

Registered names include `internvl2` and `internvl2-mpo-cot`.

- `use_custom_prompt()` disables adapter prompts for selected physics/science, alignment, real-world, video, and special system-prompt cases; otherwise it usually enables custom prompts.
- `build_prompt()` branches by `DATASET_TYPE(dataset)`:
  - `Y/N`: appends short-answer or yes/no instructions for selected datasets.
  - `MCQ`: uses InternVL multi-choice helpers; optionally adds chain-of-thought prompt when `USE_COT=1`.
  - `VQA`: chooses detailed-answer, short-answer, or plain-question prompts by dataset family.
  - `GUI`: loads GUI templates and formats action/navigation prompts.
  - `ChartMimic`: resolves image path from the data root image directory.
- `process_payload()` adds `max_dynamic_patch` to image payload entries based on dataset family.
- `postprocess()` applies MPO post-processing when the MPO/COT variant is used.

### `InternVL3Adapter`

Registered name: `internvl3`.

- `override_model_args()` injects a thinking-oriented `system_prompt` for selected reasoning datasets and otherwise forces `temperature=0`.
- `use_custom_prompt()` enables prompts for `Y/N`, `MCQ`, `VQA`, and `GUI` dataset types except for explicit exclusions and video datasets.
- `build_prompt()` returns image messages before text and shares many dataset-type branches with InternVL2.
- `process_inputs()` reorganizes interleaved prompts, builds video prompts when needed, upsizes MMMU images, replaces `<image>` with `<IMAGE_TOKEN>`, and returns image items plus text.
- `process_payload()` adds dynamic patch limits for high-resolution or GUI datasets.
- `postprocess()` strips content inside `<think>...</think>` when thinking split is enabled and returns only the final answer portion.

### `InternS1_1` adapters

Registered names: `interns1_1_no_think` and `interns1_1_think`.

- The no-think adapter follows InternVL3-style prompt selection and strips `<think>` blocks from responses.
- The think adapter enables custom prompts only for selected science/physics datasets and has specialized builders for SFE and IPhO-style records.
- Both adapters use `process_inputs()` to reorganize media/text and replace `<image>` markers.
- Their `postprocess()` logs thinking content and returns the answer after `</think>` when present.

## Thinking-output split

VLMEvalKit has two thinking-output mechanisms:

1. Evaluation-time `SPLIT_THINK=True`: `vlmeval/inference.py` stores parsed thinking content in a `thinking` column/key and uses `model.split_thinking` when provided; otherwise it parses default `<think>...</think>` tags.
2. Adapter-level `postprocess()`: adapters such as InternVL3 and InternS1_1 can strip thinking content before returning the prediction string.

Use adapter-level `postprocess()` when the served API model always returns hidden/reasoning text that would break answer extraction. Use `SPLIT_THINK=True` when preserving thinking records in prediction output is desired. Avoid double-stripping unless you have verified which layer owns the split.

## Custom prompt precedence

VLMEvalKit supports prompt customization on both dataset and model/API sides. For model-side custom prompts:

- `use_custom_prompt(dataset)` must return `True` for the target dataset.
- `build_prompt(line, dataset)` must return the VLMEvalKit message list.
- `set_dump_image()` must be called by the evaluation pipeline so custom prompts can access dumped image paths.
- If both dataset and model prompt builders are available and the model/API wrapper reports custom prompt support, the model-side prompt takes precedence.

When debugging, inspect whether the model/API wrapper logs that it is using custom prompt for the dataset, then verify the adapter name and `use_custom_prompt()` branch.

## Media and payload rules

- The adapter's `build_prompt()` should output VLMEvalKit internal messages, not HTTP payloads.
- Use `process_inputs()` to rearrange internal messages before provider formatting.
- Use `process_payload()` only after the provider wrapper has created OpenAI-style payload JSON.
- Preserve role-keyed chat histories when the provider supports multi-turn inputs; last role must be `user`.
- For native video endpoints, combine `--video-llm`/`video_llm=True` with a provider that understands `video_url` content. Otherwise use frame-based dataset handling routed through evaluation/benchmark logic.
