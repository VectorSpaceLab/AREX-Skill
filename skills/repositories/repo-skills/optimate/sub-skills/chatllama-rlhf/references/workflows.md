# ChatLLaMA Workflows

## Dataset preparation

1. Create or download the actor/reward/RLHF JSON datasets.
2. Use the source dataset helpers when you want the SHP or Anthropic formatting.
3. Clean the dataset with `BaseDataset.clean_dataset(...)` if the sequences are too long for the target models.

## Reward-model workflow

1. Prepare `reward_training_data.json`.
2. Run `generate_rewards.py` when you want the source-style synthetic scoring step.
3. Launch `main.py --type REWARD` to train the reward model.

## Actor workflow

1. Prepare `actor_training_data.json`.
2. Launch `main.py --type ACTOR` to pretrain the actor model.
3. Use `-a/--actor` if you want to override the actor model name.

## RLHF workflow

1. Prepare `rlhf_training_data.json`.
2. Launch `main.py --type RL` to run the reward, actor, and RL stages with the aligned sequence length.
3. Use `main.py --type ALL` when you want the full source-order pipeline: reward, actor, then RL.

## Practical notes

- The config file determines model names, batch sizes, checkpoint locations, and the DeepSpeed/Accelerate/PEFT options.
- External model weights or dataset downloads may be required by the selected training branch.
- The bundled probe script only validates config and dataset shape; it does not train or download.
