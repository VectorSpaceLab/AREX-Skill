# Alignment API Reference

## Reward Model Paths

- `RewardModelTunerArguments`
- `RewardModelInferencer`

## DPO Paths

- `DPOAlignerArguments`
- `DPOAligner`
- `DPOv2AlignerArguments`
- `DPOv2Aligner`

## Iterative DPO Paths

- `IterativeAlignerArguments`
- `IterativeDPOAlignerArguments`
- `IterativeDPOAligner`

## RAFT Paths

- `RaftAlignerArguments`
- `RaftAligner`

## Notes

- DPO and DPOv2 are separate alignment families even though they both use chosen/rejected preference data.
- Iterative DPO usually needs more than one model role: base, reference, and reward.
- RAFT uses reward-ranked fine-tuning and benefits from data-cleaning rules in the workflow reference.
- Merge-LoRA is a model-save workflow rather than a learning workflow.
