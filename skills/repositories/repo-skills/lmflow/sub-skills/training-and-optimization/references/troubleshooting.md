# Training Troubleshooting

## Out-of-Memory

**Symptom**: CUDA OOM, fragmentation errors, or training aborts during the first step.

**Likely cause**: model size, batch size, and sequence length exceed the available memory.

**Recovery**:

- lower `per_device_train_batch_size`;
- raise `gradient_accumulation_steps`;
- shorten `block_size` if the workflow allows it;
- move from full fine-tuning to LoRA/QLoRA/LISA;
- disable expensive extras that are not required.

## Output Directory Already Exists

**Symptom**: LMFlow refuses to start because the output directory is not empty.

**Likely cause**: `overwrite_output_dir` was not intentionally set.

**Recovery**:

- choose a fresh output directory;
- or deliberately enable overwrite;
- or resume from a specific checkpoint after checking the contents.

## W&B Problems

**Symptom**: login prompts, network issues, or unwanted experiment tracking.

**Likely cause**: `report_to` defaults or launcher behavior.

**Recovery**:

- set `report_to` to `none` when tracking is not desired;
- or log in explicitly before the run.

## Missing Optional Dependencies

**Symptom**: import failures for `deepspeed`, `bitsandbytes`, `flash_attn`, or `trl`.

**Likely cause**: the selected workflow needs an extra that is not installed.

**Recovery**: install the exact extra required by the chosen training mode.

## Dataset or Template Mismatch

**Symptom**: training starts but the prompts or labels look wrong.

**Likely cause**: the dataset type or conversation template does not match the model family.

**Recovery**: validate the dataset with the data-and-templates helper and confirm the template name.
