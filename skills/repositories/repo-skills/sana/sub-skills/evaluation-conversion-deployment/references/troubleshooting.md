# Troubleshooting

Use this guide when planning evaluation, conversion, upload, or deployment
commands for Sana.

## Missing benchmark environments

### GenEval env missing
Symptoms:
- `geneval` launcher cannot import its metric stack.
- The evaluation helper complains about detector or benchmark dependencies.

Action:
- Confirm the dedicated GenEval environment exists before planning the run.
- Do not treat the main Sana environment as a substitute for the benchmark env.
- If the detector cache is missing, plan the cache bootstrap step separately.

### DPG env missing
Symptoms:
- DPG launcher imports fail or the accelerator launch cannot find the DPG stack.

Action:
- Confirm the dedicated DPG environment exists before planning the run.
- Keep the benchmark launcher and the model-generation environment separate.

## Missing benchmark data

Symptoms:
- MJHQ-30K images or metadata are absent.
- GenEval prompt or detector assets are absent.
- DPG metadata CSV is absent.
- ImageReward benchmark prompts are absent.

Action:
- Stop at planning and report the missing dataset path.
- Do not guess a substitute benchmark.
- Do not promise metric values without the benchmark assets.

## Wrong checkpoint or model path

Symptoms:
- Conversion or metric wrappers point to a path that does not exist.
- The checkpoint family does not match the selected model type.

Action:
- Reconcile the source checkpoint, target family, and precision first.
- For conversion, ensure the `model_type`, `image_size` or `video_size`, and dtype are compatible.
- For metrics, ensure the run directory or checkpoint manifest actually points to generated images or checkpoints.

## WandB login or offline issues

Symptoms:
- Online metric logging fails.
- The tracker complains about authentication or missing project state.

Action:
- Disable the logging flag when online sync is not needed.
- If wandb is intentionally offline, make that explicit in the plan.
- Do not assume another tracker backend is wired into the metric helper.

## HF token safety

Symptoms:
- The user wants to upload or launch a job with Hugging Face credentials.

Action:
- Treat the token as a secret and avoid echoing it in rendered commands.
- Prefer environment injection over inline literal tokens in visible notes.
- Do not print the token back in planner output.

## SLURM env vars missing

Symptoms:
- `sana-run` cannot find `SANA_SLURM_ACCOUNT` or `SANA_SLURM_PARTITION`.

Action:
- Tell the user the launcher cannot build the `srun` command until both vars are set.
- Keep the command in dry-plan form until the values are available.

## Upload size and private repo behavior

Symptoms:
- Large files are skipped.
- Uploads do not appear where expected.

Action:
- Remember the uploader enforces per-file and per-commit size ceilings.
- Check the exclude patterns before assuming a file should have uploaded.
- Verify whether the target is a model repo or dataset repo.
- Default to private repo behavior unless the plan explicitly says otherwise.

## SGLang support and offload choices

Symptoms:
- The user asks for a model or memory mode that the deployment path cannot support.

Action:
- Confirm the requested model matches a Sana diffusers family that SGLang supports.
- Use CPU offload options only as a memory workaround, and warn about the speed trade-off.
- If the GPU budget is too small, recommend a different route rather than pretending the deployment is lossless.

## Conversion dtype or model-type mismatch

Symptoms:
- The source checkpoint family and target `model_type` disagree.
- The requested dtype does not match the model family or downstream export.

Action:
- Stop and reconcile the model family, precision, and target pipeline before planning the command.
- For video exports, also confirm the task and scheduler choice.
- For quantization, confirm the SVDQuant/Nunchaku path is intentional.

## Output-path validation

Symptoms:
- The target export directory is unsafe or ambiguous.

Action:
- Require a writable, explicit dump path.
- Warn if the destination looks like a source checkpoint location or an unrelated model folder.
- If overwriting is possible, require an explicit decision before planning beyond a dry run.

## Native checks that are safe

Safe checks that can be planned or run without heavy model work:
- `sana-run --help`
- `sana-upload --help`
- command rendering from the bundled planners

Treat actual metrics, conversion, uploads, and deployment launches as operations that mutate local or remote state and require explicit approval.
