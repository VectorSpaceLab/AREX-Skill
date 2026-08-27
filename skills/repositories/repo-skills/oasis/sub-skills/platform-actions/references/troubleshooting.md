# Platform Actions Troubleshooting

Use this guide before changing action arguments or rewriting simulation code. For schema and trace inspection, also use [database-and-traces.md](database-and-traces.md) and the bundled [`oasis_db_summary.py`](../scripts/oasis_db_summary.py) script.

## Repost duplicate and missing-post errors

Symptoms:

- `{"success": False, "error": "Repost record already exists."}`
- `{"success": False, "error": "Post not found."}`

Likely causes and fixes:

- `repost` rejects duplicate reposts by the same user for the same root post. If a user reposted the original post, reposting a visible repost of that original still counts as a duplicate.
- A `post_id` that does not exist in `post` returns `Post not found.` Confirm the id was created before the action and that you are using the current DB file.
- `repost`, `quote_post`, `like_post`, `unlike_post`, `dislike_post`, `undo_dislike_post`, and `create_comment` accept visible post ids, but repost/quote ids may be resolved to the root post for mutation. This is expected.
- `quote_post` intentionally allows repeated quotes because `quote_content` can differ. If quote behavior looks duplicated, inspect `post.original_post_id`, `post.quote_content`, and `trace.action='quote_post'`.

## Users not signed up or missing user rows

Most platform actions assume the acting agent already has a row in `user`. If an action behaves oddly, inserts rows with unexpected ids, or returns a missing-user-style error, confirm:

```sql
SELECT user_id, agent_id, user_name FROM user ORDER BY user_id;
```

Run the agent/profile setup flow before platform actions. Detailed profile and sign-up construction belongs to `agent-profiles`, not this sub-skill.

## Self-rating blocked

Symptoms:

- `Users are not allowed to like/dislike their own posts.`
- `Users are not allowed to like/dislike their own comments.`

Cause: the platform was constructed with `allow_self_rating=False`.

Fixes:

- Use a different agent/user to rate the post or comment.
- Or construct the platform with `allow_self_rating=True` if self-ratings are valid for the experiment.
- Confirm whether the `post_id` or `comment_id` resolves to content authored by the same `agent_id`.

## Like/dislike/comment-rating duplicate or undo errors

Common exact errors:

- `Like record already exists.` / `Like record does not exist.`
- `Dislike record already exists.` / `Dislike record does not exist.`
- `Comment like record already exists.` / `Comment like record does not exist.`
- `Comment dislike record already exists.` / `Comment dislike record does not exist.`

Fixes:

- For undo actions, verify the matching like/dislike row exists for the same user and target id.
- For repeated like/dislike actions, inspect the corresponding reaction table before retrying.
- Remember that post ratings on a repost id may be stored against the root post id.

## Report workflow surprises

Symptoms:

- `Report record already exists.`
- A post was reported but no warning appears in returned content.

Fixes:

- Reports are unique per acting user and `post_id`. Use a different reporter or avoid repeated reports from the same user.
- The visible warning is added only after the report count reaches the platform threshold. The default threshold is `2` reports.
- Inspect both `report` rows and `post.num_reports` when diagnosing report state.

## Group membership before `send_to_group`

Symptoms:

- `User is not a member of this group.`
- `Group does not exist.`
- `User is already in the group.`

Fixes:

- `create_group` inserts the creator into `group_members` automatically.
- Other agents must run `join_group` before `send_to_group`.
- `send_to_group` writes to `group_messages` only after membership succeeds and returns the other member ids in `to`.
- `listen_from_group` is the safe read-only action for discovering available groups, joined groups, and messages.

## Interview should usually be manual

`INTERVIEW` exists as an action, but most runs should not include it in LLM `available_actions`. If exposed to the LLM, the model may choose interviews as an ordinary social action.

Preferred pattern:

```python
ManualAction(
    action_type=ActionType.INTERVIEW,
    action_args={"prompt": "What do you think about ...?"},
)
```

When driven through the environment, the trace stores the prompt and the generated response. Use DB traces to inspect completed interviews.

## Product purchase errors

Symptom: `No such product.`

Fix: ensure `product` contains the desired `product_name` before `purchase_product`. Then use:

```python
ManualAction(
    action_type=ActionType.PURCHASE_PRODUCT,
    action_args={"product_name": "...", "purchase_num": 1},
)
```

## Rec table empty until update

Symptoms:

- `refresh()` returns no posts despite `post` rows existing.
- The `rec` table has zero rows.

Fixes:

- Call `await platform.update_rec_table()` directly in a platform-level harness, or run `await env.step(actions)`, which updates the recommendation table before actions.
- Confirm the chosen `recsys_type`; model-dependent recommenders can fail before repopulating `rec`.
- Use the summary script to compare `post`, `user`, `rec`, and `trace` counts.

## Personalized/TwHIN model downloads and GPU caveats

Symptoms:

- First recommendation update stalls or fails on model download.
- `ModuleNotFoundError` for model libraries.
- GPU memory pressure or very slow CPU recommendations.

Fixes:

- Use `RecsysType.REDDIT` or `RecsysType.RANDOM` for dependency-light diagnostics.
- For `RecsysType.TWITTER`, make sure the sentence-transformer dependency and the personalized model cache are available.
- For `RecsysType.TWHIN`, make sure the TwHIN tokenizer/model can be loaded. It uses CUDA when available and CPU otherwise.
- For repeated isolated recsys tests, reset recsys module globals between cases to avoid cached state carrying over.

## OpenAI embedding credentials

When `use_openai_embedding=True`, TwHIN vector generation switches to the OpenAI embedding path. If credentials are missing or invalid, recommendation updates can fail before `rec` is repopulated.

Fixes:

- Configure the OpenAI credentials expected by the embedding backend before enabling this flag.
- Leave `use_openai_embedding=False` when you intend to use local TwHIN embeddings.
- Do not treat an OpenAI embedding failure as a database bug; inspect recommender logs and `rec` row counts separately.

## SQLite DB lock, stale path, or wrong DB file

Symptoms:

- `database is locked`
- The expected tables or traces are missing.
- A script reports that the DB path does not exist.

Fixes:

- Confirm the same `db_path` is used by the platform, environment, and diagnostic command. If `OASIS_DB_PATH` is set, ensure it points to the intended file.
- Stop or close previous environment/platform processes before deleting or replacing the DB.
- Prefer read-only inspection with `python scripts/oasis_db_summary.py --db-path ...`.
- If a crashed run left stale SQLite sidecar files or a partial DB, move them aside and rerun with a fresh DB path rather than mixing old traces with a new simulation.
