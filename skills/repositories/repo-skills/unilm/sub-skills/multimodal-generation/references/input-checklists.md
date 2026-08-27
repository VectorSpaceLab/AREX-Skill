# Multimodal Input Checklists

Use this reference before constructing or running native UniLM multimodal commands. Prefer `scripts/check_multimodal_inputs.py` for quick local validation, then use these checklists to finish manual review.

## Universal Inputs

| Requirement | Check |
|---|---|
| Source checkout | Native commands must be run from a compatible UniLM source checkout for the selected subproject, not from this generated skill directory. |
| Python environment | Confirm an isolated environment with the selected subproject's dependency stack; the lightweight inspected environment only proved unrelated `adalm` import. |
| Hardware | Confirm CPU/GPU expectations, CUDA availability, GPU memory, and whether Ampere/Ada/Hopper, FlashAttention, xformers, Apex, fairseq, or accelerate are required. |
| Network | Ask before downloading checkpoints, datasets, Hugging Face models, fonts, demo assets, or remote evaluation data. |
| Outputs | Choose a user-owned output directory; avoid overwriting non-empty training, FID, or inference outputs. |
| Privacy | Do not embed private local paths in reusable commands or generated notes; use placeholders such as `<CHECKPOINT_PATH>`. |

## Kosmos-2 Grounding

Required planning inputs:

- `--checkpoint`: local Kosmos-2 `.pt` checkpoint or an approved Hugging Face model path if using a Transformers implementation.
- `--image` or task dataset: a readable local image for demos, or a prepared evaluation/training data root for fairseq generation.
- `--prompt` or task-specific prompt data: grounding/caption/VQA prompt shape chosen for the task.
- `--output-dir`: destination for generated text, decoded boxes, or evaluation outputs.
- Fairseq/user-dir details: task name, user-dir, dictionary/tokenizer/config paths, and generation split when using native fairseq.

Data assumptions:

- GRIT-style data contains image IDs/URLs, captions, raw width/height, and normalized noun chunk/referring-expression boxes.
- GRIT training config lists TSV source files and is generated from local TSV paths; replace placeholder paths before a real run.
- Native evaluation datasets such as Flickr30k Entities, RefCOCO, VQAv2, and SEED-Bench need their own preprocessing scripts and access rules.

Quick checker:

```bash
python scripts/check_multimodal_inputs.py kosmos2 \
  --checkpoint <KOSMOS2_CHECKPOINT.pt> \
  --image <IMAGE_PATH> \
  --prompt "<PROMPT>" \
  --output-dir <OUTPUT_DIR>
```

## Kosmos-2.5 OCR And Markdown

Required inputs:

- `--task`: `ocr` for spatial text blocks or `markdown` for image-to-markdown.
- `--image`: existing local image readable by PIL; prefer `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, or `.tif/.tiff`.
- `--checkpoint`: existing local `ckpt.pt` or approved downloaded checkpoint.
- `--output-dir`: existing or creatable directory for JSON/markdown output.
- Optional preprocess spans: `--hw_ratio_adj_upper_span` and `--hw_ratio_adj_lower_span` formatted as two-number lists when using aspect-ratio adjustment.

Native invariants:

- Select exactly one native flag: `--do_ocr` or `--do_md`.
- FlashAttention2 means the environment should have a compatible GPU family and matching CUDA/Torch packages.
- OCR output JSON should contain `model`, `task`, `width`, `height`, and `results`; OCR `results` entries include text plus bounding boxes.
- `draw_bbox.py` requires the original image and OCR JSON; it does not create OCR itself.

Quick checker:

```bash
python scripts/check_multimodal_inputs.py kosmos25 \
  --task ocr \
  --image <IMAGE_PATH> \
  --checkpoint <CKPT.pt> \
  --output-dir <OUTPUT_DIR> \
  --use-preprocess
```

## TextDiffuser v1

Required inputs by mode:

| Mode | Required | Optional / common |
|---|---|---|
| `text-to-image` | prompt, diffusion checkpoint, output directory | `--vis_num`, `--sample_steps`, `--font_path`, xformers flag |
| `text-to-image-with-template` | prompt, template image, diffusion checkpoint, output directory | binarization and segmentation mask options |
| `text-inpainting` | prompt, original image, text mask image, diffusion checkpoint, output directory | segmentation mask options and image merge inspection |
| evaluation sampling | prompt list text file, mode, checkpoint, output directory | MARIO-Eval subset selection and OCR metric dependencies |

Prompt assumptions:

- Text intended to appear in the image should be enclosed in single quotes for v1 prompt-only generation.
- `--resume_from_checkpoint` points to the diffusion backbone directory from the TextDiffuser checkpoint archive.
- `--font_path` should exist if layout visualization or caption rendering is used.

Quick checker:

```bash
python scripts/check_multimodal_inputs.py textdiffuser1 \
  --mode text-inpainting \
  --prompt "a boy draws good morning on a board" \
  --checkpoint <TEXTDIFFUSER_CKPT>/diffusion_backbone \
  --original-image <IMAGE_PATH> \
  --text-mask <MASK_PATH> \
  --output-dir <OUTPUT_DIR>
```

## TextDiffuser-2

Required inputs by variant:

| Variant | Native script family | Required |
|---|---|---|
| `full` | `inference_textdiffuser2_t2i_full.py` | prompt/input file, base model path, full checkpoint, layout planner, output directory |
| `lora` | `inference_textdiffuser2_t2i_lora.py` | prompt/input file, base model path, LoRA checkpoint, layout planner, output directory |
| `inpainting` | demo/inpainting full scripts | original image, text mask/layout or interactive coordinates, inpainting checkpoint, output directory, GPU |
| `train-full` | `train_textdiffuser2_t2i_full.py` | dataset root, train index, output directory, base model, GPU/accelerate config |
| `train-lora` | `train_textdiffuser2_t2i_lora.py` | dataset root, train index, output directory, base model, GPU/accelerate config |

Important flags:

- `--granularity` usually `128`; valid coordinate granularity is documented as `1~512`.
- `--coord_mode` is one of `lt`, `center`, or `ltrb`; README inference examples use `ltrb`.
- `--max_length` defaults to `77` in released checkpoints for general objects.
- `--cfg`, `--sample_steps`, and `--seed` control generation behavior.
- `--input_format prompt` pairs with `--input_prompt`; file modes require `--input_file` or `--prompts_txt_file` depending on the script.

Acceleration checks:

- xformers must match the Torch/CUDA stack if `--enable_xformers_memory_efficient_attention` is used.
- FlashAttention is only needed for layout-planner training with FastChat, not ordinary inference.
- Inpainting demo may download `images2.zip` and Hugging Face weights; ask before running it.

Quick checker:

```bash
python scripts/check_multimodal_inputs.py textdiffuser2 \
  --variant full \
  --prompt "a hotdog with mustard and other toppings on it" \
  --checkpoint JingyeChen22/textdiffuser2-full-ft \
  --layout-model JingyeChen22/textdiffuser2_layout_planner \
  --output-dir <OUTPUT_DIR> \
  --coord-mode ltrb \
  --granularity 128
```

## Audio And Speech

### WavLM

- Checkpoint is a `.pt` file with `cfg` and `model` keys.
- Input waveform should be mono 16 kHz and loaded as a float tensor shaped like `[batch, time]`.
- Apply layer norm when `cfg.normalize` is true.
- Use `ret_layer_results=True` and `output_layer=model.cfg.encoder_layers` to collect layer outputs.

### BEATs

- Tokenizer checkpoints and model checkpoints use `cfg` and `model`; fine-tuned classifier checkpoints may include `label_dict`.
- Input waveform should be mono 16 kHz and paired with a boolean padding mask.
- BEATs computes 128-bin Kaldi fbank features internally; sample-rate mismatch corrupts features even when code runs.

### SpeechT5

- Fairseq data root must contain manifests and labels for the selected task.
- `--hubert-label-dir`, `--bpe-tokenizer`, `--user-dir`, and `--path` are required in most ASR/TTS/ST/VC workflows.
- `--sample-rate 16000` is used throughout evidence commands.
- `generate_speech.py` asserts `--path` and writes `.npy` features plus optional demo plots/audio under `--results-path`.
- TTS and VC generation require `--batch-size 1`.

### SpeechLM

- Cleaned feature-extraction checkpoints use `checkpoint['cfg']['model']` and `checkpoint['cfg']['task']['normalize']`.
- ASR data uses wav2vec-style `train.tsv`, `train.ltr`, and matching `dict.ltr.txt`.
- Speech translation data uses CoVoST-style language directories such as `en-de`, with source audio and translation manifests.
- KenLM/fairseq-LM decoding requires additional language-model and lexicon files in the data directory.

### VALL-E

- The inspected UniLM VALL-E directory contains only release/demo notes, not runnable local inference scripts.
- Treat requests as planning/research unless the user supplies an external implementation, checkpoint, codec/tokenizer, and generation script.

Quick checker:

```bash
python scripts/check_multimodal_inputs.py audio \
  --family beats \
  --checkpoint <BEATS_CHECKPOINT.pt> \
  --audio <AUDIO.wav> \
  --sample-rate 16000
```

## LatentLM

Required inputs by operation:

| Operation | Required | Optional / mutation risk |
|---|---|---|
| `sample` | checkpoint directory, VAE name/path, image name, output directory or default `visuals/` | reads `other_state.pth`, model safetensors, or DeepSpeed state |
| `sample-many` | checkpoint directory, VAE, batch size | writes many images under native default `demo/` unless adapted |
| `train` | output directory, VAE, either `--dataset_name` or `--train_data_dir` | may download datasets/models and writes checkpoints/logs |
| `fid` | checkpoint directory, VAE, reference-stat `.npz`, class count, batch size | writes cached latents, result JSON, and image `.npz` into checkpoint directory |

Checkpoint layout checks:

- Checkpoint directory should contain at least one model source: `model.safetensors` or `pytorch_model/mp_rank_00_model_states.pt`.
- `other_state.pth` is expected by sampling/evaluation paths, especially when using EMA or VAE scaling/bias metadata.
- `--use_ema` requires `other_state.pth` with EMA shadow parameters.

Dataset checks:

- Local `--train_data_dir` follows torchvision `ImageFolder`: one class subdirectory per class, with readable images below each class.
- Hugging Face `--dataset_name` requires network/cache approval unless already cached.
- `--num_classes`/`--num-classes` must match the dataset label space and model head.
- FID `--ref_stat_path` must be a local `.npz` file matching the target image distribution/resolution.

Quick checker:

```bash
python scripts/check_multimodal_inputs.py latentlm \
  --operation sample \
  --checkpoint <CHECKPOINT_DIR> \
  --vae <VAE_NAME_OR_PATH> \
  --image-name sample.png \
  --output-dir <OUTPUT_DIR>
```
