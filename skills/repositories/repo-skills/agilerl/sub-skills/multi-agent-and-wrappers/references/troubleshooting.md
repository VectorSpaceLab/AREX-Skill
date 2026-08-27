# Multi-Agent Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Agent spaces mismatch | `agent_ids`, observation spaces, and action spaces are not in the same order | Build a single ordered list and derive spaces from it consistently. |
| Group config not applied | Agent IDs do not follow `<group>_<idx>` or group key is misspelled | Normalize IDs and config keys before population creation. |
| PettingZoo env wrapper fails | AEC env used where parallel env is expected | Use `parallel_env(...)` or convert explicitly before vectorization. |
| Async observations/actions fail | Environment returns only active agents and wrapper is missing or unsupported | Use `AsyncAgentsWrapper` only with supported algorithms and validate active-agent keys. |
| Shared memory/vector process errors | Env factory is not picklable or top-level code starts workers recursively | Define import-safe factory functions and guard the entry point. |
| Multi-agent replay sampling fails | Missing agent key, inconsistent shapes, or wrong field names | Validate every transition dictionary before adding to replay. |
| PettingZoo/SuperSuit env missing | Optional environment package is not installed | Install the specific PettingZoo environment family and SuperSuit as needed. |

## Debug Checklist

1. Print `agent_ids`, observation spaces, and action spaces.
2. Validate group prefixes and `net_config` keys.
3. Run a single environment reset/step without training.
4. Add vectorization with a small `num_envs`.
5. Add replay or rollout collection.
6. Add HPO after space and wrapper behavior is stable.
