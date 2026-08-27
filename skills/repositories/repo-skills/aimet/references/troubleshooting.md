# AIMET troubleshooting map

## Install and dependency issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: aimet_torch` or `aimet_onnx` | Wrong distribution installed, wrong environment active, or source build failed | Verify `python -m pip show aimet-torch aimet-onnx`, reinstall in a clean Python `>=3.10` environment, then run `scripts/quick_smoke.py`. |
| `pip check` reports version conflicts after installing AIMET | Shared environment contains packages pinning incompatible visualization, Torch, ONNX, or Hugging Face dependencies | Prefer a clean dedicated environment; do not keep downgrading a shared environment unless the user approves. |
| Torch import or AIMET Torch import fails with low-level ABI errors | Torch/CUDA/triton/compiled extension mismatch | Reinstall a coherent Torch/TorchVision pair and use the dependency variant matching the desired CPU/CUDA backend. |
| ONNX QuantSim import fails with missing `onnx_ir`, `onnxscript`, `onnx2torch`, or `onnxruntime` | `aimet-onnx` was installed without dependencies or a partial source install is active | Install missing runtime dependencies or reinstall `aimet-onnx` normally; use `pip check` before debugging graph code. |
| Visualization import fails around Bokeh/HoloViews/HVPlot/Panel | Optional visualization packages are out of sync | Use AIMET's declared Bokeh/HVPlot range and remove unrelated packages that force incompatible visualization versions. |

## Backend issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is false on a GPU host | CPU-only Torch wheel, missing container GPU passthrough, driver/runtime mismatch, or no visible device | Check `nvidia-smi`, Torch CUDA tag, and container runtime; do not treat CPU import as CUDA verification. |
| ONNX Runtime refuses `CUDAExecutionProvider` | `onnxruntime-gpu` is missing or incompatible | Inspect `ort.get_available_providers()`, reinstall the correct ONNX Runtime GPU package, or run CPU provider only. |
| Source CUDA build fails before compile | `nvcc`, CMake, compiler, Eigen, or pkg-config missing | Use a CUDA development image or install the documented system packages before retrying; the bundled build wrapper fails early for missing `nvcc`. |

## PyTorch QuantSim issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Functional activations are not quantized | Model uses `torch.nn.functional` ops in `forward` | Run `aimet_torch.model_preparer.prepare_model` or rewrite functionals as modules before QuantSim. |
| Reused modules produce confusing quantizer behavior | One `nn.Module` instance is called from multiple graph locations | Use model preparer to unroll reused modules or redesign the module structure. |
| Encodings recompute unexpectedly | Frozen weight encodings were not loaded/set correctly or activation encodings are being recalibrated | Use the appropriate freeze/load API and distinguish frozen parameter encodings from recalibrated activation encodings. |
| QAT does not recover accuracy | Calibration is not representative, training hyperparameters are off, or the model is sensitive to low precision | Follow the accuracy-debugging sequence, increase precision for sensitive quantizers, and treat QAT as a training task. |

## ONNX QuantSim issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Calibration callback/input iterator fails | Input dictionary keys or shapes do not match graph inputs | Inspect `model.graph.input` or `sim.session.get_inputs()` and provide `{input_name: np_array}` batches with matching dtypes/shapes. |
| Quantizer insertion is surprising or graph passes fail | Graph has unsupported patterns, missing shape info, custom ops, or unsimplified export artifacts | Validate and simplify the ONNX graph before QuantSim; register user ONNX libraries when custom ops are unavoidable. |
| Loading encodings reports missing or extra quantizers | The encodings file came from a different graph or precision configuration | Compare graph names/tensor names, use strict loading for deployment readiness, and inspect non-strict mismatches before accepting. |
| QDQ export differs from plain export | QDQ graph materializes QuantizeLinear/DequantizeLinear nodes while plain export stores AIMET encodings separately | Choose the export form required by the downstream toolchain and validate both model and encodings. |

## Deployment and artifact issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Target toolchain cannot quantize/compile the model | Missing or mismatched AIMET encodings file | Keep the exported `.onnx` and `.encodings` JSON together; run `scripts/inspect_export.py` before target handoff. |
| Accuracy differs between simulation and target | Unsupported target op, encoding mismatch, missing QDQ/override settings, or calibration mismatch | Compare layer outputs, verify exported encodings, and isolate sensitive quantizers with QuantAnalyzer or per-layer analysis. |
| Compression or examples take too long | Full ImageNet/evaluation loops were launched without a tiny subset | Replace examples with a small evaluator while developing and run full evaluation only after user approval. |

## GenAILab and model-access issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| GenAILab config fails before model load | Missing `model`/`metrics`, unrecognized top-level key, bad recipe/precision shape, or non-terminal recipe surprise | Run `scripts/genai_config_preflight.py config.yaml --framework <torch|onnx|both> --strict`; fix static errors before using GPU time. |
| Hugging Face model or dataset download fails with 401/403 | Missing token, gated terms not accepted, wrong account, or private model path typo | Verify `HF_TOKEN` without printing it, run `hf auth whoami`, accept gated terms, or use a local `model.model_id` path. |
| GenAILab online run ignores local changes | `--online` dispatches GitHub Actions on the pushed branch/ref | Commit/push the change, use `--branch`, or run locally/pod-side for uncommitted experiments. |
| Results table warns about mixed metric versions | `scoring_version` differs for the same metric | Compare only matching versions; rerun the baseline under the current scoring version for a fair comparison. |
| S3 checkpoint download fails | AWS profile missing/expired, SAML login expired, wrong URL shape, or no bucket permission | Run `scripts/download_genai_checkpoint.sh --dry-run <url>`, refresh `saml2aws login --profile <profile>` if needed, then retry. |

## Cluster/Pod issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `cluster_pod_helper.sh preflight` fails | Missing `argo`/`kubectl`/`jq`/`tar` or invalid kube context | Install tools through the organization's approved path and verify namespace access before launch. |
| Pod launches but sync fails | Pod not running, remote directory not writable, or `tar` missing on the pod | Check pod phase, use a writable `/scratch/...` path, and verify `kubectl exec <pod> -- tar --version`. |
| GenAILab fails only on pod | Missing `HF_TOKEN`, incompatible CUDA image, insufficient VRAM, or local changes not synced | Verify token/environment inside the pod, rerun `sync-once`, and start with a small config. |
| Workflow keeps consuming GPU quota | Stop/cleanup was skipped | Run `scripts/cluster_pod_helper.sh list` and `scripts/cluster_pod_helper.sh stop <workflow>` when the run is done. |

## Qualcomm SDK / AI Hub issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `qairt-converter` rejects quantization overrides | `.encodings` file does not match the `.onnx` graph | Re-export model and encodings together, then run `scripts/inspect_export.py` and `scripts/qairt_command_builder.py`. |
| `qairt-*` or `qnn-*` command not found | QAIRT/QNN SDK environment is not sourced | Source the SDK setup script and verify the generated commands after SDK binaries are on `PATH`. |
| AI Hub dry-run passes but real run fails | `qai_hub` missing, credentials expired, unsupported device, or model op unsupported | Authenticate AI Hub, confirm device name/support, and inspect compile/profile job URLs. |
| Accuracy cannot be computed from AI Hub inference | Empty outputs, labels/input batch mismatch, channel order mismatch, or wrong input names | Use actual model input names, per-sample `N=1` arrays, and channel-last conversion only when the compile options require it. |
