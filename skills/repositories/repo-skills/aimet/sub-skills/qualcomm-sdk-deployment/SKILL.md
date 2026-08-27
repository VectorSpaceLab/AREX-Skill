---
name: qualcomm-sdk-deployment
description: "Prepare AIMET exports for Qualcomm AI Hub, QAIRT/QNN conversion,
  profiling, inference, and SDK command generation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Qualcomm SDK and AI Hub deployment

Use this sub-skill when the user asks how to send AIMET exports to Qualcomm AI Hub, QAIRT, QNN, HTP backends, DLC conversion, `qairt-converter`, `qairt-quantizer`, `qnn-context-binary-generator`, `qnn-net-run`, or AI Hub compile/profile/inference jobs.

## Read/run first

- Read [Qualcomm SDK workflows](../../references/qualcomm-sdk-workflows.md) for artifact requirements and local/remote deployment sequences.
- Run [inspect_export.py](../../scripts/inspect_export.py) on the exported model directory before target handoff.
- Use [qairt_command_builder.py](../../scripts/qairt_command_builder.py) to generate QAIRT/QNN command lines with local paths filled in.
- Use [qai_hub_qnn_job.py](../../scripts/qai_hub_qnn_job.py) for a self-contained AI Hub compile/profile entry point when `qai_hub` is installed and authenticated.
- Read [model access and credentialed evaluation](../model-access-and-credentialed-evaluation/SKILL.md) for AI Hub, AWS, and credential boundaries.

## Core workflow

1. **Validate AIMET artifacts.** You need an exported `.onnx` model and matching AIMET `.encodings` file, or an ONNX QDQ model when the target flow expects QDQ.
2. **Choose local SDK vs AI Hub.** Local QAIRT/QNN commands require installed SDK binaries and libraries; AI Hub requires `qai_hub` credentials and supported devices.
3. **Generate conversion commands.** Feed the AIMET model and encodings into converter/quantizer commands; keep output DLC and context-binary paths explicit.
4. **Compile/profile/infer.** For local SDK, run context-binary generation and net-run with input lists. For AI Hub, submit compile/profile/inference jobs and record job URLs.
5. **Check failure mode.** Distinguish missing encodings, unsupported ops, channel order mismatch, provider/runtime mismatch, and missing target libraries.

## Boundaries

AIMET export validation can be done locally. Target SDK execution cannot be proven unless the SDK, device/backend libraries, input list, and credentials are present. Do not claim target correctness from a successful AIMET QuantSim export alone.

## Expected answer shape

For deployment tasks, include the input artifact paths, target device/runtime, local SDK or AI Hub path, generated commands or API calls, expected output files, and exact credential/SDK assumptions.
