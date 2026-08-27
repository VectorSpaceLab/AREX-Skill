# Profile data formats

The generators assign `agent_id` by file order starting at `0`. Do not store `agent_id` inside the source profile file.

## Reddit JSON

`generate_reddit_agent_graph(profile_path, ...)` expects a JSON array of profile objects.
The built-in generator maps each record to a `SocialAgent` and copies the Reddit-facing details into `UserInfo`.

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `realname` | Yes | string | Canonical source field for the person's real name. Kept for completeness. |
| `username` | Yes | string | Used as the agent display name. |
| `bio` | Yes | string | Used as the agent description. |
| `persona` | Yes | string | Stored in the profile payload as the main Reddit persona text. |
| `age` | Yes | integer-like | Must be a valid non-negative integer value. |
| `gender` | Yes | string | Injected into the default Reddit prompt. |
| `mbti` | Yes | string | Injected into the default Reddit prompt. |
| `country` | Yes | string | Injected into the default Reddit prompt. |

Generated profile mapping:

- `UserInfo.name` ← `username`
- `UserInfo.description` ← `bio`
- `UserInfo.recsys_type` ← `"reddit"`
- `profile["other_info"]["user_profile"]` ← `persona`
- `profile["other_info"]["mbti"]` ← `mbti`
- `profile["other_info"]["gender"]` ← `gender`
- `profile["other_info"]["age"]` ← `age`
- `profile["other_info"]["country"]` ← `country`

Extra JSON keys are allowed, but custom prompts only work with keys that actually exist in `UserInfo.profile`.

### Minimal valid record

```json
{
  "realname": "James Miller",
  "username": "millerhospitality",
  "bio": "Passionate about hospitality and tourism.",
  "persona": "James is a thoughtful hospitality professional.",
  "age": 40,
  "gender": "male",
  "mbti": "ESTJ",
  "country": "UK"
}
```

## Twitter CSV

`generate_twitter_agent_graph(profile_path, ...)` expects a CSV file with one agent per row.
The canonical dataset may contain extra simulation columns, but these four profile columns are required.

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `name` | Yes | string | Canonical source field for the person's real name. Kept for compatibility. |
| `username` | Yes | string | Used as the agent display name. |
| `user_char` | Yes | string | Stored as the profile text shown in the default Twitter prompt. |
| `description` | Yes | string | Used as the agent description. |

Generated profile mapping:

- `UserInfo.name` ← `username`
- `UserInfo.description` ← `description`
- `UserInfo.recsys_type` ← `"twitter"`
- `profile["other_info"]["user_profile"]` ← `user_char`

Extra CSV columns such as platform metadata, follower lists, or previous posts are allowed.
The profile validator ignores those extra columns as long as the required four columns are present.

Some legacy datasets contain blank `user_char` or `description` cells. The generator can read those rows, but high-quality simulations should fill or filter blanks before creating agents so default prompts do not receive empty or `NaN`-like identities.

### Minimal valid header and row

```csv
name,username,user_char,description
Ari,ari_dev,Builder and tinkerer,Builder and tinkerer
```

## Validation checklist

- The source file contains at least one profile row.
- Required fields are present and non-empty.
- Reddit `age` is integer-like.
- Extra fields are only used when you intentionally reference them in a custom prompt.
- `agent_id` comes from row order, so keep the file ordered the way you want the agents created.
