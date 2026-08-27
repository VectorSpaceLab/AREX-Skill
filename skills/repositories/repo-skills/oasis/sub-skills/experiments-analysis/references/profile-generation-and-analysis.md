# Profile generation and analysis

This reference combines the legacy user-generation notes with the analysis workflows that consume the resulting simulation artifacts.

## User profile formats

| Platform | Legacy shape | Important fields | Notes |
| --- | --- | --- | --- |
| Reddit | JSON array | `realname`, `username`, `bio`, `persona`, `age`, `gender`, `mbti`, `country` | `agent_id` is derived from the order of the JSON file. Generator scripts may also append profession and topic fields. |
| Twitter | CSV | `user_id`, `name`, `username`, `user_char`, `description` | `agent_id` is derived from row order. Legacy generation may later add `following_agentid_list`, `activity_level`, `activity_level_frequency`, `previous_tweets`, and `tweets_id`. |

### Field mapping reminders
- Reddit generation often starts with a human-readable `bio` and a richer `persona`.
- Twitter generation often uses `description` and `user_char` as the two persona-style text fields.
- Keep the identity text consistent with the intended behavior of the simulation; mismatched bios are a common source of confusing analysis later.

## Legacy generation workflows

### Reddit user generation
- `generator/reddit/user_generate.py` samples gender, age, MBTI, country, and profession, then uses an OpenAI chat model to pick topics and synthesize a profile.
- The script writes JSON user profiles with the fields used by Reddit experiments.
- It is credential- and cost-sensitive because it fans out many API calls through a thread pool.
- Use it as a pattern for format and field expectations, not as an automatic execution target.

### Twitter user generation
- `generator/twitter/gen.py` and `generator/twitter/network.py` enrich crawled Twitter-like user data.
- The legacy flow expects source data that is not bundled as a guaranteed runnable dataset, so treat it as reference-only unless the required CSV inputs are known to exist.
- The downstream network script renames fields into the CSV shape used by Twitter simulations and adds the activity/following metadata used by the simulator.

## Analysis workflows

### Reddit score analysis
- Legacy files: `visualization/reddit_simulation_align_with_human/code/analysis_all.py` and `analysis_score.py`.
- Input pattern: a completed experiment database plus the matching experiment-info JSON, usually sharing the same base name.
- Analysis shape: load comment IDs from the experiment-info file, query comment scores from the `comment` table, compute mean and 95% confidence intervals, and save a bar plot.
- Best fit: align-with-human experiments where you want a final score comparison across treatment groups.
- Safe triage: if the DB or JSON is missing, first confirm the simulation actually produced both files. If they exist, use the DB summary route before writing new analysis code.

### Reddit counterfactual analysis
- Legacy file: `visualization/reddit_simulation_counterfactual/code/analysis_couterfact.py`.
- Input pattern: three SQLite DB files for up, control, and down treatments.
- Analysis shape: read the `trace` table for comment-creation events, look up the linked comment and post content, score the comment's agreement with the counterfactual content, and plot mean score by timestep with confidence intervals.
- Dependencies: this workflow uses `aiohttp`, `matplotlib`, `numpy`, `scipy`, and an OpenAI API key.
- Safe triage: if the user wants only a structural review, do not call the API. Summarize how the scoring pipeline works and where the data comes from instead.

### Dynamic follow network
- Legacy files: `visualization/dynamic_follow_network/code/vis_neo4j_reddit.py` and `vis_neo4j_twitter.py`.
- Input pattern: a generated SQLite database with user and follow activity.
- Analysis shape: export user nodes and follow edges into Neo4j, then inspect the resulting graph in the Neo4j console.
- Dependencies: `neo4j` plus valid Neo4j credentials and a reachable service.
- Safe triage: before custom graph work, inspect the SQLite database summary and first rows through the safe DB summary route so you know which tables and fields are actually present.

## Interpretation checklist

1. Confirm whether the request is about generating profiles, analyzing results, or visualizing graphs.
2. Confirm the expected artifact names and whether they share a base name (`db`, `json`, `png`, or graph export files).
3. Check whether the analysis can be done locally from existing outputs, or whether it would require a provider API, Neo4j, or a large model server.
4. If the requested output is a plot, decide whether it should summarize final scores, time-step trends, or network structure.
5. If the requested output is a profile format conversion, preserve the semantic fields first and the file layout second.
