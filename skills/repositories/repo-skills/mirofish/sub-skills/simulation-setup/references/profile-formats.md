# Profile and config formats

MiroFish setup generates two platform profile files plus `simulation_config.json`. Runtime reads these files later; setup API responses may expose a different shape from the saved files, so validate the correct shape for the operation.

## Common `OasisAgentProfile` fields

Profile generation first builds an internal profile object with these fields:

| Field | Type | Meaning |
|---|---|---|
| `user_id` | integer | OASIS agent id. Generated from entity order and starts at 0. |
| `user_name` | string | Internal username generated from entity name plus random suffix. |
| `name` | string | Display name, usually the source entity name. |
| `bio` | string | Short public profile text. Non-string LLM values are coerced to strings. |
| `persona` | string | Long behavior/persona prompt used for agent behavior. Non-string LLM values are coerced to strings. |
| `karma` | integer | Reddit-style activity score. |
| `friend_count`, `follower_count`, `statuses_count` | integers | Twitter-style activity counts for direct API/profile dictionaries. |
| `age` | integer or null | Optional demographic field; saved Reddit file defaults missing values to 30. |
| `gender` | string or null | Expected saved values are `male`, `female`, or `other`. |
| `mbti` | string or null | Saved Reddit file defaults missing values to `ISTJ`. |
| `country` | string or null | Saved Reddit file defaults missing values to `中国`. |
| `profession` | string or null | Optional persona field. |
| `interested_topics` | list of strings | Optional topic interests. |
| `source_entity_uuid`, `source_entity_type` | strings or null | Source graph entity identity. Not included in saved runtime files. |
| `created_at` | string | Date string such as `YYYY-MM-DD`. |

The generator distinguishes individual-like entity types (`student`, `alumni`, `professor`, `person`, `publicfigure`, `expert`, `faculty`, `official`, `journalist`, `activist`) from group/institution-like types (`university`, `governmentagency`, `organization`, `ngo`, `mediaoutlet`, `company`, `institution`, `group`, `community`) when prompting or rule-generating personas.

## Saved Reddit runtime file: `reddit_profiles.json`

Stored file shape is a JSON list. Each item must contain the fields needed by OASIS Reddit graph generation and by MiroFish initial post assignment:

```json
[
  {
    "user_id": 0,
    "username": "alice_123",
    "name": "Alice",
    "bio": "Short public bio, truncated to 150 characters when saved.",
    "persona": "Long persona text used by the agent.",
    "karma": 1500,
    "created_at": "2025-12-01",
    "age": 25,
    "gender": "female",
    "mbti": "INTJ",
    "country": "中国",
    "profession": "Student",
    "interested_topics": ["Education", "Technology"]
  }
]
```

Required saved keys:

- `user_id`
- `username`
- `name`
- `bio`
- `persona`
- `karma`
- `created_at`
- `age`
- `gender`
- `mbti`
- `country`

Optional saved keys:

- `profession`
- `interested_topics`

Saved Reddit defaults and normalization:

- `bio` is truncated to 150 characters.
- missing `karma` becomes 1000.
- missing `age` becomes 30.
- missing `gender` becomes `other`.
- Chinese `男` maps to `male`, `女` maps to `female`, and `机构`/`其他` map to `other`.
- unknown gender strings become `other`.
- missing `mbti` becomes `ISTJ`.
- missing `country` becomes `中国`.

## Saved Twitter runtime file: `twitter_profiles.csv`

Stored Twitter profiles are CSV, not JSON. Header order is significant for the current generator smoke checks:

```csv
user_id,name,username,user_char,description
0,Alice,alice_123,Alice short bio Alice long persona,Alice short bio
```

Saved fields:

| Column | Meaning |
|---|---|
| `user_id` | Sequential zero-based id from row order. |
| `name` | Display/real name. |
| `username` | Generated username. |
| `user_char` | Internal character prompt. It combines `bio` and `persona` when they differ and replaces newlines with spaces. |
| `description` | Public-facing short description from `bio`, with newlines replaced by spaces. |

Do not expect the stored CSV to contain `friend_count`, `follower_count`, or `statuses_count`; those exist on internal/direct API profile dictionaries, not the current saved OASIS Twitter CSV file.

## Direct `/generate-profiles` response formats

`POST /api/simulation/generate-profiles` does not save runtime files. It returns generated profile data in the response:

- `platform: "reddit"` uses profile dictionaries similar to `to_reddit_format()`: `user_id`, `username`, `name`, `bio`, `persona`, `karma`, `created_at`, plus optional demographics/interests if present.
- `platform: "twitter"` returns JSON dictionaries similar to `to_twitter_format()`: `user_id`, `username`, `name`, `bio`, `persona`, `friend_count`, `follower_count`, `statuses_count`, `created_at`, plus optional demographics/interests if present.
- Any other platform string returns the full generic internal dictionary, including `user_name`, source entity fields, and both Reddit/Twitter counters. This is useful for inspection but not a stored runtime file format.

## `simulation_config.json` skeleton

The config generator serializes a `SimulationParameters` object. A complete file has this top-level shape:

```json
{
  "simulation_id": "sim_...",
  "project_id": "proj_...",
  "graph_id": "mirofish_...",
  "simulation_requirement": "What social scenario should be simulated?",
  "time_config": {
    "total_simulation_hours": 72,
    "minutes_per_round": 60,
    "agents_per_hour_min": 1,
    "agents_per_hour_max": 5,
    "peak_hours": [19, 20, 21, 22],
    "peak_activity_multiplier": 1.5,
    "off_peak_hours": [0, 1, 2, 3, 4, 5],
    "off_peak_activity_multiplier": 0.05,
    "morning_hours": [6, 7, 8],
    "morning_activity_multiplier": 0.4,
    "work_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
    "work_activity_multiplier": 0.7
  },
  "agent_configs": [
    {
      "agent_id": 0,
      "entity_uuid": "node_uuid",
      "entity_name": "Alice",
      "entity_type": "Student",
      "activity_level": 0.8,
      "posts_per_hour": 0.6,
      "comments_per_hour": 1.5,
      "active_hours": [8, 9, 10, 11, 12, 13, 18, 19, 20, 21, 22, 23],
      "response_delay_min": 1,
      "response_delay_max": 15,
      "sentiment_bias": 0.0,
      "stance": "neutral",
      "influence_weight": 0.8
    }
  ],
  "event_config": {
    "initial_posts": [
      {"content": "Initial post text", "poster_type": "Student", "poster_agent_id": 0}
    ],
    "scheduled_events": [],
    "hot_topics": ["topic"],
    "narrative_direction": "..."
  },
  "twitter_config": {
    "platform": "twitter",
    "recency_weight": 0.4,
    "popularity_weight": 0.3,
    "relevance_weight": 0.3,
    "viral_threshold": 10,
    "echo_chamber_strength": 0.5
  },
  "reddit_config": {
    "platform": "reddit",
    "recency_weight": 0.3,
    "popularity_weight": 0.4,
    "relevance_weight": 0.3,
    "viral_threshold": 15,
    "echo_chamber_strength": 0.6
  },
  "llm_model": "gpt-4o-mini",
  "llm_base_url": "https://api.openai.com/v1",
  "generated_at": "ISO time",
  "generation_reasoning": "time reasoning | event reasoning | agent/config reasoning"
}
```

### Time defaults and bounds

When LLM time-config generation fails, fallback defaults use China-style activity periods:

- `total_simulation_hours`: 72
- `minutes_per_round`: 60
- `agents_per_hour_min`: `max(1, num_entities // 15)`
- `agents_per_hour_max`: `max(5, num_entities // 5)`
- peak hours: `[19, 20, 21, 22]`
- off-peak hours: `[0, 1, 2, 3, 4, 5]`
- morning hours: `[6, 7, 8]`
- work hours: `[9, 10, 11, 12, 13, 14, 15, 16, 17, 18]`

The parser corrects per-hour agent activation values that exceed total agent count and ensures min/max are ordered.

### Agent config defaults by entity type

If LLM per-agent config generation fails, rule-based defaults are used:

- `University`, `GovernmentAgency`, `NGO`: low activity, work hours, slow response, high influence.
- `MediaOutlet`: medium activity, broad active hours, quick response, high influence.
- `Professor`, `Expert`, `Official`: medium activity, work/evening hours, medium-high influence.
- `Student`: high activity, morning/evening hours, quick response, lower influence.
- `Alumni`: medium-high activity, lunch/evening hours.
- other/person-like types: daytime/evening activity, neutral stance.

`stance` values should be one of `supportive`, `opposing`, `neutral`, or `observer`.

### Initial post assignment

The LLM event step proposes `initial_posts` with `content` and `poster_type`. The generator maps each `poster_type` to an existing `agent_id` by exact lowercased entity type, then by aliases such as:

- `official` -> `official`, `university`, `governmentagency`, `government`
- `mediaoutlet` -> `mediaoutlet`, `media`
- `student` -> `student`, `person`
- `professor` -> `professor`, `expert`, `teacher`
- `organization` -> `organization`, `ngo`, `company`, `group`

If no type match exists, it chooses the highest-influence agent. Validate `poster_agent_id` after generation because runtime initial actions depend on it.

## Platform defaults

Creation defaults enable both Twitter and Reddit. When both are enabled, completed-profile reads default to Reddit for backward compatibility. When only Twitter is enabled, profile reads default to Twitter; otherwise they default to Reddit.

Platform configs are included only for enabled platforms during config generation. Stored profile files are written only for enabled platforms, but the current prepared-artifact reuse check expects both `reddit_profiles.json` and `twitter_profiles.csv`; see troubleshooting if single-platform reuse appears inconsistent.

## Quick validation checklist

- `reddit_profiles.json` parses as a list and every object has required Reddit keys.
- `twitter_profiles.csv` has header `user_id,name,username,user_char,description` and at least one data row.
- Profile `user_id` values and config `agent_id` values are contiguous from zero unless there is an intentional custom transformation.
- `len(reddit_profiles)` or CSV row count equals `len(simulation_config.agent_configs)` for enabled platforms.
- All `event_config.initial_posts[*].poster_agent_id` values exist in `agent_configs`.
- `twitter_config` and/or `reddit_config` match enabled platform flags.
- `time_config.minutes_per_round` is positive and produces positive total rounds.
