# Database and traces

OASIS stores platform state in SQLite. Use this reference when a task needs to inspect an output database, map an action to a table, or understand a trace payload.

## Database lifecycle

- `Platform(db_path=...)` creates the SQLite database and executes all bundled schema scripts.
- `env.reset()` signs up agents and starts the platform loop.
- `env.step(actions)` updates the recommendation table, performs actions concurrently, and records traces for most actions.
- `env.close()` sends `exit`, closes the cursor/connection, and logs the final database path.

Use a fresh `db_path` for deterministic runs. Reusing an existing file preserves existing rows unless the caller removes it first.

## Core tables

| Table | Purpose |
| --- | --- |
| `user` | Users/agents, names, bios, follower/following counters. |
| `post` | Original posts, reposts, quote posts, counts, report count, timestamps. |
| `comment` | Comments on posts with like/dislike counters. |
| `follow` | Directed follow relations. |
| `mute` | Muted user relations. |
| `like` / `dislike` | Post ratings. |
| `comment_like` / `comment_dislike` | Comment ratings. |
| `report` | Post reports and reasons. |
| `trace` | Action log with `user_id`, timestamp, action name, and JSON `info`. |
| `rec` | Recommendation buffer mapping `user_id` to visible/recommended `post_id`s. |
| `product` | Electronic-mall product rows and sales counters. |
| `chat_group` | Group chat metadata. |
| `group_members` | Group membership rows. |
| `group_messages` | Group chat messages. |

## Trace payload patterns

`trace.info` is a JSON string. Common payloads:

| Action | Typical `info` payload |
| --- | --- |
| `sign_up` | `{"name": ..., "user_name": ..., "bio": ...}` |
| `create_post` | `{"content": ..., "post_id": ...}` |
| `repost` | `{"reposted_id": ..., "new_post_id": ...}` |
| `quote_post` | `{"quoted_id": ..., "new_post_id": ..., "quote_content": ...}` |
| `create_comment` | `{"post_id": ..., "content": ..., "comment_id": ...}` |
| `like_post` / `unlike_post` | `{"post_id": ..., "like_id": ...}` |
| `dislike_post` / `undo_dislike_post` | `{"post_id": ..., "dislike_id": ...}` |
| `follow` / `unfollow` | followee-related IDs and row IDs. |
| `refresh` | selected posts, including nested comments and counts or score. |
| `trend` | returned trending posts. |
| `interview` | prompt/response/interview identifier after a manual interview action. |
| `do_nothing` | empty or minimal info. |

Some failures return `{"success": false, "error": ...}` to the caller without inserting the intended business row. Check `trace` and the target table before assuming the action succeeded.

## Post identity rules

The `post` table can contain three logical post types:

- Common/original post: `original_post_id` is `NULL`.
- Repost: `original_post_id` points at the root post and `quote_content` is `NULL`; content can be empty.
- Quote post: `original_post_id` points at the root post and `quote_content` is non-empty.

Like/dislike/comment/share actions often resolve repost ids back to the root post internally. If counts appear on a different row than expected, inspect `original_post_id` and `quote_content` before treating it as data loss.

## Recommendation table

The `rec` table is cleared and refilled by `Platform.update_rec_table()`. `env.step()` calls that method before executing the step's actions. A newly created post usually becomes eligible for recommendation on a later step, not the same step that created it.

For Twitter-like platforms, `refresh` combines recommended posts with followed-user posts. For Reddit-like platforms, recommendations emphasize hot-score ordering.

## Safe DB inspection

Use the bundled helper from this sub-skill:

```bash
python scripts/oasis_db_summary.py --db-path path/to/simulation.db --limit 5
```

The helper only reads the SQLite file. It reports table counts, action counts from `trace`, and recent trace rows. Use it before writing ad-hoc SQL against a production result database.

## SQL snippets

Count trace actions:

```sql
SELECT action, COUNT(*)
FROM trace
GROUP BY action
ORDER BY COUNT(*) DESC, action;
```

Inspect recent actions:

```sql
SELECT user_id, created_at, action, info
FROM trace
ORDER BY rowid DESC
LIMIT 10;
```

Find posts with root/quote information:

```sql
SELECT post_id, user_id, original_post_id, content, quote_content,
       num_likes, num_dislikes, num_shares, num_reports
FROM post
ORDER BY post_id;
```
