# Multimodal Models and Arguments

## `VisModelArguments`

Important fields in the inspected checkout:

- `model_name_or_path`
- `custom_model`
- `pretrained_language_projection_path`
- `custom_vision_model`
- `image_encoder_name_or_path`
- `qformer_name_or_path`
- `llm_model_name_or_path`
- `low_resource`
- `use_prompt_cache`
- `prompt_cache_path`
- `llava_loading`
- `with_qformer`
- `vision_select_layer`
- `llava_pretrain_model_path`
- `save_pretrain_model_path`

## `MultiModalDatasetArguments`

Important fields:

- `dataset_path`
- `image_folder`
- `image_aspect_ratio`
- `is_multimodal`
- `use_image_start_end`
- `sep_style`

## Model-Side Helpers

- `CustomAutoVision2SeqModel` in `lmflow.models.vision2seq_model`
- `update_custom_config` in `lmflow.utils.multimodal`
- `load_llava_pretrain_model` in `lmflow.utils.multimodal`
- `adapt_llava_model_to_lmflow_type` in `lmflow.utils.multimodal`

## Operational Notes

- `custom_vision_model=True` selects the custom CLIP-style vision tower path.
- `llava_loading=True` is used when a pre-converted multimodal checkpoint needs to be mapped into LMFlow keys.
- `save_language_projection=True` is the stage-1 handoff flag that keeps the projector checkpoint for later reuse.
- `pretrained_language_projection_path` is the stage-2 bridge into the finetuning phase.
- `vision_select_feature` is used internally by the vision tower, but it is not a stable top-level dataclass field in this checkout.
