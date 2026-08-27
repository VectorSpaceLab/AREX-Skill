# Training and merge troubleshooting

## Import and package issues

- If the training CLIs import the wrong PEFT code, run the script from `scripts/training/` so the bundled `peft/` package is visible first.
- If `torch` or `transformers` fail to import, fix the private inspection environment before retrying the scripts.
- Keep the installation set minimal; the training path does not need the optional serving packages.

## Dataset issues

- Missing `instruction`, `input`, or `output` keys usually means the JSON schema does not match the expected instruction-tuning format.
- Empty validation data is acceptable only when the CLI explicitly falls back to a train/validation split.
- Cache directories are created automatically per dataset filename and max sequence length.

## Training configuration issues

- DeepSpeed stage-2 config errors usually come from a mismatch between the launch script and the local JSON config.
- LoRA merge errors almost always mean the base checkpoint and the adapter checkpoint do not belong to the same model family.
- Quantized training flags and gradient checkpointing are tightly coupled; review the CLI help before changing one without the other.

## Optional dependency issues

- `bitsandbytes` is only needed for the quantized training or inference branches.
- Flash-attention is optional and should be treated as an acceleration path, not a hard prerequisite for the training docs in this skill.
