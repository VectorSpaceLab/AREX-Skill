# Model integration troubleshooting

## Registration is not discovered

Symptoms:

- A model that should use an Omni pipeline falls back to ordinary vLLM behavior.
- The server accepts the model name but exposes the wrong endpoint or stage count.
- `--deploy-config` works only when passed explicitly, not by default.

Likely causes:

- `model_type`, architecture, or Diffusers class name does not match the registry predicate.
- Default deploy config name is missing or mismatched.
- Package entry-point/model registration plugin was not imported before vLLM worker startup.
- Editable checkout version mismatch means the installed package is not the intended revision.

Recovery:

1. Verify `import vllm_omni` happens before expecting model registration side effects.
2. Check the model family's pipeline registration, default deploy config name, and endpoint restrictions together.
3. Confirm that stage IDs in the deploy config match the pipeline stages.
4. Run a parser/config check before launching a full model.

## Custom pipeline import fails

Symptoms:

- `ModuleNotFoundError` or `AttributeError` for `custom_pipeline_args["pipeline_class"]`.
- Worker starts but then fails to call `forward`.
- The base pipeline loads twice or loads before custom initialization.

Likely causes:

- The custom module is not on `PYTHONPATH` or installed in the serving environment.
- The class constructor does not match expected keyword arguments.
- `diffusion_load_format` was left at `default` when a dummy/custom initialization path was intended.
- Custom output fields are not handled by the output formatter.

Recovery:

1. Import the custom class in a plain Python process before starting the server.
2. Use `diffusion_load_format="dummy"` when the custom pipeline should own initialization.
3. Keep the class constructor compatible with native pipeline expectations.
4. Return only fields the output formatter can serialize, or update output formatting/tests.

## TTS adapter check fails

Symptoms:

- Static checker cannot find an adapter class.
- Runtime returns audio metadata but no audio bytes/chunks.
- Streaming speech fails only when forced aligner or custom voice mode is enabled.

Likely causes:

- Adapter method names or response helpers diverged from the serving code's expectations.
- Optional dependency for phonemization, token-to-waveform, forced alignment, or text normalization is missing.
- Reference audio/task-type schema differs between model modes such as CustomVoice, VoiceDesign, and Base.

Recovery:

1. Run `scripts/check_tts_adapter_contract.py --adapter-file <file>` for static warnings.
2. Inspect optional imports and keep them lazy with actionable error messages.
3. Add a CPU unit test for schema conversion before full audio generation.
4. Run a small cached-model audio smoke only after optional dependencies and hardware are available.

## Deploy config does not match model integration

Symptoms:

- Unknown stage ID, connector reference error, or headless worker never registers.
- Stage output type is not what the endpoint expects.
- The model works offline but server launch fails with stage topology errors.

Likely causes:

- `PipelineConfig.stages` and deploy YAML `stages` diverged.
- `input_connectors` / `output_connectors` refer to names not declared under `connectors`.
- A platform override changes a field that should stay pipeline-wide.
- The endpoint restriction or final stage ID is wrong for the model's output modality.

Recovery:

1. Run the stage-configuration deploy validator on the YAML.
2. Check `model_type`, default deploy config name, stage IDs, and endpoint restrictions as one unit.
3. Use a single-runtime launch first, then split head/headless after the topology is valid.
4. Keep connector choices consistent with same-host vs cross-host deployment.

## Full-model tests are too slow or blocked

Symptoms:

- Test starts downloading large checkpoints or stalls on gated model access.
- CUDA OOM occurs before the code path under test is reached.
- Benchmark/nightly scripts require services, dashboards, or private data.

Likely causes:

- The selected test is an e2e model example rather than a unit/config test.
- The model needs more VRAM, multiple GPUs, or a specific backend family.
- The task is validating guidance rather than proving full model quality.

Recovery:

1. Replace the broad test with a CPU/static/parser/config test for the changed surface.
2. Mark model-running validation as requiring checkpoint cache, license, GPU, and time.
3. Use a synthetic assertion-backed case for guidance quality while preserving the backend block.
4. Escalate to full model verification only when the user approves the required runtime.
