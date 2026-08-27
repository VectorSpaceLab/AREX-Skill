# Registry overview

YiVal discovers components through process-local registries. A registry is populated when the implementation module is imported. Importing `yival.cli.init`, `yival.experiment.utils`, or the specific implementation modules is usually enough to register built-ins.

## Built-in ids observed at the baseline

| Category | Base class | Built-in ids |
| --- | --- | --- |
| Readers | `BaseReader` | `csv_reader`, `huggingface_dataset_reader` |
| Data generators | `BaseDataGenerator` | `document_data_generator`, `openai_prompt_data_generator` |
| Variation generators | `BaseVariationGenerator` | `chain_of_density_prompt_generator`, `openai_prompt_based_variation_generator`, `self_exemplar` |
| Evaluators | `BaseEvaluator` | `alpaca_eval_evaluator`, `bertscore_evaluator`, `openai_elo_evaluator`, `openai_prompt_based_evaluator`, `python_validation_evaluator`, `rouge_evaluator`, `string_expected_result` |
| Selection strategies | `SelectionStrategy` | `ahp_selection` |
| Enhancers | `BaseCombinationEnhancer` | `openai_prompt_based_combination_enhancer`, `optimize_by_prompt_enhancer`, `pe2_enhancer` |
| Wrappers | `BaseWrapper` | `string_wrapper` |
| Trainers | `BaseTrainer` | Trainer registry can be empty without optional trainer extras; local SFT is out-of-scope unless requested. |

## Config-key mapping

| YAML section | Registry used | Common built-in id |
| --- | --- | --- |
| `dataset.reader` | `BaseReader` | `csv_reader`, `huggingface_dataset_reader` |
| `dataset.data_generators` | `BaseDataGenerator` | `openai_prompt_data_generator`, `document_data_generator` |
| `variations[].generator_name` | `BaseVariationGenerator` | `openai_prompt_based_variation_generator`, `chain_of_density_prompt_generator`, `self_exemplar` |
| `evaluators[].name` | `BaseEvaluator` | `string_expected_result`, `bertscore_evaluator`, `openai_prompt_based_evaluator` |
| `selection_strategy` top-level key | `SelectionStrategy` | `ahp_selection` |
| `enhancer.name` | `BaseCombinationEnhancer` | `optimize_by_prompt_enhancer`, `pe2_enhancer`, `openai_prompt_based_combination_enhancer` |
| `wrapper_configs` and `StringWrapper` names | `BaseWrapper` | `string_wrapper` |

## Custom registry sections

| Custom section | Expected mapping keys |
| --- | --- |
| `custom_reader` | `name: {class: <module_or_path.Class>, config_cls: <module_or_path.Config>}` |
| `custom_wrappers` | same pattern |
| `custom_evaluators` | same pattern |
| `custom_data_generators` | same pattern |
| `custom_variation_generators` | same pattern |
| `custom_selection_strategies` | same pattern |
| `custom_enhancers` | same pattern |

Implementation note: YiVal's registration helpers look for `class` and optional `config_cls` keys. Some CLI init options call the key `config_path`, but runtime registration helpers use `config_cls`; when writing YAML manually, prefer `config_cls`.

## Registry smoke probe

Run this after installing YiVal:

```bash
python scripts/check_install.py
```

A healthy core environment should show non-empty reader, data generator, variation generator, evaluator, strategy, enhancer, and wrapper registries after the script imports built-in modules.
