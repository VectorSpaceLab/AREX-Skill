# Registry and Plugins

ms-swift customization is registry-driven. Dataset metadata goes into `DATASET_MAPPING`, model metadata into `MODEL_MAPPING`, and template metadata into `TEMPLATE_MAPPING`. The CLI can load extra registration code with `--external_plugins plugin.py` and extra dataset metadata with `--custom_dataset_info dataset_info.json`.

## Choose the Lightest Customization Path

| Need | Recommended path |
| --- | --- |
| A local JSONL/JSON/CSV/TXT file already has usable columns | Pass it directly with `--dataset` and optional `--columns`. |
| A reusable dataset alias, subsets, splits, or stable column mapping | Use `--custom_dataset_info dataset_info.json`. |
| A custom row transformation, custom loader, model type, or template | Use `--external_plugins plugin.py`. |
| A new model architecture or multimodal processor behavior | Register both model and template, and plan custom loader/template code if needed. |

Prefer `--dataset` first. Move to metadata or plugins only when repeated use or code-level preprocessing is required.

## Inspect Installed Registries

Use the bundled script before overriding types:

```bash
python scripts/inspect_registries.py --datasets --models --templates --contains qwen2_5
python scripts/inspect_registries.py --models --limit 20 --json
```

This imports installed `swift` and reads mapping objects. It does not call `get_processor`, download models, or run training.

Optional dependency caveats:

- Some registry rows mention extra package requirements such as newer `transformers`, quantization libraries, or backend-specific dependencies.
- Megatron support in generated supported-model tables may depend on optional `mcore_bridge`/Megatron extras. Missing Megatron extras do not invalidate normal registry inspection.
- Evaluation extras such as evalscope are not required for this sub-skill and should be treated as optional for eval workflows.

## Custom Dataset Info

A minimal metadata file is a JSON list. Each entry needs one source identifier: `ms_dataset_id`, `hf_dataset_id`, or `dataset_path`.

```json
[
  {
    "dataset_name": "my-sft-jsonl",
    "dataset_path": "train.jsonl",
    "columns": {
      "prompt": "query",
      "answer": "response"
    }
  },
  {
    "ms_dataset_id": "namespace/dataset",
    "subsets": [
      {
        "subset": "train",
        "split": ["train"],
        "columns": {
          "problem": "query",
          "solution": "response"
        }
      }
    ]
  }
]
```

Use it with:

```bash
swift sft --custom_dataset_info dataset_info.json --dataset my-sft-jsonl
```

Relative `dataset_path` values are resolved relative to the metadata file by ms-swift. For portable projects, keep dataset files and metadata together and avoid machine-specific absolute paths.

## External Plugin Safety

A plugin is imported by ms-swift for registration side effects. Keep import-time behavior deterministic and cheap:

- Define classes/functions and call `register_dataset`, `register_model`, or `register_template` at module import.
- Do not start training, inference, downloads, subprocesses, or large file reads at import time.
- Guard demos with `if __name__ == "__main__":`.
- Use unique `dataset_name`, `model_type`, and `template_type` identifiers.
- Avoid `exist_ok=True` unless intentionally replacing an existing registration.
- Print little or nothing at import time; noisy plugins make CLI debugging harder.

Load a plugin with any relevant route:

```bash
swift sft --external_plugins custom_ms_swift_plugin.py --dataset my_dataset_alias ...
swift infer --external_plugins custom_ms_swift_plugin.py --model ./models/my-model --model_type my_model_type ...
```

## Dataset Plugin Skeleton

```python
from typing import Any, Dict, Optional

from swift.dataset import DatasetMeta, ResponsePreprocessor, register_dataset


class SimilarityPreprocessor(ResponsePreprocessor):
    def preprocess(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = (
            "Task: score semantic similarity from 0.0 to 5.0.\n"
            f"Sentence 1: {row['text1']}\n"
            f"Sentence 2: {row['text2']}\n"
            "Score:"
        )
        return super().preprocess({"query": query, "response": str(row["label"])})


register_dataset(
    DatasetMeta(
        dataset_name="my_similarity_dataset",
        dataset_path="data/train.jsonl",
        preprocess_func=SimilarityPreprocessor(),
        tags=["custom", "sft"],
    )
)
```

When registering hub datasets, use `ms_dataset_id` or `hf_dataset_id`. When registering local files, prefer a project-relative `dataset_path` and load the plugin from the project root so paths resolve predictably.

## Model and Template Plugin Skeleton

```python
from swift.model import Model, ModelGroup, ModelMeta, register_model
from swift.template import TemplateMeta, register_template

register_template(
    TemplateMeta(
        template_type="my_chat_template",
        prefix=["<s>"],
        system_prefix=["<s><system>\n{{SYSTEM}}\n"],
        prompt=["<user>\n{{QUERY}}\n<assistant>\n"],
        chat_sep=["</assistant>\n"],
        suffix=["</assistant>"],
        default_system="You are a helpful assistant.",
        agent_template="hermes",
    )
)

register_model(
    ModelMeta(
        model_type="my_model_type",
        model_groups=[
            ModelGroup(
                [Model(ms_model_id="Org/My-Model", hf_model_id="Org/My-Model")],
                template="my_chat_template",
                tags=["custom"],
            )
        ],
        template="my_chat_template",
        architectures=["MyForCausalLM"],
        is_multimodal=False,
    )
)
```

For a multimodal model, set `is_multimodal=True` and specify `model_arch` when training needs module prefixes for LLM/vision/aligner components. If the default loader is not enough, provide a custom loader class that returns the model and processor expected by ms-swift. Keep loader code focused on loading; do not encode dataset-specific assumptions there.

## Key Registration Objects

Dataset registration uses:

- `DatasetMeta`: source IDs/paths, aliases, subsets, splits, `preprocess_func`, `loader`, tags, and help text.
- `SubsetDataset`: named subsets with per-subset split and preprocessor overrides.
- `register_dataset(dataset_meta, exist_ok=False)`: adds the metadata to `DATASET_MAPPING`.
- `AutoPreprocessor`, `MessagesPreprocessor`, `AlpacaPreprocessor`, `ResponsePreprocessor`: reusable preprocessing classes.

Model registration uses:

- `Model`: ModelScope ID, Hugging Face ID, local model path, and revisions.
- `ModelGroup`: a group of model IDs with optional template, requires, ignore patterns, and tags.
- `ModelMeta`: `model_type`, model groups, loader, template, `model_arch`, architectures, extra saved files, dtype, multimodal/reward/task flags, requirements, and tags.
- `register_model(model_meta, exist_ok=False)`: adds the metadata to `MODEL_MAPPING`.

Template registration uses:

- `TemplateMeta`: `template_type`, `prefix`, `prompt`, `chat_sep`, `suffix`, optional `template_cls`, `system_prefix`, `default_system`, stop words, `agent_template`, and thinking controls.
- `register_template(template_meta, exist_ok=False)`: adds the metadata to `TEMPLATE_MAPPING`.

## Supported Registry Documentation

Installed ms-swift exposes supported registry data programmatically. The public supported-model table includes model ID, model type, default template, default agent template, requirements, Megatron support, tags, and Hugging Face ID. The supported-dataset table includes dataset ID, subsets, size/statistics, tags, and optional Hugging Face ID.

Use generated documentation as a human aid, but verify active behavior against the installed package mappings because plugins and package versions can change the live registry.

## Plugin Plan for a New Multimodal Model

For a new multimodal model, plan these fields before coding:

1. `model_type`: unique lowercase identifier for CLI `--model_type`.
2. `template_type`: unique template identifier for CLI `--template`.
3. Model IDs or local paths in `ModelGroup`.
4. `architectures`: values expected in `config.json` for automatic matching.
5. `model_arch`: module prefixes needed by training, such as language model, vision tower, and projector names.
6. `is_multimodal=True` and any loader/processor customization.
7. Template multimodal tokens and placeholder handling for `<image>`, `<video>`, `<audio>`, grounding, or agent tools.
8. Required optional packages and a small offline import test that only inspects mapping entries.

After writing the plugin, run:

```bash
python scripts/inspect_registries.py --external-plugin custom_ms_swift_plugin.py --models --templates --contains my_model_type
python scripts/inspect_template_encoding.py --model ./local-model-dir --model-type my_model_type --template my_chat_template --attempt --no-download
```

The second command may still need tokenizer/processor files already available locally; keep it optional and do not make it the only validation step.
