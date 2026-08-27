# CLI reference

Run commands in an environment where the installed `pointllm` package is
importable. The bundled `scripts/run_installed_cli.py` wrapper locates each
launcher inside that installed package and handles its legacy sibling imports.
The README has one stale chat example using `--data_name`; the actual parser
uses `--data_path`.

## `PointLLM_chat.py`

```text
--model_name STRING       default: RunsenXu/PointLLM_7B_v1.2
--data_path STRING        default: data/objaverse_data
--torch_dtype STRING      default: float32; choices: float32, float16, bfloat16
```

Example:

```bash
python ../../scripts/run_installed_cli.py PointLLM_chat.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 \
  --data_path data/objaverse_data --torch_dtype float16
```

The model and tokenizer load before the interactive prompt. The program then
asks for an Objaverse object ID; `q` quits the program and `exit` ends the
current object's conversation. This CLI only resolves the object-ID naming
pattern `<id>_8192.npy`; it does not upload PLY/NPY files.

## `chat_gradio.py`

```text
--model_name STRING       default: RunsenXu/PointLLM_7B_v1.2
--data_path STRING        default: data/objaverse_data
--pointnum INT            default: 8192
--log_file STRING         default: serving_workdirs/serving_log.txt
--tmp_dir STRING          default: serving_workdirs/tmp
--port INT                default: 7810
```

Example with explicit serving directories:

```bash
python ../../scripts/run_installed_cli.py chat_gradio.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 \
  --data_path data/objaverse_data --port 7810 \
  --log_file serving_workdirs/serving_log.txt \
  --tmp_dir serving_workdirs/tmp
```

The script binds `0.0.0.0`, launches with `share=False`, and sets
`GRADIO_TEMP_DIR`. It creates the log and temporary directory before model
loading. `--pointnum` is exposed but the file handler's FPS branch is coded
against 8192; treat the flag as documentation/configuration only unless the
implementation is changed. Object ID selection can call Objaverse and fetch
external objects; use File mode for an offline-oriented demo test.

## `eval_objaverse.py`

```text
--model_name STRING       default: RunsenXu/PointLLM_7B_v1.2
--data_path STRING        default: data/objaverse_data
--anno_path STRING        default: data/anno_data/PointLLM_brief_description_val_200_GT.json
--pointnum INT            default: 8192
--use_color               store_true; default: True
--batch_size INT          default: 6
--shuffle BOOL            default: False
--num_workers INT         default: 10
--prompt_index INT        default: 0
--start_eval              store_true; default: False
--gpt_type STRING         default: gpt-4-0613
--task_type STRING        default: captioning; choices: captioning, classification
```

Accepted `--gpt_type` values are `gpt-3.5-turbo-0613`,
`gpt-3.5-turbo-1106`, `gpt-4-0613`, and `gpt-4-1106-preview`. The generation
prompt table is fixed in the script:

| `--task_type` | valid prompt index | prompt |
|---|---:|---|
| classification | 0 | `What is this?` |
| classification | 1 | `This is an object of ` |
| captioning | 2 | `Caption this 3D model in detail.` |

The script prints a warning for an inappropriate index but does not reject it
before indexing the list. Use the valid pair. The output is written to
`<model_name>/evaluation/<annotation-basename>_Objaverse_<task_type>_prompt<index>.json`.
`<model_name>` is used literally as the output directory; a Hub identifier
therefore creates a relative directory named like the identifier unless a
local path is supplied.

Examples:

```bash
# Open-vocabulary classification, prompt 0
python ../../scripts/run_installed_cli.py eval_objaverse.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 \
  --task_type classification --prompt_index 0

# Captioning, prompt 2
python ../../scripts/run_installed_cli.py eval_objaverse.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 \
  --task_type captioning --prompt_index 2 \
  --batch_size 2 --num_workers 2
```

Although `--use_color` is declared with `store_true`, its source default is
already `True`; there is no `--no_color` switch. The source model dtype is
always `torch.bfloat16`, regardless of a CLI dtype flag (there is none).
`--start_eval` adds an external evaluator step and needs the separate
credentials/network contract.

## `eval_modelnet_cls.py`

```text
--model_name STRING       default: RunsenXu/PointLLM_7B_v1.2
--split STRING            default: test; help says train or test
--use_color               store_true; default: True
--batch_size INT          default: 30
--shuffle BOOL            default: False
--num_workers INT         default: 20
--subset_nums INT         default: -1
--prompt_index INT        default: 0
--start_eval              store_true; default: False
--gpt_type STRING         default: gpt-3.5-turbo-0613
```

`--gpt_type` accepts the same four values as Objaverse. Prompt indices are:

| index | prompt |
|---:|---|
| 0 | `What is this?` |
| 1 | `This is an object of ` |

Example bounded generation (the source still needs the configured ModelNet
processed data):

```bash
python ../../scripts/run_installed_cli.py eval_modelnet_cls.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 --split test \
  --prompt_index 0 --subset_nums 10 --batch_size 2 --num_workers 1
```

The output is
`<model_name>/evaluation/ModelNet_classification_prompt<index>.json`.
`--subset_nums` samples a deterministic subset after seeding Python's random
module to 0. Keep `--shuffle` false: the loader asserts no shuffle because the
sample index is emitted as `object_id`. As with Objaverse, the source defaults
`--use_color` to true and always loads bfloat16 before `.cuda()`.

## Boolean and output pitfalls

The two batch parsers declare `type=bool` for `--shuffle`. In argparse,
`bool("False")` is true, so do not pass a textual false value expecting it to
be false. Omit the flag to keep the safe default. Both scripts check the
expected output path first and load existing JSON instead of regenerating it;
remove or rename that artifact intentionally if a fresh run is required.
