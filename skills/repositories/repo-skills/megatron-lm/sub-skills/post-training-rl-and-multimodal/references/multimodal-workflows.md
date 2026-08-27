# VLM, multimodal, and MIMO workflows

## Surface map

Megatron's multimodal examples include image/text/video data preparation, vision encoders, language-model providers, evaluation scripts, checkpoint combination/conversion, and MIMO/AVLM heterogeneous training.

Treat these as separate contracts:

1. media/data schema and storage
2. encoder/tokenizer/model-provider construction
3. heterogeneous topology (encoder and LLM TP/DP/CP/PP/EP)
4. training or inference command
5. evaluation/output artifacts

## Preflight checklist

- Identify image/audio/video format and manifest/task encoder.
- Confirm media paths are mounted/visible to all relevant ranks.
- Verify vision/audio encoder dependency and checkpoint.
- Check tokenizer and text vocabulary compatibility.
- Compute encoder and LLM parallel grids; do not copy a MIMO config to a different GPU count without re-deriving the grid.
- Use mock data only when the model provider explicitly supports it; mock text is not proof that media decoding works.

## Outputs to validate

- batch keys include expected media/text features and masks
- encoder and LLM shapes match the model provider
- checkpoints combine/load with the expected format
- evaluation scripts write deterministic, inspectable results

## Scope note

The multimodal surface is broad and hardware/data-dependent. Generated guidance should route concrete model names and config files to the nearest example family but should not claim every encoder, video dataset, or evaluation benchmark is covered.
