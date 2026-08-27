# Inference workflows

These recipes distill the checked-in inference launchers and README. They are
GPU workflows: the launchers call `.cuda()` and load full model checkpoints.
They do not provide a CPU fallback.

## 1. Prepare a model-backed run

The tested baseline was Python 3.10, torch 2.0.1+cu117, CUDA 11.7, an A100
40 GB, Transformers 4.28.0.dev0 at `cae78c46`, and tokenizers 0.12.1. Install
the package in the environment that will run inference, and confirm CUDA
before loading a checkpoint:

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
PY
python -c "import pointllm; print('pointllm import ok')"
```

The package dependencies include `accelerate`, `einops`, `gradio`, `numpy`,
`sentencepiece`, `tokenizers==0.12.1`, the pinned Transformers commit,
`easydict`, `timm==0.4.12`, `open3d==0.16.0`, `h5py`, `plyfile`, and torch.
The model and tokenizer can be a local checkpoint directory or a Hub model
identifier. A Hub identifier requires network/cache access and may download
large files.

## 2. Inspect the point contract without a model

For an NPY or PLY file that is already available locally:

```bash
python scripts/check_pointcloud.py /path/to/cloud.npy --strict
```

A valid serving input has non-empty finite XYZ, and preferably exactly six
columns: XYZ plus RGB. RGB should be finite and in `[0, 1]`; the Gradio path
also accepts `[0, 255]` and converts it to `[0, 1]`. A 3-column cloud gets
black RGB in the Gradio path, but it is not the README's colored-model input
contract. A PLY without vertex colors likewise receives black RGB.

The model-side normalization is:

```text
centroid = mean(points[:, :3], axis=0)
xyz = points[:, :3] - centroid
radius = max(sqrt(sum(xyz**2, axis=1)))
xyz = xyz / radius
```

The radius must be nonzero. The bundled checker reports centroid and radius;
it does not rewrite the source file. `data.utils.farthest_point_sample` keeps
all columns and samples by XYZ distance. The Gradio path applies FPS only when
there are more than 8192 points, then applies `pc_norm`; it does not pad a
cloud with fewer than 8192 points.

## 3. Load and chat with one Objaverse object

From the PointLLM project root, the README's chat entry point is:

```bash
export PYTHONPATH=$PWD
python ../../scripts/run_installed_cli.py PointLLM_chat.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 \
  --data_path data/objaverse_data \
  --torch_dtype float16
```

The source default is `float32`; the accepted values are `float32`, `float16`,
and `bfloat16`. `float16` is a practical 7B choice when supported. The README
reports approximate model-only GPU requirements of 14 GB for 7B float16, 28 GB
for 7B float32, 26 GB for 13B float16, and 52 GB for 13B float32. It
recommends bfloat16 where supported, but does not provide a memory table for
bfloat16. Keep headroom for CUDA allocations and point processing.

The interactive program asks for an object ID, loads
`<object_id>_8192.npy` from `--data_path`, normalizes it, casts it to the
selected dtype on CUDA, and asks questions until `exit`; `q` quits the program.
It uses `vicuna_v1_1`, resets the conversation for each object, and allows up
to 100 dialogue rounds. The object-ID route is Objaverse-specific; it does not
accept an arbitrary PLY/NPY upload.

## 4. Run the Gradio demo

```bash
export PYTHONPATH=$PWD
python ../../scripts/run_installed_cli.py chat_gradio.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 \
  --data_path data/objaverse_data \
  --port 7810 \
  --tmp_dir serving_workdirs/tmp \
  --log_file serving_workdirs/serving_log.txt
```

The demo loads the model and tokenizer, calls the no-embedding tokenizer
initializer, then launches on `0.0.0.0:<port>` with `share=False`. It creates a
timestamped log beside `--log_file`, creates `--tmp_dir`, and sets
`GRADIO_TEMP_DIR` to that directory. The UI supports `File` and `Object ID`.
File mode accepts PLY and NPY. Object ID mode calls `objaverse.load_objects` for
visualization and can download external objects; it is not a safe offline
smoke test. Do not expose this research preview publicly without reviewing
Gradio file-access and data-handling security.

The declared `--pointnum` flag defaults to 8192 but the demo's file handler
uses the literal 8192 when deciding FPS. Do not assume changing `--pointnum`
changes preprocessing without changing the implementation.

For a local file, confirm the point cloud first, wait for `[System] New Point
Cloud`, then ask a question. The first question receives point tokens; later
questions reuse the conversation. `Clear` resets the conversation state.

## 5. Batch Objaverse generation

Classification prompts are indices 0 or 1; captioning is index 2:

```bash
export PYTHONPATH=$PWD
python ../../scripts/run_installed_cli.py eval_objaverse.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 \
  --data_path data/objaverse_data \
  --anno_path data/anno_data/PointLLM_brief_description_val_200_GT.json \
  --task_type classification --prompt_index 0 \
  --batch_size 6 --num_workers 10

python ../../scripts/run_installed_cli.py eval_objaverse.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 \
  --data_path data/objaverse_data \
  --anno_path data/anno_data/PointLLM_brief_description_val_200_GT.json \
  --task_type captioning --prompt_index 2 \
  --batch_size 6 --num_workers 10
```

The script constructs an `ObjectPointCloudDataset`, uses colored points by its
`--use_color` default, and always loads the model as `torch.bfloat16` before
`.cuda()`; there is no dtype CLI flag. It repeats one tokenized prompt across
each batch, generates with sampling (`temperature=1.0`, `top_k=50`,
`top_p=0.95`, `max_length=2048`), then writes the JSON described in the API
reference. The output directory is `<model_name>/evaluation`; if the expected
file already exists, generation is skipped and that file is loaded.

Keep the default `--shuffle False`. The parser uses `type=bool`, so passing a
string such as `--shuffle False` does not reliably mean false. The default is
the safe value.

## 6. Batch ModelNet40 generation

```bash
export PYTHONPATH=$PWD
python ../../scripts/run_installed_cli.py eval_modelnet_cls.py \
  --model_name RunsenXu/PointLLM_7B_v1.2 \
  --split test --prompt_index 0 \
  --batch_size 30 --num_workers 20 --subset_nums 10
```

`--subset_nums 10` is a bounded generation example; omit it for the full test
split. The ModelNet loader reads its configured processed `.dat` file, emits
normalized point tensors, and the launcher always loads bfloat16 and CUDA.
Prompt index 0 is `What is this?`; index 1 is `This is an object of `. Output
is `ModelNet_classification_prompt<index>.json` under
`<model_name>/evaluation`. Keep `--shuffle` at its default false because the
script asserts that evaluation is not shuffled.

## 7. Optional open-step evaluation hook

Both batch launchers accept `--start_eval --gpt_type <choice>`, and Objaverse
maps `classification`/`captioning` to evaluator modes. This requires an
OpenAI key, network access, and paid external calls. It is not a model-loading
or safe smoke test. Keep scoring workflows in the evaluation sibling.

## 8. No-download CLI inspection

```bash
python scripts/inspect_cli.py --all
```

This prints the distilled flag contracts without importing PointLLM, loading
weights, starting Gradio, or contacting a network. Native `--help` is useful
only after all import dependencies are installed; argparse is reached after
module imports in all four launchers.
