# CLI reference

This reference captures the inference CLI surfaces and the bundled dry-run builder. The builder is the preferred way to construct commands because it does not import model libraries, load checkpoints, download weights, or start a server.

## Bundled dry-run builder

Show help:

```bash
python sub-skills/inference/scripts/build_inference_command.py --help
```

Medical QA JSONL command plan:

```bash
python sub-skills/inference/scripts/build_inference_command.py \
  --workflow medical-qa \
  --base-model "$BASE_MODEL" \
  --lora-weights "$LORA_DIR_OR_ID" \
  --instruct-dir "$INFER_JSONL"
```

Literature single-turn command plan:

```bash
python sub-skills/inference/scripts/build_inference_command.py \
  --workflow literature-single \
  --base-model "$BASE_MODEL" \
  --lora-weights "$LITERATURE_LORA_DIR_OR_ID"
```

Literature multi-turn command plan:

```bash
python sub-skills/inference/scripts/build_inference_command.py \
  --workflow literature-multi \
  --base-model "$BASE_MODEL" \
  --lora-weights "$LITERATURE_LORA_DIR_OR_ID"
```

Gradio serving command plan with conservative defaults:

```bash
python sub-skills/inference/scripts/build_inference_command.py \
  --workflow gradio \
  --base-model "$BASE_MODEL" \
  --lora-weights "$LORA_DIR_OR_ID"
```

Override the template when the model family or adapter training data requires it:

```bash
python sub-skills/inference/scripts/build_inference_command.py \
  --workflow medical-qa \
  --base-model "$BASE_MODEL" \
  --lora-weights "$LORA_DIR_OR_ID" \
  --instruct-dir "$INFER_JSONL" \
  --model-family bloom-huozi \
  --prompt-template bloom_deploy
```

## Builder arguments

| Builder argument | Required? | Meaning |
| --- | --- | --- |
| `--workflow {medical-qa,literature-single,literature-multi,gradio}` | yes | Selects the distilled workflow. |
| `--base-model TEXT` | yes | Base model path or Hugging Face id. It must match the adapter family. |
| `--lora-weights TEXT` | yes | LoRA adapter path or id. For local adapters, expect `adapter_config.json` and `adapter_model.bin`. |
| `--instruct-dir TEXT` | yes for `medical-qa` | JSON Lines file for medical QA batch inference. Ignored by literature and Gradio workflows. |
| `--prompt-template TEXT` | no | Overrides workflow/model-family default template. Use names such as `med_template`, `literature_template`, or `bloom_deploy`. |
| `--model-family {llama-alpaca,bloom-huozi,custom}` | no | Helps select a default template and warnings. Default is `llama-alpaca`. |
| `--python TEXT` | no | Python executable to place in the printed command. Default is `python`. |
| `--workdir TEXT` | no | Optional working directory prefix for the printed command. Useful because the prompt helper expects a `templates/` directory relative to the command's current directory. |
| `--load-8bit` | no | Adds `--load_8bit True` to the printed command. Requires a compatible bitsandbytes/CUDA stack during real execution. |
| `--no-lora` | no | Prints `--use_lora False` for medical QA or literature baseline comparisons. Not valid for Gradio because the serving workflow always composes a LoRA adapter. |
| `--server-name TEXT` | Gradio only | Server interface for Gradio. Builder default is `127.0.0.1` for safety. |
| `--share-gradio` | Gradio only | Prints `--share_gradio True`. Use only when an external share link is explicitly authorized. |
| `--check-local-paths` | no | Performs lightweight filesystem checks for local-looking paths only; still does not import or download models. |

## Distilled workflow CLI surfaces

### Medical QA batch inference

```bash
python infer.py \
  --base_model "$BASE_MODEL" \
  --lora_weights "$LORA_DIR_OR_ID" \
  --use_lora True \
  --instruct_dir "$INFER_JSONL" \
  --prompt_template med_template
```

Relevant arguments:

| Argument | Meaning | Default from source workflow |
| --- | --- | --- |
| `--load_8bit` | Load base model in int8 where supported. | `False` |
| `--base_model` | Base model path/id. | empty string; real run needs explicit value |
| `--instruct_dir` | JSONL inference file. | empty string; then built-in questions are used |
| `--use_lora` | Compose PEFT LoRA adapter. | `True` |
| `--lora_weights` | Adapter path/id. | `tloen/alpaca-lora-7b` placeholder |
| `--prompt_template` | Template name loaded from `templates/<name>.json`. | `med_template` |

Generation defaults: `temperature=0.1`, `top_p=0.75`, `top_k=40`, `num_beams=4`, `max_new_tokens=256`.

### Literature inference

```bash
python infer_literature.py \
  --base_model "$BASE_MODEL" \
  --lora_weights "$LITERATURE_LORA_DIR_OR_ID" \
  --single_or_multi single \
  --use_lora True \
  --prompt_template literature_template
```

For multi-turn, change `--single_or_multi multi`.

Relevant arguments:

| Argument | Meaning | Default from source workflow |
| --- | --- | --- |
| `--load_8bit` | Load base model in int8 where supported. | `False` |
| `--base_model` | Base model path/id. | empty string; real run needs explicit value |
| `--single_or_multi` | `single` for fixed prompts, `multi` for stdin conversation. | empty string |
| `--use_lora` | Compose PEFT LoRA adapter. | `True` |
| `--lora_weights` | Adapter path/id. | `tloen/alpaca-lora-7b` placeholder |
| `--prompt_template` | Template name loaded from `templates/<name>.json`. | `med_template`, but literature workflows should override to `literature_template` |

Generation defaults: `temperature=0.1`, `top_p=0.75`, `top_k=40`, `num_beams=4`, `max_new_tokens=256`.

### Gradio serving

```bash
python generate.py \
  --base_model "$BASE_MODEL" \
  --lora_weights "$LORA_DIR_OR_ID" \
  --prompt_template med_template \
  --server_name 127.0.0.1 \
  --share_gradio False
```

Relevant arguments:

| Argument | Meaning | Default from source workflow |
| --- | --- | --- |
| `--load_8bit` | Load base model in int8 where supported. | `False` |
| `--base_model` | Base model path/id; asserted non-empty. | empty string |
| `--lora_weights` | Adapter path/id. | `tloen/alpaca-lora-7b` placeholder |
| `--prompt_template` | Template name loaded from `templates/<name>.json`. | `med_template` |
| `--server_name` | Interface to bind. | `0.0.0.0` in source; safer builder default is `127.0.0.1` |
| `--share_gradio` | Whether to create a Gradio share link. | `True` in source; safer builder default is `False` |

Generation defaults: `temperature=0.1`, `top_p=0.75`, `top_k=40`, `num_beams=4`, `max_new_tokens=128` by default with UI slider up to 2000.

## Fire boolean syntax

The workflow scripts use Python Fire. The repository's shell examples pass booleans as strings such as `--use_lora True`, `--use_lora False`, and `--share_gradio False`. Keep this style in generated commands unless the runtime project has replaced Fire with another parser.
