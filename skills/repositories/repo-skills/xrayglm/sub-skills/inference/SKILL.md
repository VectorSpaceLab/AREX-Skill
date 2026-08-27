---
name: inference
description: "Operate checkpoint-backed XrayGLM inference from the CLI or Gradio
  WebUI, including image inputs, multi-turn conversations, sampling,
  quantization, and runtime diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# XrayGLM inference

Use this route when a Researcher needs to run the released XrayGLM/VisualGLM
model locally, inspect an image, or troubleshoot an inference launch. This is
an operating route, not a training or data-preparation route. Follow the
repository's license and checkpoint terms.

**Medical safety:** XrayGLM outputs are research assistance only, not a
medical diagnosis. They can be wrong, incomplete, unsafe, or sensitive to
prompt wording, image quality, sampling, and quantization. Never use an output
to diagnose, triage, or choose treatment. A qualified clinician must review the
original study and clinical context; protect patient-identifying data.

## Readiness gate

1. Work from the repository root and confirm that `cli_demo.py`, `web_demo.py`,
   `model/`, `requirements.txt`, and `checkpoints/` are present.
2. Use Python 3.10 or a compatible isolated environment. The verified setup
   imported the model modules and demos with torch 2.1.2+cu121,
   torchvision 0.16.2+cu121, transformers 4.27.4, SwissArmyTransformer 0.3.7,
   gradio 3.50.2, cpm_kernels 1.0.11, bitsandbytes 0.39.0, and deepspeed
   0.10.3. Treat these as a known-good reference, not a requirement to expose
   private machine details.
3. Install dependencies using `pip install -r requirements.txt`. If
   deepspeed is not needed, use `requirements_wo_ds.txt` and install
   `SwissArmyTransformer>=0.3.6 --no-deps` as documented in the CLI reference.
   Pin compatible versions rather than blindly upgrading old dependencies.
4. A checkpoint directory is required for model inference. Pass its local path
   with `--from_pretrained`; an existing local checkpoint is not the same as a
   parser-only smoke test. The default base model name may trigger model
   resolution/download and is not a no-download guarantee.
5. The tokenizer is separately loaded as `THUDM/chatglm-6b` with
   `trust_remote_code=True`. Ensure its files are already available locally or
   that approved network access and cache policy permit resolution. A model
   checkpoint without tokenizer assets is not ready.
6. Check `torch.cuda.is_available()` and free GPU memory before loading. The
   demos are designed around GPU inference; a local image and checkpoint do
   not make CPU inference feasible or supported. Do not promise CPU inference
   when no GPU or tokenizer cache exists.

Run the deterministic, weight-free checks before a costly load:

```bash
python skills/disco/xrayglm/sub-skills/inference/scripts/check_image_preprocessing.py --repo-root .
python skills/disco/xrayglm/sub-skills/inference/scripts/check_cli_contract.py --repo-root .
python skills/disco/xrayglm/sub-skills/inference/scripts/check_web_contract.py --repo-root .
```

These checks parse source and exercise a tiny PIL image only; they never fetch
weights, import the model, or launch Gradio. See the linked references for
what a successful check means.

## CLI route

Launch from the repository root, for example:

```bash
python cli_demo.py \
  --from_pretrained checkpoints/checkpoints-XrayGLM-3000 \
  --prompt_zh '详细描述这张胸部X光片的诊断结果' \
  --max_length 2048 --top_p 0.4 --top_k 100 --temperature 0.8
```

The first prompt is used after entering an image path or URL. The interactive
loop accepts a local image path, an `http...` URL, or an empty line for text
only. Type `clear` to discard the current conversation/image cache and start
a new round; type `stop` to exit. After the first image round, the code sets
the image path to `None` and passes the processed tensor as `image`, so later
turns reuse the cached image. Do not accidentally carry that cache across
patients or studies.

Use `--english` for English prompts and the English `Q:`/`A:` conversation
format; otherwise use Chinese `问：`/`答：` separators. `--prompt_en` controls
the first English image prompt. `--max_length` is total sequence capacity,
not a promise of response length. `--top_p`, `--top_k`, and `--temperature`
control sampling; lower temperature is generally more reproducible but does
not make medical content reliable. `--quant 8` or `--quant 4` applies
quantization to the transformer after loading. See the CLI and contract
references for exact defaults and caveats.

Responses are decoded text and printed after the `XrayGLM：` label (or the
English separator handling). Capture stdout if a downstream experiment needs
the answer, but retain the prompt, image identifier, checkpoint, language,
and sampling settings alongside it.

## WebUI route

```bash
python web_demo.py \
  --from_pretrained checkpoints/checkpoints-XrayGLM-3000 \
  --quant 8
# open http://127.0.0.1:7860 locally
```

The WebUI accepts a filepath through Gradio's image component, requires
non-empty text and an image, and maintains a displayed multi-round history.
Adjust Temperature and Top P, press Generate or Enter, and use Clear before
switching studies. Uploading or clearing an image resets the displayed
conversation seed. `--share` requests a public Gradio share link: avoid it for
patient images and private prompts, and disable proxy/network exposure unless
explicitly approved. The UI's exception message says timeout even for other
runtime failures; inspect the terminal traceback.

## Recovery order

- If argument help works but loading fails, treat that as parser success only.
  Verify the checkpoint path and files, then verify tokenizer availability and
  CUDA/PyTorch compatibility.
- For missing model/config/weights, stop and obtain the intended checkpoint;
  do not substitute an unrelated language-model directory. For tokenizer
  errors, pre-cache the compatible ChatGLM tokenizer under the approved cache
  policy and retry.
- For CUDA out-of-memory, close other jobs, reduce sequence capacity, use an
  approved quantization mode, or use a smaller/compatible checkpoint. Do not
  infer that 4/8-bit works merely because the flag parses.
- `bitsandbytes==0.39.0` was observed warning that it is CPU-only or missing
  libcudart in the verified environment. Treat 4/8-bit and QLoRA-related
  acceleration as unavailable until a real quantized load is proven; repair
  the CUDA-linked bitsandbytes installation or omit `--quant`.
- For image errors, verify the file is readable, decodable, and non-empty;
  for URLs, verify approved network access, HTTPS, timeout behavior, and that
  the response is actually an image. Avoid untrusted URLs and huge files.
- If a Chinese turn is followed by an English turn, start a fresh `--english`
  session (or `clear`) rather than mixing separator conventions in one history.
  A URL image is fetched by the chat helper and may be cached only as the
  in-memory processed tensor; network retrieval and image retention remain
  security/privacy concerns.

For implementation-level prompt, image, and architecture details read:

- [CLI reference](references/cli-reference.md)
- [Chat and image contract](references/chat-and-image-contract.md)
- [Model architecture](references/model-architecture.md)
- [Troubleshooting](references/troubleshooting.md)
- [Image preprocessing check](scripts/check_image_preprocessing.py)
- [CLI contract check](scripts/check_cli_contract.py)
- [Web contract check](scripts/check_web_contract.py)

Do not add checkpoints, images, model code, or copied source demos to this
skill. Training, dataset preparation, and fine-tuning belong to sibling routes.
