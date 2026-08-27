#!/usr/bin/env python
"""Render a self-contained LMFlow multimodal recipe.

This helper prints a Python heredoc for a multimodal training or single-image
chat recipe. It does not execute the recipe on its own.

Examples:
  python scripts/render_multimodal_recipe.py --mode train --model-name-or-path Salesforce/blip2-flan-t5-xxl \
    --image-encoder-name-or-path openai/clip-vit-large-patch14 --llm-model-name-or-path lmsys/vicuna-7b-v1.3 \
    --dataset-path data/train.json --image-folder data/images --output-dir output_models/mm
"""

from __future__ import annotations

import argparse
from textwrap import indent


def render_kwargs(kwargs: dict[str, object]) -> str:
    parts: list[str] = []
    for key, value in kwargs.items():
        if value is None:
            continue
        if isinstance(value, bool):
            parts.append(f"{key}={value}")
        elif isinstance(value, str):
            parts.append(f"{key}={value!r}")
        else:
            parts.append(f"{key}={value!r}")
    return ", ".join(parts)


def train_recipe(args: argparse.Namespace) -> str:
    body = f'''from transformers import AutoConfig, AutoTokenizer
from lmflow.args import AutoArguments, MultiModalDatasetArguments, VisModelArguments
from lmflow.datasets import Dataset
from lmflow.datasets.multi_modal_dataset import DataCollatorForSupervisedDataset
from lmflow.models.vision2seq_model import CustomAutoVision2SeqModel
from lmflow.pipeline.auto_pipeline import AutoPipeline
from lmflow.utils.multimodal import update_custom_config, load_llava_pretrain_model

pipeline_name = "finetuner"
PipelineArguments = AutoArguments.get_pipeline_args_class(pipeline_name)
model_args = VisModelArguments({render_kwargs({
        "model_name_or_path": args.model_name_or_path,
        "custom_model": args.custom_model,
        "custom_vision_model": args.custom_vision_model,
        "image_encoder_name_or_path": args.image_encoder_name_or_path,
        "qformer_name_or_path": args.qformer_name_or_path,
        "llm_model_name_or_path": args.llm_model_name_or_path,
        "low_resource": args.low_resource,
        "use_prompt_cache": args.use_prompt_cache,
        "prompt_cache_path": args.prompt_cache_path,
        "llava_loading": args.llava_loading,
        "with_qformer": args.with_qformer,
        "vision_select_layer": args.vision_select_layer,
        "llava_pretrain_model_path": args.llava_pretrain_model_path,
        "save_pretrain_model_path": args.save_pretrain_model_path,
        "pretrained_language_projection_path": args.pretrained_language_projection_path,
    })})
data_args = MultiModalDatasetArguments({render_kwargs({
        "dataset_path": args.dataset_path,
        "image_folder": args.image_folder,
        "image_aspect_ratio": args.image_aspect_ratio,
        "is_multimodal": True,
        "use_image_start_end": args.use_image_start_end,
        "sep_style": args.sep_style,
    })})
pipeline_args = PipelineArguments({render_kwargs({
        "output_dir": args.output_dir,
        "overwrite_output_dir": args.overwrite_output_dir,
        "num_train_epochs": args.num_train_epochs,
        "per_device_train_batch_size": args.per_device_train_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "learning_rate": args.learning_rate,
        "lr_scheduler_type": args.lr_scheduler_type,
        "save_steps": args.save_steps,
        "logging_steps": args.logging_steps,
        "bf16": args.bf16,
        "deepspeed": args.deepspeed,
        "do_train": True,
        "save_language_projection": args.save_language_projection,
        "finetune_part": args.finetune_part,
        "report_to": args.report_to,
    })})

config = AutoConfig.from_pretrained(model_args.model_name_or_path, trust_remote_code={args.trust_remote_code})
config = update_custom_config(config, model_args)
model = CustomAutoVision2SeqModel(
    config,
    image_encoder_name_or_path=model_args.image_encoder_name_or_path,
    qformer_name_or_path=model_args.qformer_name_or_path,
    language_model_name_or_path=model_args.llm_model_name_or_path,
    low_resource=model_args.low_resource,
)
model.tokenizer = AutoTokenizer.from_pretrained(
    model_args.llm_model_name_or_path or model_args.model_name_or_path,
    trust_remote_code={args.trust_remote_code},
)
if model_args.llava_loading and model_args.llava_pretrain_model_path:
    load_llava_pretrain_model(model, model_args.llava_pretrain_model_path)

dataset = Dataset(data_args, backend="custom_multi_modal")
data_collator = DataCollatorForSupervisedDataset(tokenizer=model.tokenizer)
finetuner = AutoPipeline.get_pipeline(
    pipeline_name=pipeline_name,
    model_args=model_args,
    data_args=data_args,
    pipeline_args=pipeline_args,
)
finetuner.tune(model=model, dataset=dataset, data_collator=data_collator)'''
    return "python - <<'PY'\n" + indent(body, "") + "\nPY"


def chat_recipe(args: argparse.Namespace) -> str:
    body = f'''from pathlib import Path

import torch
from PIL import Image
from transformers import AutoConfig, AutoTokenizer

from lmflow.args import VisModelArguments
from lmflow.datasets.multi_modal_dataset import tokenizer_image_token
from lmflow.models.vision2seq_model import CustomAutoVision2SeqModel
from lmflow.utils.multimodal import update_custom_config, load_llava_pretrain_model

model_args = VisModelArguments({render_kwargs({
        "model_name_or_path": args.model_name_or_path,
        "custom_model": args.custom_model,
        "custom_vision_model": args.custom_vision_model,
        "image_encoder_name_or_path": args.image_encoder_name_or_path,
        "qformer_name_or_path": args.qformer_name_or_path,
        "llm_model_name_or_path": args.llm_model_name_or_path,
        "low_resource": args.low_resource,
        "use_prompt_cache": args.use_prompt_cache,
        "prompt_cache_path": args.prompt_cache_path,
        "llava_loading": args.llava_loading,
        "with_qformer": args.with_qformer,
        "vision_select_layer": args.vision_select_layer,
        "llava_pretrain_model_path": args.llava_pretrain_model_path,
        "save_pretrain_model_path": args.save_pretrain_model_path,
        "pretrained_language_projection_path": args.pretrained_language_projection_path,
    })})

config = AutoConfig.from_pretrained(model_args.model_name_or_path, trust_remote_code={args.trust_remote_code})
config = update_custom_config(config, model_args)
model = CustomAutoVision2SeqModel(
    config,
    image_encoder_name_or_path=model_args.image_encoder_name_or_path,
    qformer_name_or_path=model_args.qformer_name_or_path,
    language_model_name_or_path=model_args.llm_model_name_or_path,
    low_resource=model_args.low_resource,
)
model.tokenizer = AutoTokenizer.from_pretrained(
    model_args.llm_model_name_or_path or model_args.model_name_or_path,
    trust_remote_code={args.trust_remote_code},
)
if model_args.llava_loading and model_args.llava_pretrain_model_path:
    load_llava_pretrain_model(model, model_args.llava_pretrain_model_path)

image = Image.open(Path({args.image_path!r})).convert("RGB")
pixel_values = model.image_processor.preprocess(image, return_tensors="pt")["pixel_values"]
prompt_template = {args.prompt!r}
input_text = {args.input_text!r}
prompt = prompt_template.format(input_text=input_text) if "{input_text}" in prompt_template else f"{prompt_template} {input_text}".strip()
input_ids = tokenizer_image_token(prompt, model.tokenizer, return_tensors="pt").unsqueeze(0)
attention_mask = torch.ones_like(input_ids)
outputs = model.generate(
    pixel_values=pixel_values,
    input_ids=input_ids,
    attention_mask=attention_mask,
    max_new_tokens={args.max_new_tokens},
    temperature={args.temperature},
)
prompt_text = model.tokenizer.decode(input_ids[0], skip_special_tokens=True)
text = model.tokenizer.decode(outputs[0], skip_special_tokens=True)
print(text[len(prompt_text):].strip() if text.startswith(prompt_text) else text)'''
    return "python - <<'PY'\n" + indent(body, "") + "\nPY"


def gradio_recipe(args: argparse.Namespace) -> str:
    body = f'''import torch
from PIL import Image
import gradio as gr
from transformers import AutoConfig, AutoTokenizer

from lmflow.args import VisModelArguments
from lmflow.datasets.multi_modal_dataset import tokenizer_image_token
from lmflow.models.vision2seq_model import CustomAutoVision2SeqModel
from lmflow.utils.multimodal import update_custom_config, load_llava_pretrain_model

model_args = VisModelArguments({render_kwargs({
        "model_name_or_path": args.model_name_or_path,
        "custom_model": args.custom_model,
        "custom_vision_model": args.custom_vision_model,
        "image_encoder_name_or_path": args.image_encoder_name_or_path,
        "qformer_name_or_path": args.qformer_name_or_path,
        "llm_model_name_or_path": args.llm_model_name_or_path,
        "low_resource": args.low_resource,
        "use_prompt_cache": args.use_prompt_cache,
        "prompt_cache_path": args.prompt_cache_path,
        "llava_loading": args.llava_loading,
        "with_qformer": args.with_qformer,
        "vision_select_layer": args.vision_select_layer,
        "llava_pretrain_model_path": args.llava_pretrain_model_path,
        "save_pretrain_model_path": args.save_pretrain_model_path,
        "pretrained_language_projection_path": args.pretrained_language_projection_path,
    })})

config = AutoConfig.from_pretrained(model_args.model_name_or_path, trust_remote_code={args.trust_remote_code})
config = update_custom_config(config, model_args)
model = CustomAutoVision2SeqModel(
    config,
    image_encoder_name_or_path=model_args.image_encoder_name_or_path,
    qformer_name_or_path=model_args.qformer_name_or_path,
    language_model_name_or_path=model_args.llm_model_name_or_path,
    low_resource=model_args.low_resource,
)
model.tokenizer = AutoTokenizer.from_pretrained(
    model_args.llm_model_name_or_path or model_args.model_name_or_path,
    trust_remote_code={args.trust_remote_code},
)
if model_args.llava_loading and model_args.llava_pretrain_model_path:
    load_llava_pretrain_model(model, model_args.llava_pretrain_model_path)

prompt_template = {args.prompt!r}

def answer(image: Image.Image, text: str) -> str:
    prompt = prompt_template.format(input_text=text) if "{input_text}" in prompt_template else f"{prompt_template} {text}".strip()
    pixel_values = model.image_processor.preprocess(image.convert("RGB"), return_tensors="pt")["pixel_values"]
    input_ids = tokenizer_image_token(prompt, model.tokenizer, return_tensors="pt").unsqueeze(0)
    attention_mask = torch.ones_like(input_ids)
    outputs = model.generate(
        pixel_values=pixel_values,
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens={args.max_new_tokens},
        temperature={args.temperature},
    )
    prompt_text = model.tokenizer.decode(input_ids[0], skip_special_tokens=True)
    text = model.tokenizer.decode(outputs[0], skip_special_tokens=True)
    return text[len(prompt_text):].strip() if text.startswith(prompt_text) else text

iface = gr.Interface(
    fn=answer,
    inputs=[gr.Image(type="pil"), gr.Textbox(label="Prompt")],
    outputs=gr.Textbox(label="Answer"),
    title="LMFlow multimodal recipe",
)
iface.launch()'''
    return "python - <<'PY'\n" + indent(body, "") + "\nPY"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a self-contained LMFlow multimodal recipe.")
    parser.add_argument("--mode", choices=["train", "chat", "gradio"], default="train")
    parser.add_argument("--model-name-or-path", required=True)
    parser.add_argument("--image-encoder-name-or-path", default="openai/clip-vit-large-patch14")
    parser.add_argument("--qformer-name-or-path", default=None)
    parser.add_argument("--llm-model-name-or-path", default=None)
    parser.add_argument("--dataset-path", default=None)
    parser.add_argument("--image-folder", default=None)
    parser.add_argument("--output-dir", default="./output_models/multimodal")
    parser.add_argument("--image-aspect-ratio", default="pad")
    parser.add_argument("--sep-style", choices=["plain", "v1"], default="v1")
    parser.add_argument("--prompt", default="<image>\n{input_text}", help="Prompt template; use {input_text} for substitution.")
    parser.add_argument("--input-text", default="Describe the image.")
    parser.add_argument("--image-path", default=None)
    parser.add_argument("--custom-model", action="store_true")
    parser.add_argument("--custom-vision-model", action="store_true", default=True)
    parser.add_argument("--llava-loading", action="store_true")
    parser.add_argument("--llava-pretrain-model-path", default=None)
    parser.add_argument("--pretrained-language-projection-path", default=None)
    parser.add_argument("--save-pretrain-model-path", default=None)
    parser.add_argument("--use-prompt-cache", action="store_true")
    parser.add_argument("--prompt-cache-path", default=None)
    parser.add_argument("--with-qformer", action="store_true", default=False)
    parser.add_argument("--vision-select-layer", type=int, default=-2)
    parser.add_argument("--low-resource", action="store_true")
    parser.add_argument("--use-image-start-end", action="store_true", default=True)
    parser.add_argument("--overwrite-output-dir", action="store_true", default=True)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--lr-scheduler-type", default="cosine")
    parser.add_argument("--save-steps", type=int, default=5000)
    parser.add_argument("--logging-steps", type=int, default=20)
    parser.add_argument("--bf16", action="store_true", default=True)
    parser.add_argument("--deepspeed", default=None)
    parser.add_argument("--save-language-projection", action="store_true", default=True)
    parser.add_argument("--finetune-part", default="language_projection")
    parser.add_argument("--report-to", default="none")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()

    if args.mode == "train":
        print(train_recipe(args))
    elif args.mode == "chat":
        if not args.image_path:
            raise SystemExit("--image-path is required for chat mode")
        print(chat_recipe(args))
    else:
        print(gradio_recipe(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
