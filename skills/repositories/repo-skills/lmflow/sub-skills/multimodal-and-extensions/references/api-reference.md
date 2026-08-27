# Multimodal API Reference

## Dataset / Collator

- `lmflow.datasets.CustomMultiModalDataset`
- `lmflow.datasets.multi_modal_dataset.DataCollatorForSupervisedDataset`
- `Dataset(..., backend="custom_multi_modal")`

## Model / Helper Functions

- `lmflow.models.vision2seq_model.CustomAutoVision2SeqModel`
- `lmflow.utils.multimodal.update_custom_config`
- `lmflow.utils.multimodal.load_llava_pretrain_model`
- `lmflow.utils.multimodal.adapt_llava_model_to_lmflow_type`

## Template Surface

- `lmflow.utils.llava_conversation_lib.conv_templates`
- `lmflow.utils.constants.DEFAULT_IMAGE_TOKEN`
- `lmflow.utils.constants.DEFAULT_IM_START_TOKEN`
- `lmflow.utils.constants.DEFAULT_IM_END_TOKEN`

## Availability Checks

- `lmflow.utils.versioning.is_multimodal_available()`
- `lmflow.utils.versioning.is_gradio_available()`
