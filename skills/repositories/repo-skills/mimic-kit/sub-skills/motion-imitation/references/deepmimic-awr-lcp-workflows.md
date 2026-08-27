# DeepMimic, AWR, LCP, and vault workflows

This reference distills the motion-imitation recipe matrix from the repo README, the DeepMimic/AWR/LCP docs, the env and agent YAMLs, and the env implementations. It is intentionally routed around the generated sub-skill tree, not the original docs.

## Common command pattern

Use the matching arg file as the base recipe, then override only the run-specific flags:

```bash
python ../runner-and-backends/scripts/run_mimickit.py \
  --repo-root <mimickit-checkout> \
  -- --arg_file args/<recipe>_args.txt --mode train --visualize false
python ../runner-and-backends/scripts/run_mimickit.py \
  --repo-root <mimickit-checkout> \
  -- --arg_file args/<recipe>_args.txt --mode test --num_envs 4 --visualize true --model_file data/models/<checkpoint>.pt
```

Practical defaults from the shipped recipes:

- Train with the arg file as-is, or keep `--mode train` explicit when editing commands.
- Test with a checkpoint and a small env count.
- Keep the recipe file, env file, and agent file aligned after every edit.

## Supported recipe families

Character families and task variants visible in the shipped filenames:

- `humanoid`
- `humanoid_sword_shield`
- `g1`
- `go2`
- `pi_plus`
- `smpl`
- `vault` task variants for `humanoid` and `g1`

## Config pair matrix

| Family | Args file | Env config | Agent config | Typical checkpoint / note |
| --- | --- | --- | --- | --- |
| DeepMimic humanoid PPO | `args/deepmimic_humanoid_ppo_args.txt` | `data/envs/deepmimic_humanoid_env.yaml` | `data/agents/deepmimic_humanoid_ppo_agent.yaml` | Docs example: `data/models/deepmimic_humanoid_spinkick_model.pt` |
| DeepMimic humanoid AWR | `args/deepmimic_humanoid_awr_args.txt` | `data/envs/deepmimic_humanoid_env.yaml` | `data/agents/deepmimic_humanoid_awr_agent.yaml` | Docs example: `data/models/deepmimic_humanoid_awr_spinkick_model.pt` |
| DeepMimic humanoid sword/shield PPO | `args/deepmimic_humanoid_sword_shield_ppo_args.txt` | `data/envs/deepmimic_humanoid_sword_shield_env.yaml` | `data/agents/deepmimic_humanoid_ppo_agent.yaml` | Uses the humanoid PPO agent config with a sword/shield env |
| DeepMimic g1 PPO | `args/deepmimic_g1_ppo_args.txt` | `data/envs/deepmimic_g1_env.yaml` | `data/agents/deepmimic_g1_ppo_agent.yaml` | G1 walk / locomotion recipe |
| DeepMimic go2 PPO | `args/deepmimic_go2_ppo_args.txt` | `data/envs/deepmimic_go2_env.yaml` | `data/agents/deepmimic_go2_ppo_agent.yaml` | Quadruped pacing recipe |
| DeepMimic pi_plus PPO | `args/deepmimic_pi_plus_ppo_args.txt` | `data/envs/deepmimic_pi_plus_env.yaml` | `data/agents/deepmimic_pi_plus_ppo_agent.yaml` | High-torque humanoid recipe |
| DeepMimic smpl PPO | `args/deepmimic_smpl_ppo_args.txt` | `data/envs/deepmimic_smpl_env.yaml` | `data/agents/deepmimic_smpl_ppo_agent.yaml` | SMPL motion imitation recipe |
| LCP g1 | `args/lcp_g1_ppo_args.txt` | `data/envs/deepmimic_g1_env.yaml` | `data/agents/lcp_g1_agent.yaml` | Docs example: `data/models/lcp_g1_walk_model.pt` |
| Vault humanoid | `args/vault_humanoid_args.txt` | `data/envs/vault_humanoid_env.yaml` | `data/agents/deepmimic_humanoid_ppo_agent.yaml` | Static-object vault recipe |
| Vault g1 | `args/vault_g1_args.txt` | `data/envs/vault_g1_env.yaml` | `data/agents/deepmimic_g1_ppo_agent.yaml` | Static-object double-kong / vault recipe |

## Command templates

### DeepMimic / AWR / LCP

```bash
# Train
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/deepmimic_humanoid_ppo_args.txt --mode train --visualize false

# Test
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/deepmimic_humanoid_ppo_args.txt --mode test --num_envs 4 --visualize true --model_file data/models/<checkpoint>.pt

# AWR train/test use the AWR arg file instead
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/deepmimic_humanoid_awr_args.txt --mode train --visualize false
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/deepmimic_humanoid_awr_args.txt --mode test --num_envs 4 --visualize true --model_file data/models/<checkpoint>.pt

# LCP g1 train/test
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/lcp_g1_ppo_args.txt --mode train --visualize false
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/lcp_g1_ppo_args.txt --mode test --num_envs 4 --visualize true --model_file data/models/<checkpoint>.pt
```

### Vault and static-object recipes

```bash
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/vault_humanoid_args.txt --mode train --visualize false
python ../runner-and-backends/scripts/run_mimickit.py --repo-root <mimickit-checkout> -- \
  --arg_file args/vault_humanoid_args.txt --mode test --num_envs 4 --visualize true --model_file data/models/<checkpoint>.pt
```

## Train / test / adapt flow

1. Pick the closest shipped recipe family.
2. Edit the environment YAML first when changing motion, target bodies, reward weights, or termination behavior.
3. Edit the agent YAML second when changing PPO/AWR/LCP training knobs.
4. Keep the arg file pointing at the exact env and agent pair you want to run.
5. Train with `--mode train`.
6. Test with `--mode test`, a checkpoint, and a small env count.
7. If you are adapting to a new motion clip or a new object layout, clone the closest YAMLs and keep the character, joint list, and contact list consistent.
8. If you change the observation layout, retrain the agent; test-time loading only works when the model shape still matches the env.

## Vault / static-object notes

`StaticObjectsEnv` extends `DeepMimicEnv` and adds rigid objects from the env YAML:

- Each `objects` entry needs `file` and `pos`; `rot` is optional and defaults to the identity quaternion.
- Objects are spawned with `fix_root=True`, so they are static scene geometry.
- Keep `contact_bodies` aligned to the new vault geometry; otherwise pose termination and fall checks can fire too early.
- The bundled vault envs reference `data/assets/objects/vault_box.xml` and `data/assets/objects/climbing_box.xml`, which are not present in this checkout and must come from external assets.

## Notes on the shipped configs

- The DeepMimic, AWR, LCP, and vault arg files currently use the Isaac Gym engine config.
- `motion_file` may point to a single motion pickle or a dataset YAML under `data/datasets/`.
- `deepmimic_*` and `vault_*` recipes reuse the same PPO-style actor/critic base code; the differences are in the env YAML and, for AWR/LCP, the extra agent knobs.
