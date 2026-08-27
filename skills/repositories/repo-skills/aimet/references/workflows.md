# AIMET workflow recipes

Use this reference for end-to-end patterns. Keep the examples small when debugging; only scale up to ImageNet, Hugging Face, GenAILab, cluster/Pod, S3/AWS, GitHub Actions, or target SDK workflows when the user provides the required assets, credentials, and budget.

## PyTorch QuantSim/PTQ/QAT loop

1. Put the model in `eval()` mode for PTQ calibration.
2. Prepare the model if it uses functional activations or reused modules.
3. Fold BatchNorm when the deployment runtime expects folded layers.
4. Create `aimet_torch.QuantizationSimModel` with the chosen bit widths and optional config file.
5. Calibrate with representative data.
6. Evaluate FP32 vs quantized behavior.
7. Export the model plus encodings.
8. Move to QAT only if PTQ is insufficient and the user can tune training.

## ONNX QuantSim/PTQ loop

1. Start from a valid `onnx.ModelProto` and simplify it if necessary.
2. Choose precision and providers.
3. Create `aimet_onnx.QuantizationSimModel`.
4. Calibrate with `{input_name: np_array}` batches.
5. Apply SeqMSE, AdaRound, or blockwise/precision overrides if needed.
6. Evaluate and export either plain AIMET artifacts or QDQ graphs.

## Accuracy debugging sequence

1. Confirm the FP32 baseline.
2. Isolate weight sensitivity versus activation sensitivity.
3. Use per-channel quantization, BatchNorm folding, Cross-Layer Equalization, AdaRound, or SeqMSE for weight problems.
4. Use range adjustments or mixed precision for activation problems.
5. Analyze sensitive layers before changing many knobs at once.
6. Use QAT only after the PTQ path is exhausted.

## Compression loop

1. Select compression ratios and a cost metric.
2. Apply Weight SVD, Spatial SVD, or Channel Pruning.
3. Evaluate the compressed model.
4. Fine-tune if needed.

## GenAILab scorecard loop

1. Start from a YAML document with `model`, `metrics`, optional `precision`, optional `recipe`, and optional `export` or `eval_in_onnx`.
2. Run `scripts/genai_config_preflight.py config.yaml --framework <torch|onnx|both> --print-command` before allocating GPU time.
3. Verify model access (`HF_TOKEN` or local checkpoint path), benchmark dataset availability, CUDA memory, and cache directories.
4. Run locally with `python -m GenAILab --framework <framework> --config config.yaml ...` when the environment is prepared.
5. Use `--online`, `--wait`, and `--download <run_id>` only when GitHub Actions credentials and pushed branch state are acceptable.
6. Compare results only when metric names and `scoring_version` match.

## Credentialed model/download loop

1. Identify which boundary is active: Hugging Face, GitHub Actions, AWS/S3/SAML, or Qualcomm AI Hub.
2. Verify credentials with a non-secret command such as `hf auth whoami`, `gh auth status`, `aws sts get-caller-identity --profile <profile>`, or AI Hub auth tooling.
3. Use explicit model, FP, recipe, and ONNX cache directories for repeated evaluations.
4. Use `scripts/download_genai_checkpoint.sh --dry-run <url>` before S3 checkpoint downloads; run the real download only after credentials are valid.

## Cluster/Pod execution loop

1. Run `scripts/cluster_pod_helper.sh preflight --namespace <ns>` to verify Argo/Kubernetes access.
2. Launch only after the user approves remote-state and quota usage: `scripts/cluster_pod_helper.sh launch -c 8 -g 1 -m 32Gi`.
3. Sync once with `scripts/cluster_pod_helper.sh sync-once --pod <pod> --local-dir <repo> --remote-dir /scratch/aimet`.
4. Execute bounded commands with `scripts/cluster_pod_helper.sh exec --pod <pod> -- bash -lc 'cd /scratch/aimet && ...'`.
5. Stop workflows with `scripts/cluster_pod_helper.sh stop <workflow>` when finished.

## Export and Qualcomm deployment loop

1. Export the quantized model and encodings together.
2. Inspect the export directory with `scripts/inspect_export.py`.
3. Verify ONNX Runtime provider availability if CUDA provider behavior matters.
4. For local QAIRT/QNN, generate the conversion, quantization, context-binary, and `qnn-net-run` sequence with `scripts/qairt_command_builder.py`.
5. For Qualcomm AI Hub, dry-run and then submit compile/profile/inference through `scripts/qai_hub_qnn_job.py` when `qai_hub` credentials and target device access are present.
6. Do not claim target-device correctness until the target runtime accepts the artifacts and returns profile/inference evidence.
