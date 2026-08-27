# HPO Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `HyperparameterConfig` field has no effect | Field name does not match an algorithm attribute | Inspect the algorithm attributes and use exact names such as `lr`, `batch_size`, or `learn_step`. |
| Mutation never changes agents | `no_mutation` probability too high, unsupported mutation type, or no registered mutable networks/hyperparameters | Lower `no_mutation`, enable relevant probabilities, and verify registry contents. |
| Activation mutation warning or no-op | Some algorithms/modules do not support activation mutation | Set `activation=0` or use modules that expose activation mutation. |
| Population size errors | `INIT_HP["POP_SIZE"]`, `population_size`, and tournament population size disagree | Keep all population-size values aligned. |
| Tournament selects unexpected agents | Fitness history or `eval_loop` not populated as expected | Confirm each agent has recent fitness values and that evaluation runs before selection. |
| Architecture mutation fails for LLM | LLM algorithms do not generally support architecture mutation | Use RL hyperparameter mutation only for LLM workflows. |
| Multi-agent mutation seems uneven | Heterogeneous agents or centralized critics do not share identical mutation methods | Use group-aware `net_config` and read the multi-agent sub-skill. |

## Probability Guidance

Mutation probabilities do not need to sum to exactly one in every helper pattern, but they should reflect deliberate relative rates. Avoid setting every mutation type high during debugging; start with one mutation path at a time so failures are attributable.

## Debug Checklist

1. Confirm the population contains AgileRL evolvable algorithms.
2. Print or inspect mutable hyperparameter config.
3. Validate tournament size and population size.
4. Run one mutation pass with a fixed seed.
5. Compare pre/post hyperparameter values and network architecture summaries.
