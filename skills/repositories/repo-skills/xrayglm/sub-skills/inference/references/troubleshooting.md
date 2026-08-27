# Inference troubleshooting

Use this decision tree in order. Keep parser, input, dependency, device, and
model readiness failures separate.

## 1. Parser and source checks

Run the three weight-free checks from the skill root:

```bash
python skills/disco/xrayglm/sub-skills/inference/scripts/check_image_preprocessing.py --repo-root .
python skills/disco/xrayglm/sub-skills/inference/scripts/check_cli_contract.py --repo-root .
python skills/disco/xrayglm/sub-skills/inference/scripts/check_web_contract.py --repo-root .
```

A passing result means that expected source constructs and a tiny PIL contract
were found. It does not load a checkpoint, tokenizer, CUDA kernel, or server.
Use `python cli_demo.py --help` and `python web_demo.py --help` as additional
argument-parser checks; help success is not model readiness.

## 2. Missing checkpoint or tokenizer

**Symptoms:** `FileNotFoundError`, missing config/weight shard, SAT model
configuration error, or an `AutoTokenizer` resolution/cache error.

**Recovery:**

1. Confirm `--from_pretrained` is the intended local checkpoint directory and
   that its config and all referenced weight files are readable.
2. Obtain the checkpoint through an approved source and follow its license;
   do not fabricate missing shards or silently substitute a base language
   model.
3. Separately verify that the compatible `THUDM/chatglm-6b` tokenizer and
   remote-code files are in the approved cache or can be resolved under the
   network policy. If the network is disabled, a cold cache is a hard block.
4. Retry a load only after both prerequisites exist. Record the checkpoint
   identity and tokenizer identity in the experiment log.

A local checkpoint plus a local image, with no GPU and no tokenizer cache, is
an input-ready but model-unready state. Report it explicitly; do not promise
CPU inference or claim the model ran.

## 3. Dependencies and imports

The known compatible reference imported `model`, `model.chat`, `model.blip2`,
`model.visualglm`, `model.infer_util`, `cli_demo`, `web_demo`,
`finetune_XrayGLM`, and `lora_mixin` after compatible dependency pinning.
If imports fail:

- activate the intended Python 3.10 environment;
- compare torch/torchvision CUDA build compatibility;
- install the normal requirements, or the no-deepspeed requirements plus the
  no-deps SwissArmyTransformer workaround;
- check `transformers` and `cpm_kernels` before changing SAT;
- avoid upgrading everything at once, since this code targets older APIs.

The `deepspeed` package is unnecessary for ordinary inference but appears in
the normal requirements. On systems where it cannot install, use the
no-deepspeed requirements for inference and document the choice.

## 4. CUDA, memory, and quantization

**Symptoms:** no CUDA device, `invalid device function`, missing libcudart,
CUDA out of memory, bitsandbytes warnings, or failure inside quantization.

Check `python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())"`
and inspect free memory without embedding private machine paths in the skill
or reports. A successful torch CUDA smoke test is useful, but custom SAT or
bitsandbytes kernels can still fail.

For out-of-memory, close competing jobs, lower `--max_length`, use a smaller
compatible checkpoint, or test an approved quantization mode. Do not assume
4-bit is always lighter or accurate enough. The observed bitsandbytes 0.39.0
was CPU-only/missing libcudart in this environment; repair the CUDA-linked
installation and verify a real quantized load before using `--quant 4` or
`--quant 8`. A parsed flag or successful import is insufficient.

Do not force `.cuda()` on a host with no usable CUDA device. The demos' CPU
branch is an initialization fallback, not evidence that full visual
inference is practical or supported on CPU.

## 5. Image and URL failures

**Symptoms:** PIL cannot identify the image, URL timeout, empty WebUI image,
wrong modality, or the answer ignores the image.

For a local file, check existence, permissions, nonzero size, and PIL decode;
convert to RGB and use a bounded image size. For a URL, use an allowlisted
HTTPS origin, enforce request and response-size limits in a wrapper, reject
non-image content, and avoid internal/private network destinations. The
built-in helper only applies a 10-second request timeout and does not provide
all of those protections.

An image tag can parse while the model remains unavailable. Conversely, a
valid image can reach a text-only branch if the marker/cache contract is
broken. Check the prompt representation, `image` exclusivity, and returned
cache tensor before investigating generation quality.

## 6. Conversation and WebUI behavior

The CLI keeps history as `(query, response)` pairs and caches the processed
image after the first turn. Set the path to `None` on later turns and pass the
returned image. Use `clear` between studies. To switch Chinese to English,
start a fresh English CLI session rather than mixing `问：/答：` with `Q:/A:`.
For a Chinese-to-English test with a URL, explicitly record whether the image
was fetched once and reused as a tensor, or fetched again in a new session.

The WebUI callback rejects an empty image or text before inference. It exposes
Temperature and Top P, while Top K and max length remain internal defaults
(100 and 2048). `--share` publishes a Gradio endpoint and should not be used
with patient data unless expressly approved. If the UI says “Timeout,” inspect
the terminal: the callback uses that message for broad exceptions, not only
wall-clock timeouts. Clear/upload events reset displayed history, but clear
state deliberately before changing a subject.

## 7. Quality and safety

Nondeterministic or clinically implausible output is not fixed by repeating a
prompt blindly. Record image quality, language branch, checkpoint, sampling,
quantization, and history. Compare against clinician-reviewed ground truth in
an approved evaluation workflow. XrayGLM output is research assistance only,
not diagnosis, and cannot replace a radiologist or other qualified clinician.
