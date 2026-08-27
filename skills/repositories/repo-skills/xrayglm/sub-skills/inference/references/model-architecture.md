# Model architecture and load contract

XrayGLM adapts VisualGLM-6B for chest-radiograph conversations. This page
keeps only the runtime facts needed to load and troubleshoot it; it does not
bundle model code or weights.

## Load path

The demos call SAT's `AutoModel.from_pretrained` with a checkpoint/model
identifier and an argument namespace containing `fp16=True`, `skip_init=True`,
GPU initialization when CUDA is available and no quantization is requested,
and a CUDA or CPU device selection. The model is put in evaluation mode and
receives SAT's `CachedAutoregressiveMixin` under the `auto-regressive` name.
If quantization is requested, SAT's `quantize(model.transformer, bits)` runs
after construction. The CLI leaves the model on the selected device through
that load path; the WebUI explicitly calls `.cuda()` when CUDA is available.

The tokenizer is loaded independently with:

```text
AutoTokenizer.from_pretrained("THUDM/chatglm-6b", trust_remote_code=True)
```

This means two prerequisites must be checked independently:

1. the XrayGLM/VisualGLM checkpoint contains a compatible SAT configuration and
   all required weight shards; and
2. the ChatGLM tokenizer/configuration can be resolved from an approved local
   cache or network source.

A checkpoint directory alone is not proof that tokenizer files are present.
Conversely, a tokenizer that loads does not prove checkpoint compatibility.

## Visual path

`VisualGLMModel` extends the SAT ChatGLM model and adds an image mixin. The
mixin owns a BLIP-2-style visual module and replaces the configured image
placeholder span with projected visual embeddings. The default image length
is 32 tokens. The visual module consists of:

- an EVA ViT image encoder;
- a Q-Former that consumes visual encoder output and produces query features;
- a linear `glm_proj` from 768 hidden units to the language model's 4096-unit
  space.

The image processor converts RGB pixels to a normalized square tensor. Chat's
runtime processor uses a 224-pixel square; the standalone
`BlipImageEvalProcessor` constructor defaults to 384. Do not alter this size
for a model run without an experiment-specific reason.

The image mixin skips visual insertion when there is no image or when the
placeholder position is outside the input. Therefore a malformed marker,
empty/failed image decode, or a cached image passed at the wrong time can
silently become a text-only path or fail later during generation. Inspect the
input contract before blaming weights.

## Generation

`chat` builds GLM token/attention/position inputs, reserves the visual image
length when an image is present, and calls SAT `filling_sequence` with a
`BaseStrategy`. The strategy receives temperature, top-p, top-k,
repetition-penalty, EOS token, and optional invalid token slices. It then
reorders/decodes the generated sequence and extracts text after `答：` in
Chinese or `A:` in English.

The English CLI branch supplies an invalid token slice covering a configured
range; it is a compatibility behavior of the demo, not a general language
safety filter. Do not interpret it as a quality guarantee.

## Device and quantization implications

The verified host had CUDA-capable A100 hardware and a successful torch CUDA
smoke test, but absence of `nvcc` is not itself a failure. Runtime success
still depends on the installed PyTorch CUDA build, driver compatibility, SAT,
custom kernels, memory, and checkpoint dtype. The observed bitsandbytes 0.39.0
installation warned that it was CPU-only or missing libcudart. Consequently,
`--quant 4`/`--quant 8` must be validated by an actual model load and short
inference, not by argument parsing or package import alone.

Do not use this route to train, fine-tune, construct datasets, or prepare
LoRA data. Those operations require sibling routes and a separate environment
and resource plan.
