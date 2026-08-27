# Legacy OASIS experiment families

This reference summarizes the legacy experiment shapes that matter for analysis and config triage. It is intentionally descriptive, not executable.

## Family map

| Family | Legacy files | What it teaches | Key knobs | Safe stance |
| --- | --- | --- | --- | --- |
| Reddit GPT | `examples/experiment/reddit_gpt_example/gpt_example.yaml`, `reddit_simulation_gpt.py` | Small OpenAI-backed Reddit simulation with controllable users and score display | `user_path`, `pair_path`, `db_path`, `activate_prob`, `num_timesteps`, `round_post_num`, `max_rec_post_len`, `available_actions`, `show_score`, `allow_self_rating` | Good for small-budget adaptation and config reading, but still credential-cost sensitive |
| Reddit electronic mall | `examples/experiment/reddit_emall_demo/emall.yaml`, `emall_simulation.py` | Same Reddit mechanics with product content and purchase behavior | `pair_path` to product seed data, `purchase_product`, `num_timesteps`, `available_actions` | Reference for scenario swapping; action semantics belong to `platform-actions` |
| Twitter GPT | `examples/experiment/twitter_gpt_example/gpt_example.yaml`, `twitter_simulation.py` | CSV-based Twitter simulation using a recommendation system and OpenAI model | `csv_path`, `db_path`, `num_timesteps`, `clock_factor`, `recsys_type`, `available_actions` | Reference only; safe execution still depends on the provider setup |
| Twitter GPT + embeddings | `examples/experiment/twitter_gpt_example_openai_embedding/gpt_example.yaml`, `twitter_simulation.py` | Same Twitter recipe with OpenAI embeddings enabled | `use_openai_embedding`, `model_type`, `csv_path`, `db_path` | Reference only; embedding and provider setup are both prerequisites |
| Alignment with human | `examples/experiment/reddit_simulation_align_with_human/*.yaml`, `reddit_simulation_align_with_human.py` | Large Reddit topic studies with exp-info files and multi-host open-source serving | `exp_info_filename`, `user_path`, `pair_path`, `db_path`, `activate_prob`, `num_timesteps`, `max_rec_post_len`, `round_post_num`, `server_url` | Only after backend, host, and path sanity checks |
| Counterfactual | `examples/experiment/reddit_simulation_counterfactual/*.yaml`, `reddit_simulation_counterfactual.py` | Up/control/down treatment comparisons for Reddit content | `pair_path`, `db_path`, `init_post_score`, `activate_prob`, `num_timesteps`, `round_post_num`, `model_type`, `server_url` | Good for tiny-budget triage or treatment comparison planning |
| Group polarization | `examples/experiment/twitter_simulation/group_polarization/*.yaml`, `twitter_simulation_group_polar.py` | Twitter polarization run and evaluation pattern | `csv_path`, `db_path`, `num_timesteps`, `clock_factor`, `available_actions`, `model_type`, `model_path` or provider flags | Reference for polarization analysis, not a default smoke |
| 1M-agent simulation | `examples/experiment/twitter_simulation_1M_agents/twitter_1m.yaml`, `twitter_simulation_1m.py` | Massive open-source deployment pattern with many server ports | `model_type`, `model_path`, `server_url`, host and ports | Blocked until GPU, model, and server pool are confirmed |

## Cost and token warnings

- The README's small Reddit GPT example is intentionally cheap, but it still implies about 36 agents, `activate_prob` 0.1, and 2 timesteps, which the README frames as roughly 7.2 agent inferences and about 14 API requests.
- The README's small Twitter GPT example is about 111 agents, `activate_prob` around 0.1, and 3 timesteps, which the README frames as roughly 33.3 agent inferences.
- Treat those numbers as warnings, not guarantees. If a request sounds bigger than those examples, assume the cost and runtime will grow quickly.

## Legacy config glossary

| Key | Meaning |
| --- | --- |
| `data.user_path` / `data.csv_path` | Profile source for Reddit JSON or Twitter CSV inputs. |
| `data.pair_path` | Reddit seed pairs, counterfactual content, or product seed data depending on the family. |
| `data.db_path` | SQLite output database for the simulation run. |
| `data.exp_info_filename` | Companion JSON file used by alignment-with-human runs. |
| `simulation.controllable_user` | Whether the run is driven by prepared controllable-user posts. |
| `simulation.allow_self_rating` | Whether self-rating is allowed. |
| `simulation.show_score` | Whether Reddit-style score display is used. |
| `simulation.activate_prob` | Probability that a non-controllable agent acts on a timestep. |
| `simulation.num_timesteps` | Number of simulation timesteps. |
| `simulation.clock_factor` | Time magnification factor; legacy Reddit examples often use 10, Twitter examples often use 60. |
| `simulation.max_rec_post_len` | Maximum size of the recommendation buffer. |
| `simulation.round_post_num` | Number of controllable-user posts injected per timestep. |
| `simulation.refresh_rec_post_count` | Number of posts surfaced on refresh. |
| `simulation.follow_post_agent` / `simulation.mute_post_agent` | Whether agents are forced to follow or mute the controllable user. |
| `simulation.init_post_score` | Initial score for counterfactual posts. |
| `simulation.available_actions` | Action whitelist for the family. |
| `simulation.recsys_type` | Recommendation-system mode such as Reddit or Twitter-oriented behavior. |
| `inference.model_type` | Model identity used by the example. |
| `inference.model_path` | Local model path for open-source serving. |
| `inference.server_url` | Host and port list that expands into VLLM URLs via `create_model_urls`. |
| `inference.is_openai_model` | Flag used by OpenAI-backed examples. |
| `inference.use_openai_embedding` | Enables embedding-backed Twitter variants. |

## Adaptation notes

- Keep the scenario constant when possible and adjust only scale knobs first: `num_timesteps`, `round_post_num`, `activate_prob`, and the sample size of the input data.
- For Reddit runs, remember the README heuristic: one timestep is roughly two hours in the simulated world, and controllable posts need enough room in the recommendation cache to be seen.
- If the task is only to understand a legacy recipe, do not rerun the simulation. Summarize the config shape, the likely outputs, and the safety blockers instead.
- If the task asks about a DB that already exists, inspect it through the safe DB summary route before inventing a custom analysis script.
