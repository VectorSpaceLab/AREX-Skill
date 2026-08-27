# Automations and Memory Troubleshooting

Use this guide to identify whether a failure is in API validation, scheduling, scheduler leadership, chat execution, email notification, memory settings, or memory scoping.

## Automation Create or Edit Is Rejected

Symptoms:

- `400 A query and crontime is required`
- `400 A query, subject and crontime is required`
- `400 Invalid crontime`
- `400 Minute level recurrence is unsupported...`
- `400 Recurrence of every X minutes is unsupported...`

Checks:

1. Ensure required query params are present: create needs `q` and `crontime`; edit needs `automation_id`, `q`, `subject`, and `crontime`.
2. Validate the cron with `scripts/validate_cron.py '0 9 * * 1'` before sending it to the API.
3. Use exactly five useful cron fields. The API truncates extra fields to the first five; seconds or year fields may be silently discarded.
4. Replace Quartz-style `?` with `*`, or let the API normalize it.
5. Keep the first field numeric. Khoj API routes reject `*`, `*/5`, comma lists, ranges, and named values in the minute field to avoid minute-level recurrence.
6. Pass a valid timezone such as `UTC`, `America/New_York`, or `Asia/Kolkata`, especially on edit.

## `/automated_task` Prefix Issues

Create and edit add `/automated_task ` to the inferred execution query unless it already starts with that exact prefix. If an automation appears to ignore automation-specific chat behavior:

- Inspect returned `query_to_run` metadata; it should usually start with `/automated_task`.
- Check whether the scheduling actor already returned a slash command or whitespace that changed prefix detection.
- Do not add another slash command before `/automated_task`; chat command routing treats the first recognized prefix as significant.
- When presenting the task to users, remove the prefix only for display. Runtime metadata should preserve it.

## Duplicate Automation or Unexpected `500`

A duplicate automation can collide because job ids are deterministic for the current user, normalized execution query, and normalized cron. If create returns `500 Unable to create automation. Ensure the automation doesn't already exist.`:

- List existing automations with `GET /api/automation` and compare normalized `query_to_run` plus `crontime`.
- Remember that six-field cron input may have been truncated before the id hash was computed.
- Remember that `?` and `*` become equivalent after normalization.
- Change either the execution query, the schedule, or delete the old automation before recreating.

## Manual Trigger Does Not Show a Result

`POST /api/automation/trigger` only starts a thread and returns `Automation triggered`. It does not wait for chat execution or email delivery.

If there is no visible result:

- Confirm the id belongs to the current user and still exists; invalid ids return `403 Invalid automation`.
- Check server logs for chat API failures, redirect handling, missing bearer tokens, or notification-decision failures.
- Confirm email provider setup if the expected output is an email.
- Confirm the stored conversation still exists; scheduled execution deletes the automation and exits when its `conversation_id` is missing.
- Confirm the job did not run successfully within the last six hours; duplicate-run protection skips recent executions.

## Scheduler Leader Conflicts

Symptoms:

- Jobs are created but never execute.
- Multiple workers log scheduler startup, but only one executes jobs.
- A worker says the schedule leader is already running or running elsewhere.

Checks:

1. This is expected in multi-worker deployments: only the process holding the `schedule_leader` lock runs jobs.
2. Check whether the active leader is alive. A stale lock lasts up to twelve hours unless the wakeup path clears it after expiry.
3. Non-leader workers start their scheduler paused; they can add/edit/delete jobs but should not execute them.
4. A current leader should periodically wake the scheduler. If no process holds a valid lock, the wakeup path should acquire one and resume scheduling.
5. Do not fix this by enabling every worker to run jobs; that risks duplicate automations. Fix lock staleness, startup/shutdown, or database connectivity instead.

## Invalid or Missing Conversation Id

Scheduled chat validates the stored `conversation_id` before posting to chat. If the conversation is missing, Khoj deletes the automation and exits.

Debug steps:

- Inspect automation metadata for `conversation_id` if you are looking at internal job metadata.
- Older automations without a conversation id get one during edit.
- If a user reports a disappearing automation after a trigger or scheduled time, check whether the conversation row was deleted.
- Prefer editing the automation to regenerate missing conversation metadata rather than manually patching scheduler job state.

## Memory Not Found

`DELETE /api/memories/{memory_id}` and `PUT /api/memories/{memory_id}` return `404 {"error": "Memory not found"}` when the memory id does not belong to the authenticated user or no longer exists.

Common causes:

- The client is using a memory id from another user.
- The memory was already deleted.
- The memory was updated; update deletes the old row and creates a new row with a different id.
- The client cached ids from `GET /api/memories` and did not refresh after an update.

## Memory Update Changes Id

This is expected. The update route deletes the old row and creates a new memory through the adapter so embeddings are regenerated for the new raw text. Downstream code must use the returned `{id, raw}` as the new canonical memory.

## Memory Is Disabled

If chat does not create or use memories:

- Check server memory mode. `disabled` overrides every user setting.
- Under `enabled_default_off`, users must explicitly opt in.
- Under `enabled_default_on`, memory is on unless the user opted out.
- With no server settings row, memory defaults on unless the user's preference is false.
- Check user configuration output for both `enable_memory` and `server_memory_mode`.

## Custom Agent Cannot See a Memory

This is usually scoping, not data loss.

- Default Khoj agent and `agent=None` can pull all memories for a user.
- A custom non-default agent can pull/search only memories scoped to that exact agent.
- Memories saved by the default agent are stored unscoped and are not visible to custom agents through custom-agent pull/search.
- Memories saved by one custom agent are not visible to another custom agent.
- Users remain isolated regardless of agent scope.

If the desired behavior is shared memory across agents, route through default-agent memory behavior or change the scoping logic deliberately; do not treat current custom-agent isolation as a bug.

## Memory Exists But Search Misses It

Separate direct API listing from adapter search:

- `GET /api/memories` lists all rows for the user and ignores agent scope.
- `pull_memories` applies user/agent scope, a default seven-day update window, newest-first ordering, and a default limit of 10.
- `search_memories` applies user/agent scope and vector-distance thresholding.
- If a row appears in the API but not chat context, check agent scope, recency, limit, embeddings, and search model threshold.

Use `search-retrieval` for embedding model or vector threshold issues after ownership and scope are confirmed.
