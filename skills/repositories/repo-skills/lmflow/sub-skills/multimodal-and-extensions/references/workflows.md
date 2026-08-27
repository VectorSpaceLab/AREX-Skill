# Multimodal Workflows

## 1. Legacy Training / Stage 1

Goal: learn the projector and base multimodal alignment from image-caption style data.

Typical settings:

- `custom_model=True`
- `custom_vision_model=True`
- `image_encoder_name_or_path` set to the vision tower
- `llm_model_name_or_path` set to the language backbone
- `image_folder` pointing at the image corpus
- `image_aspect_ratio="pad"` for uneven images
- `save_language_projection=True`

This is a compatibility workflow and should only be promised when the current package surface is ready for it.

## 2. Legacy Training / Stage 2

Goal: instruction-tune the multimodal checkpoint on LLaVA-style conversations.

Typical settings:

- `llava_loading=True`
- `llava_pretrain_model_path` or `pretrained_language_projection_path`
- `sep_style="v1"`
- `use_image_start_end=True`
- `custom_vision_model=True`
- `image_folder` pointing at the instruction images

## 3. Visual Chat / CLI

Goal: produce a single answer or a multi-turn image-backed reply.

Typical settings:

- `type="image_text"`
- `chatbot_type` set to the LLaVA-style route when using the core image token path
- `prompt_structure` and `end_string` for UI or streaming loops
- `task="image_caption"` for single-turn captioning
- `task="vqa"` for question answering

## 4. Gradio UI

Goal: wrap the same visual-chat generation path in a browser interface.

Typical settings:

- `gradio` extra installed
- upload button for one or more images
- text box tied to the same prompt builder
- same image preprocessing and decode path as the CLI route

## Extension Boundary

- Tool inference is not owned here; route it to the core inference skill.
- Long-context template selection is usually handled by the generic template skill.
- Vocabulary or tokenizer-extension work belongs to the model/data customization path, not to the visual-chat path.
