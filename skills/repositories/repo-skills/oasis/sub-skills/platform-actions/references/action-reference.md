# ActionType and ManualAction Reference

Use this file to choose an OASIS `ActionType` and the exact `ManualAction.action_args` keys. `ManualAction` uses the shape:

```python
ManualAction(action_type=ActionType.CREATE_POST, action_args={"content": "..."})
```

The enum member is safest; the platform dispatches on the lowercase `.value` string.

## ActionType enum values

| Enum member | `.value` | Scope note |
| --- | --- | --- |
| `ActionType.EXIT` | `"exit"` | Infrastructure: stop the platform loop. |
| `ActionType.REFRESH` | `"refresh"` | Fetch recommended/visible posts. |
| `ActionType.SEARCH_USER` | `"search_user"` | Search users by text/id fields. |
| `ActionType.SEARCH_POSTS` | `"search_posts"` | Search posts by text/id fields. |
| `ActionType.CREATE_POST` | `"create_post"` | Create an original post. |
| `ActionType.LIKE_POST` | `"like_post"` | Like/upvote a post. |
| `ActionType.UNLIKE_POST` | `"unlike_post"` | Remove an existing post like. |
| `ActionType.DISLIKE_POST` | `"dislike_post"` | Dislike/downvote a post. |
| `ActionType.UNDO_DISLIKE_POST` | `"undo_dislike_post"` | Remove an existing post dislike. |
| `ActionType.REPORT_POST` | `"report_post"` | Report a post with a reason. |
| `ActionType.FOLLOW` | `"follow"` | Follow another user. |
| `ActionType.UNFOLLOW` | `"unfollow"` | Remove a follow relation. |
| `ActionType.MUTE` | `"mute"` | Mute another user. |
| `ActionType.UNMUTE` | `"unmute"` | Remove a mute relation. |
| `ActionType.TREND` | `"trend"` | Return top trending posts. |
| `ActionType.SIGNUP` | `"sign_up"` | Infrastructure/profile setup; route detailed use to `agent-profiles`. |
| `ActionType.REPOST` | `"repost"` | Repost/reshare content without quote text. |
| `ActionType.QUOTE_POST` | `"quote_post"` | Repost with quote text. |
| `ActionType.UPDATE_REC_TABLE` | `"update_rec_table"` | Infrastructure: rebuild `rec`; `env.step()` calls it automatically. |
| `ActionType.CREATE_COMMENT` | `"create_comment"` | Comment on a post. |
| `ActionType.LIKE_COMMENT` | `"like_comment"` | Like a comment. |
| `ActionType.UNLIKE_COMMENT` | `"unlike_comment"` | Remove a comment like. |
| `ActionType.DISLIKE_COMMENT` | `"dislike_comment"` | Dislike a comment. |
| `ActionType.UNDO_DISLIKE_COMMENT` | `"undo_dislike_comment"` | Remove a comment dislike. |
| `ActionType.DO_NOTHING` | `"do_nothing"` | No-op that still records a trace. |
| `ActionType.PURCHASE_PRODUCT` | `"purchase_product"` | Increment product sales. |
| `ActionType.INTERVIEW` | `"interview"` | Manual/harness interview; usually keep out of LLM action sets. |
| `ActionType.JOIN_GROUP` | `"join_group"` | Join an existing chat group. |
| `ActionType.LEAVE_GROUP` | `"leave_group"` | Leave a joined chat group. |
| `ActionType.SEND_TO_GROUP` | `"send_to_group"` | Send a message to a joined group. |
| `ActionType.CREATE_GROUP` | `"create_group"` | Create a group and auto-join creator. |
| `ActionType.LISTEN_FROM_GROUP` | `"listen_from_group"` | Read group catalog, joined groups, and messages. |

## Default action presets

`ActionType.get_default_twitter_actions()` returns these enum members, in order:

```python
[
    ActionType.CREATE_POST,
    ActionType.LIKE_POST,
    ActionType.REPOST,
    ActionType.FOLLOW,
    ActionType.DO_NOTHING,
    ActionType.QUOTE_POST,
]
```

`ActionType.get_default_reddit_actions()` returns these enum members, in order:

```python
[
    ActionType.LIKE_POST,
    ActionType.DISLIKE_POST,
    ActionType.CREATE_POST,
    ActionType.CREATE_COMMENT,
    ActionType.LIKE_COMMENT,
    ActionType.DISLIKE_COMMENT,
    ActionType.SEARCH_POSTS,
    ActionType.SEARCH_USER,
    ActionType.TREND,
    ActionType.REFRESH,
    ActionType.DO_NOTHING,
    ActionType.FOLLOW,
    ActionType.MUTE,
]
```

These presets are action availability lists for agents, not full platform presets. Platform constructor defaults and `DefaultPlatformType` presets are in [platform-and-recsys.md](platform-and-recsys.md).

## ManualAction argument map

| Action | `action_args` keys | Main DB effect and trace behavior |
| --- | --- | --- |
| `CREATE_POST` | `{"content": str}` | Inserts an original `post`; trace `info` includes `content` and `post_id`. |
| `LIKE_POST` | `{"post_id": int}` | Inserts `like`, increments `post.num_likes`, writes trace. Repost ids resolve to the root post for the count. |
| `UNLIKE_POST` | `{"post_id": int}` | Deletes matching `like`, decrements `post.num_likes`, writes trace. Repost ids resolve to the root post. |
| `DISLIKE_POST` | `{"post_id": int}` | Inserts `dislike`, increments `post.num_dislikes`, writes trace. Repost ids resolve to the root post. |
| `UNDO_DISLIKE_POST` | `{"post_id": int}` | Deletes matching `dislike`, decrements `post.num_dislikes`, writes trace. Repost ids resolve to the root post. |
| `REPOST` | `{"post_id": int}` | Inserts a new `post` row with `original_post_id`, increments root `num_shares`, writes trace with `reposted_id` and `new_post_id`. Duplicate reposts of the same root by the same user are rejected. |
| `QUOTE_POST` | `{"post_id": int, "quote_content": str}` | Inserts a quote `post`, increments root `num_shares`, writes trace with `quoted_id` and `new_post_id`. Multiple quotes are allowed because quote text can differ. |
| `CREATE_COMMENT` | `{"post_id": int, "content": str}` | Inserts `comment`, writes trace with `content` and `comment_id`. Repost ids resolve to the root post. |
| `LIKE_COMMENT` | `{"comment_id": int}` | Inserts `comment_like`, increments `comment.num_likes`, writes trace. |
| `UNLIKE_COMMENT` | `{"comment_id": int}` | Deletes matching `comment_like`, decrements `comment.num_likes`, writes trace. |
| `DISLIKE_COMMENT` | `{"comment_id": int}` | Inserts `comment_dislike`, increments `comment.num_dislikes`, writes trace. |
| `UNDO_DISLIKE_COMMENT` | `{"comment_id": int}` | Deletes matching `comment_dislike`, decrements `comment.num_dislikes`, writes trace. |
| `REPORT_POST` | `{"post_id": int, "report_reason": str}` | Inserts `report`, increments `post.num_reports`, writes trace with `post_id` and `report_id`. Duplicate reports by the same user for the same `post_id` are rejected. |
| `FOLLOW` | `{"followee_id": int}` | Inserts `follow`, increments follower/followee counters in `user`, writes trace. |
| `UNFOLLOW` | `{"followee_id": int}` | Deletes `follow`, decrements follower/followee counters in `user`, writes trace. |
| `MUTE` | `{"mutee_id": int}` | Inserts `mute`, writes trace. |
| `UNMUTE` | `{"mutee_id": int}` | Deletes `mute`, writes trace. |
| `SEARCH_POSTS` | `{"query": str}` | Searches `post.content`, `post_id`, and `user_id`; writes trace with `query`. |
| `SEARCH_USER` | `{"query": str}` | Searches `user.user_name`, `name`, `bio`, and `user_id`; writes trace with `query`. |
| `TREND` | `{}` | Returns top posts from a recent window, ordered by likes; writes trace with returned posts. |
| `REFRESH` | `{}` | Reads `rec`; non-Reddit modes also include followed-user posts; writes trace with returned posts. |
| `DO_NOTHING` | `{}` | Writes a trace row with empty `info`; returns `{"success": True}`. |
| `PURCHASE_PRODUCT` | `{"product_name": str, "purchase_num": int}` | Looks up `product`, increments `sales`, writes trace. A product row must already exist. |
| `INTERVIEW` | `{"prompt": str}` | In `env.step()`, the environment asks the agent and records `prompt`, generated `response`, and `interview_id` in `trace`. Use manually unless you intentionally expose it to LLM tool choice. |
| `CREATE_GROUP` | `{"group_name": str}` | Inserts `chat_group`, inserts creator in `group_members`, writes trace. |
| `JOIN_GROUP` | `{"group_id": int}` | Inserts `group_members`, writes trace. Fails if the group does not exist or the user is already a member. |
| `LEAVE_GROUP` | `{"group_id": int}` | Deletes `group_members`, writes trace. Fails if the user is not a member. |
| `SEND_TO_GROUP` | `{"group_id": int, "message": str}` | Requires membership, inserts `group_messages`, writes trace, returns `message_id` and the other members in `to`. |
| `LISTEN_FROM_GROUP` | `{}` | Reads all groups, joined groups, and messages; does not write a trace row. |

## Infrastructure actions

- `SIGNUP` creates user rows during agent/profile setup. Do not use this sub-skill for profile-generation details.
- `UPDATE_REC_TABLE` is normally called by `env.step()` before executing the step's actions. Direct platform harnesses may send it through the platform channel or call `await platform.update_rec_table()`.
- `EXIT` closes the platform loop and database connection. Full lifecycle handling belongs to `simulation-workflows`.
