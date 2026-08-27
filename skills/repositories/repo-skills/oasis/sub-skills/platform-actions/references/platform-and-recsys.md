# Platform and recommendation systems

Use this reference when a task needs a custom OASIS `Platform`, a non-default recommendation system, a clock/channel setting, or an explanation of why refreshed posts differ between Reddit-like and Twitter-like runs.

## Default platform presets

`oasis.make(agent_graph=..., platform=DefaultPlatformType.REDDIT, database_path=...)` constructs a `Platform` with Reddit-style defaults:

- `recsys_type="reddit"`
- `allow_self_rating=True`
- `show_score=True`
- `max_rec_post_len=100`
- `refresh_rec_post_count=5`

`oasis.make(agent_graph=..., platform=DefaultPlatformType.TWITTER, database_path=...)` constructs a Twitter-like platform with:

- `recsys_type="twhin-bert"`
- `refresh_rec_post_count=2`
- `max_rec_post_len=2`
- `following_post_count=3`

When using a `DefaultPlatformType`, `database_path` is required. When passing a custom `Platform` instance, the environment uses the platform's own database path and channel.

## Custom `Platform` constructor

Current installed signature:

```python
Platform(
    db_path: str,
    channel=None,
    sandbox_clock=None,
    start_time=None,
    show_score=False,
    allow_self_rating=True,
    recsys_type="reddit",
    refresh_rec_post_count=1,
    max_rec_post_len=2,
    following_post_count=3,
    use_openai_embedding=False,
)
```

Common settings:

| Setting | Use |
| --- | --- |
| `db_path` | SQLite database file path. Use a fresh path for repeatable runs. |
| `channel` | Shared async channel between agents and platform. Omit only when constructing directly for tests. |
| `sandbox_clock` | Optional `Clock(k)` for accelerated Reddit timestamps or Twitter time steps. |
| `start_time` | Initial simulated time when clock conversion matters. |
| `show_score` | Shows Reddit-style score (`likes - dislikes`) instead of separate counts in refreshed observations. |
| `allow_self_rating` | If `False`, self-like/self-dislike of posts/comments returns an error. |
| `recsys_type` | `"random"`, `"reddit"`, `"twitter"`, or `"twhin-bert"` via `RecsysType`. |
| `refresh_rec_post_count` | Number of recommended posts returned per refresh. |
| `max_rec_post_len` | Maximum posts retained in each user's recommendation buffer. |
| `following_post_count` | Twitter-like refresh adds top posts from followed users. |
| `use_openai_embedding` | TwHIN path can use OpenAI embeddings instead of local TwHIN vectors; requires credentials. |

## `Channel` and platform loop

A `Platform` consumes actions from a `Channel` and sends results back to agents. `env.reset()` starts `platform.running()` in the background; `env.close()` sends `ActionType.EXIT` and waits for the platform to close its database connection.

If you drive `Platform.running()` directly in a harness, make sure the channel eventually returns an `exit` action. Otherwise the async loop waits forever and the database remains open.

## `Clock`

`Clock(k=1)` records real start time and a Twitter-style integer `time_step`.

- Reddit-style time uses `time_transfer(now, start_time)` and the magnification factor `k`.
- Twitter-style time uses `get_time_step()`; `OasisEnv.step()` increments it after each Twitter step.

## Recommendation system types

| RecsysType | Behavior | Required dependencies and risks |
| --- | --- | --- |
| `RANDOM` / `"random"` | Samples post IDs randomly up to `max_rec_post_len`. | CPU-only and safe for tiny checks. |
| `REDDIT` / `"reddit"` | Uses Reddit hot-score-like ranking from likes, dislikes, and timestamps. | CPU-only and safe for tiny checks. |
| `TWITTER` / `"twitter"` | Personalized text similarity from user bios, posts, and traces. | May load sentence-transformers and torch; can download models if not cached. |
| `TWHIN` / `"twhin-bert"` | Uses TwHIN-BERT-style post vectors plus recency/social signals; default Twitter preset uses this. | Optional model downloads, torch, CUDA acceleration, or OpenAI embedding credentials depending on configuration. |

For a skill or CI smoke, prefer `RANDOM` or `REDDIT`. Treat `TWITTER` and `TWHIN` as optional unless the user explicitly provides model cache/network, provider credentials, and runtime budget.

## `update_rec_table()` timing

`env.step(actions)` calls `await self.platform.update_rec_table()` before it performs the step's actions. That means a post created in the current step will not necessarily appear in `REFRESH` results until a later step. Direct platform tests can call `await platform.update_rec_table()` explicitly.

## OpenAI embeddings and TwHIN

`use_openai_embedding=True` delegates embedding generation to CAMEL's OpenAI embedding wrapper and requires provider credentials. `use_openai_embedding=False` uses local transformer models and may download `Twitter/twhin-bert-base` or a sentence-transformer model if they are not cached. Do not trigger those paths during a small smoke unless the user approved downloads and optional GPU/model time.
