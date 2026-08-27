# Inference troubleshooting

## Install and import

**`ModuleNotFoundError` before `--help`** — all four native launchers import
PointLLM and their optional dependencies before constructing argparse. Install
the package's declared inference dependencies in the Python 3.10 environment,
including `easydict`, `timm==0.4.12`, `tokenizers==0.12.1`, the pinned
Transformers revision, and (for Gradio PLY uploads) `open3d==0.16.0`. Check
without loading a model:

```bash
python - <<'PY'
mods = ['torch', 'transformers', 'tokenizers', 'easydict', 'timm', 'numpy']
for name in mods:
    try:
        m = __import__(name)
        print(name, 'OK', getattr(m, '__version__', ''))
    except Exception as exc:
        print(name, 'FAIL', repr(exc))
PY
python -c "import pointllm; print('pointllm import OK')"
```

The inspected shell did not reproduce the declared inspection environment: its
Python was 3.13 and `easydict`/Open3D were missing, so native `--help` stopped
at import. Do not interpret that as a model or CLI defect. `scripts/inspect_cli.py`
is the no-import alternative.

**Transformers/tokenizer mismatch** — checkpoint loading can fail if the
Transformers commit or `tokenizers==0.12.1` differs materially from the tested
stack. Check versions before changing model code. Do not replace the pinned
Transformers revision casually; PointLLM relies on the old Llama registration
surface.

**`pointllm` import finds a different package** — run from the project root
with `PYTHONPATH=$PWD`, and print `pointllm.__file__`. Avoid silently mixing a
managed install and a different checkout.

## Dependencies and backends

**`open3d` import fails** — the core NPY chat and batch scripts do not parse
PLY, but `chat_gradio.py` imports Open3D at startup, so even Gradio `--help`
needs it. Install a version compatible with the target Python and the declared
`open3d==0.16.0`, or use NPY/interactive chat if PLY is not needed. Do not
claim Gradio PLY support until Open3D imports.

**CUDA unavailable / `.cuda()` error** — this source calls `.cuda()` for the
model, token IDs, and point tensors. Use a CUDA-enabled torch build and a
visible compatible GPU. There is no CPU inference branch. Check:

```bash
python - <<'PY'
import torch
assert torch.cuda.is_available(), 'PointLLM inference requires CUDA'
print(torch.__version__, torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
PY
```

**Out of memory** — choose a smaller model or lower-memory dtype first. README
figures are approximately 14/28 GB for 7B float16/float32 and 26/52 GB for
13B float16/float32; they are not a reservation or an upper bound. Batch size,
context length, CUDA allocator state, and point encoder allocations add to
those numbers. For Objaverse lower `--batch_size`; for ModelNet lower
`--batch_size`; for chat choose `--torch_dtype float16` where appropriate.
The batch scripts are hard-coded to bfloat16, so changing their dtype requires
code adaptation and verification, not an undocumented flag.

**dtype mismatch in a custom caller** — keep the model, point tensor, and
projector-compatible dtype coherent. The interactive CLI casts the point tensor
to `args.torch_dtype`; batch launchers cast batches to `model.dtype`. Do not
feed a CPU point tensor to a CUDA model.

## Data and point shape

**NPY has the wrong shape** — model input is XYZ plus RGB, conventionally
`(N, 6)`. A three-column cloud is accepted by Gradio and gets black RGB, but
colored checkpoints are intended for six channels. Fewer than 3 columns,
empty arrays, NaN/Inf, or a zero-radius cloud should be rejected before model
loading. Run:

```bash
python scripts/check_pointcloud.py input.npy --strict
```

**Colors are wrong** — the README expects RGB in `[0, 1]`. Gradio converts
values whose maximum is in `(1, 255]` from 0-255, and uses black when colors
are absent. For deterministic model inputs, convert RGB to float32 `[0, 1]`
before saving an NPY with columns `[xyz, rgb]`. A filename containing
`no_color` forces black in the demo.

**Cloud is not normalized** — both the Objaverse helper and Gradio handler
center XYZ and divide by the max Euclidean radius. Preserve RGB while applying
this transform. A constant XYZ cloud has radius zero and produces invalid
values; reject it rather than allowing NaNs into PointBERT.

**Too many or too few points** — Gradio uses farthest-point sampling only for
`N > 8192`; the README recommends 8192 because the model was trained there.
The source does not pad fewer-than-8192 uploads, and its `--pointnum` flag does
not control the hard-coded FPS count in the handler. Objaverse chat resolves
only `_8192.npy`. Use the checker to see the actual shape and make sampling an
explicit preprocessing step when a fixed size is required.

**Objaverse ID cannot be loaded** — confirm that
`<data_path>/<object_id>_8192.npy` exists and that the ID is valid for the
local Objaverse files. Gradio Object ID mode additionally invokes Objaverse
object loading for a 3D preview and may need network access. It is not an
offline smoke test. This route does not cover downloading or arranging data;
hand off to data preparation.

## Model, tokenizer, and point-token failures

**Unknown model/config or missing custom keys** — use a PointLLM checkpoint,
not an arbitrary Llama checkpoint. Verify its config identifies the PointLLM
model and contains the PointBERT-related fields expected by
`PointLLMConfig`/`PointLLMLlamaModel`, such as `point_backbone` and
`mm_use_point_start_end`. v1.1/v1.2 PointBERT configuration and checkpoint
names differ.

**`point_patch_token` count mismatch** — never hard-code 513 for every
checkpoint. Read `model.get_model().point_backbone_config['point_token_len']`
and insert exactly that many configured patch tokens. With start/end enabled,
use the configured start and end tokens around the sequence; the end must be
immediately after it. With start/end disabled, all patch IDs must be
consecutive. Mismatch causes model forward validation errors.

**Tokenizer has no point tokens** — call
`initialize_tokenizer_point_backbone_config_wo_embedding(tokenizer)` after
loading the model and before tokenizing the prompt. If adapting training code,
use the separate embedding-initializing method only when its training contract
is intended; do not casually call it for inference.

**Generation repeats or produces a malformed first answer** — inspect the
first prompt and ensure the point-token block is present exactly once before
the first question. Reuse the same copied `vicuna_v1_1` conversation object
within a dialogue, but call `reset()` for a new object or after `Clear`.

## Context and generation

**Context length error** — PointLLM uses a 2048-token context in this path and
`max_length=2048` is total sequence length. Point tokens, system prompt,
question, separator, previous turns, and answer all count. Gradio rejects
`input_ids.shape[1] >= 2047`; the interactive CLI does not pre-check, so keep
prompts short. Start a new conversation with `exit`/new object or `Clear` in
Gradio.

**Stop text appears in output** — this is expected to be `</s>` from
`vicuna_v1_1`. The scripts use `KeywordsStoppingCriteria` and strip a trailing
stop string after decoding. If a custom conversation template changes the
separator, update both the stop keywords and decoding logic.

**Nondeterministic output** — all native launchers use sampling with
`temperature=1.0`, `top_k=50`, and `top_p=0.95`. This is expected. A custom
reproducible run must set seeds and generation options deliberately, then
record those changes.

## CLI and Gradio workflow failures

**Native `--help` fails** — distinguish import failure from parser failure. Run
`scripts/inspect_cli.py --all` to verify the documented flags without imports;
then repair the environment and retry each native command with `--help`.
Never pass a model name to a help-only smoke.

**`eval_objaverse.py` regenerates nothing** — it intentionally loads an
existing JSON if `<model_name>/evaluation/<expected filename>` exists. Confirm
`--task_type`, `--prompt_index`, and annotation basename, then archive/remove
the old artifact only when a fresh generation is intended.

**Wrong classification prompt** — Objaverse classification accepts prompt 0 or
1; captioning requires 2. ModelNet accepts 0 or 1. The Objaverse script warns
for an invalid pairing but can still fail when indexing its prompt list.

**Unexpected batching or order** — keep `--shuffle` omitted/false. The parser
uses `type=bool`, so `--shuffle False` may evaluate as true. ModelNet asserts
that shuffle is false because indices become output `object_id` values.

**Gradio cannot upload or display** — check Open3D for PLY, NumPy for NPY,
Plotly/Gradio versions, file permissions, and the chosen temp directory. Use a
local NPY with finite `(N, 6)` data first. Wait for the UI's
`[System] New Point Cloud` message before asking a question. Do not use an
Objaverse ID as a no-network smoke.

**Gradio is exposed unsafely** — the source binds to `0.0.0.0` but sets
`share=False`; the research preview is not a hardened public service. Keep it
behind appropriate access controls, use an isolated launch directory/temp
area, and review Gradio file-access guidance before any exposure.

## Output and external evaluation

**JSON is missing fields** — batch generation writes `prompt` and `results`.
Each Objaverse result has `object_id`, `ground_truth`, and `model_output`; each
ModelNet result also has `label_name`. Validate JSON syntax and result count
before scoring. The interactive and Gradio paths stream text and do not write
this JSON envelope.

**`--start_eval` fails or costs money** — it invokes external GPT evaluation
and needs a valid OpenAI key/network. Treat it as a separate opt-in workflow;
first run generation without `--start_eval`, inspect the JSON, then hand off
scoring details to the evaluation route.
