# LLM API Reference

## Algorithms

- `agilerl.algorithms.grpo.GRPO`
- `agilerl.algorithms.cispo.CISPO`
- `agilerl.algorithms.gspo.GSPO`
- `agilerl.algorithms.ppo_llm.PPO`
- `agilerl.algorithms.reinforce_llm.REINFORCE`
- `agilerl.algorithms.sft.SFT`
- `agilerl.algorithms.dpo.DPO`

## Training Helpers

- `agilerl.training.train_llm.finetune_llm_reasoning(...)`
- `agilerl.training.train_llm.finetune_llm_preference(...)`
- `agilerl.training.train_llm.finetune_llm_multiturn(...)`
- `agilerl.training.train_llm.finetune_llm_sft(...)`

## LLM Environments And Data

- `agilerl.llm_envs.base.HuggingFaceGym`
- `agilerl.llm_envs.preference.PreferenceGym`
- `agilerl.llm_envs.reasoning.ReasoningGym`
- `agilerl.llm_envs.sft.SFTGym`
- `agilerl.llm_envs.sync_vec_env.SyncMultiTurnVecEnv`
- `agilerl.llm_envs.token_observation.TokenObservationWrapper`
- `agilerl.data.rl_data` reward/dataset helpers
- `agilerl.data.tokenizer` tokenizer abstractions
- `agilerl.utils.llm_utils` and `agilerl.utils.llm_packing`

## Optional Stack

The `[llm]` extra includes LLM-specific dependencies such as datasets, PEFT, Transformers, vLLM, DeepSpeed, bitsandbytes, and liger-kernel where supported. Keep hardware/backend checks separate from ordinary AgileRL import checks.
