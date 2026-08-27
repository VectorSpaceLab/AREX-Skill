# TensorRT, Ascend, and DCU Support

These workflows are optional and hardware-specific. A CPU or generic CUDA import does not verify them.

## TensorRT-LLM

The TensorRT recipe is for NVIDIA deployment through TensorRT-LLM. Use it when the user explicitly targets TensorRT engine conversion or high-performance NVIDIA inference. Verify TensorRT-LLM version, CUDA/toolkit, GPU architecture, checkpoint conversion path, and engine build resources before recommending a build.

## Ascend NPU

The Ascend support path uses a Qwen MindSpore Docker image and host NPU devices. The launch script mounts devices such as `/dev/davinci*`, `/dev/davinci_manager`, `/dev/devmm_svm`, `/dev/hisi_hdc`, host driver directories, `npu-smi`, install info, and logs. It also mounts the checkpoint into the container.

Use this route only when the host has Ascend hardware and the user wants a vendor container workflow. Do not adapt Ascend commands to ordinary CUDA hosts.

## Hygon DCU / fastllm

The DCU support path uses a vendor container, DTK environment setup, and a small `fastllm_pytools` package. The documented flow is:

1. Start a DCU container with `/dev/kfd`, `/dev/dri`, `seccomp=unconfined`, `SYS_PTRACE`, and shared memory.
2. Source the vendor environment script inside the container.
3. Install `dcu-support/package` to provide `fastllm_pytools`.
4. Convert a Qwen Hugging Face checkpoint into an FLM binary with the conversion script.
5. Run CLI, batch CLI, or Streamlit web demo against the FLM file.

The conversion script loads a Qwen checkpoint with Transformers and exports with `torch2flm`. It may require editing the model path for local checkpoints and sufficient CPU/GPU memory for conversion.

## Safety and verification

- Treat vendor containers and device mounts as privileged operations.
- Record exact driver, image, toolkit, device, and checkpoint requirements before running.
- Do not claim verification unless a vendor runtime command actually ran on matching hardware.
- Use static planning when hardware is unavailable.
