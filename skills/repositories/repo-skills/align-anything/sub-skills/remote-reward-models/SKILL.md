---
name: remote-reward-models
description: "Operate Align-Anything remote reward servers, payload checks, and
  PPO remote-RM wiring."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Remote Reward Models

Use this sub-skill when you need to:
- start a local remote reward server
- validate the HTTP payload contract
- wire PPO training to a remote reward endpoint
- debug address, port, dataset, reward-type, or reward-function failures

## Fast route
1. Read `references/remote-rm-contract.md`.
2. Start the server with `scripts/start_remote_rm_template.sh` or the `python -m align_anything.models.remote_rm.run_reward_server` pattern.
3. Validate `/get_reward` with `scripts/probe_remote_rm_payload.py`.
4. If PPO still fails, check `references/troubleshooting.md`.
5. For PPO remote RM, use the adapted qwen2_5_vl launch pattern captured here: start the reward server first, export `REMOTE_RM_URL`, then run `deepspeed --module align_anything.trainers.text_to_text.ppo_remote_rm`.

## What this sub-skill covers
- Flask reward server lifecycle
- reward function registration and dataset-backed math verification
- `RemoteRewardModel` client calls and retries
- PPO remote RM config keys and launch order
- common failures around payload shape, reward type, dataset mapping, and tokenizer mismatch

## Primary facts
- Server entry point: `python -m align_anything.models.remote_rm.run_reward_server`
- HTTP endpoint: POST `/get_reward`
- Client class: `align_anything.models.remote_rm.remote_rm_client.RemoteRewardModel`
- PPO trainer: `align_anything.trainers.text_to_text.ppo_remote_rm`
- Math verifier reward: `math_verifier_reward_function`
- Bundled launch helpers: `scripts/start_remote_rm_template.sh`, `scripts/probe_remote_rm_payload.py`

## What is out of scope
- editing source implementation outside the skill tree
- production hardening, auth, or multi-tenant deployment
- non-HTTP reward training paths that do not use the remote RM server
