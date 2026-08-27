# Runtime SDK and edge guidance

This reference covers the lower-level deployment families that sit below the packaged HTTP and WebSocket servers: ONNXRuntime binaries, libtorch, GGUF / llama.cpp, and Triton.

## Prefer the packaged servers first

If the caller only needs a service endpoint, start with `funasr-server` or `funasr-realtime-server`. Move to the lower-level runtime families only when you need one of these:

- a native JSONL transcript binary on CPU or edge hardware
- a Python-free edge binary
- TorchScript / libtorch inference
- a GPU deployment stack that is managed by Triton
- a model-repository or binary-wrapper layout that the packaged servers do not cover

## Decision table

| Need | Better fit | Why |
|---|---|---|
| HTTP API for local apps | Packaged HTTP server | Lowest setup cost. |
| Streaming WebSocket service | Packaged realtime server | Handles session control and partial decoding. |
| Offline / 2-pass machine-readable output | ONNXRuntime binaries | Emit JSONL and fit batch tooling. |
| Python-free edge inference | GGUF / llama.cpp | CPU-first, quantized, no Python at runtime. |
| TorchScript-based deployment | libtorch | Useful when the runtime is already TorchScript-friendly. |
| Managed GPU serving | Triton | Good when you want model repositories, backend control, and GPU scheduling. |

## ONNXRuntime binaries

Use ONNXRuntime when you want the native offline, online, or two-pass binaries to produce one JSON record per completed input.

```bash
funasr-onnx-offline \
  --model-dir /path/to/model \
  --wav-path /path/to/audio.wav \
  --output-format jsonl

funasr-onnx-2pass \
  --model-dir /path/to/offline-model \
  --online-model-dir /path/to/online-model \
  --vad-dir /path/to/vad-model \
  --punc-dir /path/to/online-punctuation-model \
  --wav-path /path/to/audio.wav \
  --mode 2pass \
  --output-format jsonl
```

### What to expect

- `offline`, `online`, and `2pass` are the valid modes.
- The `2pass` runtime needs both a VAD model and an online punctuation model.
- JSONL output is written to stdout.
- Diagnostics and progress messages stay on stderr.
- Each record can include `key`, `mode`, `text`, `timestamp`, and `stamp_sents`.

### Useful when

- you need a native integration with batch tooling
- you want machine-readable results from a lower-level runtime
- you are debugging timestamps or sentence-level output without standing up a web server

## libtorch

Use the libtorch path when your model has already been exported to TorchScript and you want the runtime to stay close to PyTorch semantics without using the full Python package.

Typical model directories contain:

- `model.torchscript`
- `config.yaml`
- `am.mvn`

That path is useful when the environment already has TorchScript deployment conventions and you do not need the HTTP or WebSocket service layers.

## GGUF / llama.cpp

Use the GGUF path when you need CPU-first, edge-friendly binaries with no Python runtime. Start from the prebuilt GGUF assets or the runtime family's model-download helper, then run the matching `llama-funasr-*` binary for the model family you want.

```bash
llama-funasr-sensevoice -m sensevoice-small-q8.gguf -a sample.wav --backend cpu
llama-funasr-paraformer -m paraformer-q8.gguf -a sample.wav --backend cpu
llama-funasr-cli -m fun-asr-nano-q8_0.gguf --vad fsmn-vad.gguf -a sample.wav --backend cpu
```

### Why it is attractive

- no Python ML runtime is required at inference time
- weights are quantized and portable for edge usage
- built-in VAD support helps long-audio segmentation
- the default backend is CPU, which makes first-run behavior predictable

### Caveats

- backend switches such as CUDA or Vulkan are only valid when the binary was built with that backend support
- architecture-specific GPU builds are not portable across arbitrary hardware generations
- a wrapper HTTP server can exist around the binary, but the binary itself is still the primary runtime artifact

## Triton

Use Triton when you need a GPU serving stack with model repositories and backend control.

Typical flow:

1. Export an unquantized ONNX graph for the encoder or model family you want to serve.
2. Build a TensorRT engine only on the same GPU architecture and TensorRT version you will deploy.
3. Keep the ONNX Runtime backend if you do not need TensorRT.
4. Replace the TensorRT config only after the plan is built and validated on the target hardware.

### Important caveats

- TensorRT plans are not portable across GPU compute capabilities or arbitrary TensorRT versions.
- Quantized ONNX graphs are not a drop-in replacement for the TensorRT path.
- The runtime model repository layout matters; make sure the generated plan is placed where the Triton config expects it.

## Legacy runtime examples

The repository also contains older Python HTTP and WebSocket runtime examples. They are useful as protocol references, but the packaged servers are preferred for ordinary serving tasks.

## Boundary notes

- This reference does not own model-family selection for Nano / GLM / Qwen3 or the vLLM tuning story.
- It does not replace the packaged server docs for ordinary HTTP or realtime serving.
- If a user wants a browser demo, desktop automation, or MCP tooling, route back to the client-integration reference.
