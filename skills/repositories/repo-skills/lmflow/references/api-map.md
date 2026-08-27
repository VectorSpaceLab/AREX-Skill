# API Map

## Purpose

Read this when you need a fast overview of the LMFlow package surface before diving into a sub-skill.

## Core Package Surface

### `lmflow.args`
Verified dataclasses in the inspected checkout:

- `ModelArguments`
- `VisModelArguments`
- `DatasetArguments`
- `MultiModalDatasetArguments`
- `FinetunerArguments`
- `RewardModelTunerArguments`
- `EvaluatorArguments`
- `InferencerArguments`
- `RaftAlignerArguments`
- `BenchmarkingArguments`
- `DPOAlignerArguments`
- `DPOv2AlignerArguments`
- `IterativeAlignerArguments`
- `IterativeDPOAlignerArguments`

Important route helper:

- `AutoArguments.get_pipeline_args_class(pipeline_name)`

### `lmflow.datasets.Dataset`
Key methods confirmed from source and inspection:

- `__init__(data_args, backend="huggingface")`
- `from_dict(dict_obj, *args, **kwargs)`
- `create_from_dict(dict_obj, *args, **kwargs)`
- `to_dict()`
- `to_list()`
- `map(...)`
- `save(file_path, format="json")`
- `sample(n, seed=42)`
- `train_test_split(test_size=0.2, shuffle=True, seed=42)`
- `drop_instances(indices)`
- `sanity_check(...)`

Dataset backends and supported types include `text_only`, `text2text`, `float_only`, `image_text`, `conversation`, `paired_conversation`, `paired_text_to_text`, `text_to_textlist`, and `text_to_scored_textlist`.

### `lmflow.models.AutoModel`
- `AutoModel.get_model(model_args, *args, **kwargs)`
- `decoder_only` routes to `HFDecoderModel`
- `text_regression` routes to `HFTextRegressionModel`

### `lmflow.pipeline.AutoPipeline`
Base routes present in the inspected install:

- `evaluator`
- `finetuner`
- `inferencer`
- `rm_inferencer`
- `rm_tuner`

Optional routes require extras or version gates:

- `vllm_inferencer`
- `sglang_inferencer`
- `raft_aligner`
- `dpo_aligner`
- `dpov2_aligner`
- `iterative_dpo_aligner`

### `lmflow.utils.conversation_template`
`PRESET_TEMPLATES` includes at least:

- `chatglm3`, `chatml`, `deepseek`, `deepseek_v2`, `deepseek_v3`, `deepseek_r1`, `deepseek_r1_distill`, `disable`, `empty`, `empty_no_special_tokens`, `gemma`, `hymba`, `internlm2`, `llama2`, `llama3`, `llama3_for_tool`, `phi3`, `qwen2`, `qwen2_for_tool`, `qwen2_5`, `qwen2_5_1m`, `qwen2_5_math`, `qwen_qwq`, `qwen3`, `yi`, `yi1_5`, `zephyr`.

## Practical Use

- Read `data-and-templates` for dataset schemas and template customization.
- Read `training-and-optimization` for full fine-tuning and optimizer flags.
- Read `inference-and-evaluation` for engine flags and result formats.
- Read `post-training-alignment` for preference data and alignment argument families.
- Read `multimodal-and-extensions` for multimodal-only argument families.
