# Automation API

Khoj mounts the automation router at `/api/automation`. All routes require an authenticated user and operate only on job ids prefixed for that user's UUID.

## Endpoint Summary

| Method and path | Purpose | Required inputs | Success response |
| --- | --- | --- | --- |
| `GET /api/automation` | List active automations owned by the current user. | Authentication. | JSON list of automation metadata. |
| `POST /api/automation` | Create an automation from a natural-language scheduling request. | Query params `q` and `crontime`. Optional `subject`, `timezone`, `city`, `region`, `country`. | JSON metadata for the created automation. |
| `PUT /api/automation` | Edit an existing automation. | Query params `automation_id`, `q`, `subject`, and `crontime`. Optional `timezone`, `city`, `region`, `country`. | JSON metadata for the edited automation. |
| `DELETE /api/automation` | Delete an existing automation. | Query param `automation_id`. | Deleted automation metadata as JSON, or `204` if the id is invalid/missing. |
| `POST /api/automation/trigger` | Manually trigger an existing automation. | Query param `automation_id`. | Plain text `Automation triggered`. |

## Create Behavior

`POST /api/automation` validates `q` and `crontime`, asks the chat scheduling actor to infer the concrete query-to-run and subject, creates a conversation titled `Automation: <subject>`, and schedules an APScheduler job.

Important details:

- `q` is the user's original scheduling request and becomes `scheduling_request` in job metadata.
- The scheduling actor returns a crontab string, execution query, and generated subject; an explicit `subject` query parameter overrides the generated subject.
- The execution query is stripped and prefixed with `/automated_task ` unless it already starts with `/automated_task`.
- The crontab is stripped, truncated to the first five fields when more fields are supplied, and has `?` replaced with `*` before scheduling.
- The first cron field must be numeric after normalization. Expressions such as `*/5 * * * *` or `* * * * *` are rejected by the API because minute-level recurrence is unsupported.
- The schedule is built with `CronTrigger.from_crontab(crontime, user_timezone)` and job jitter is set to 60 seconds.
- If `timezone` is invalid in the synchronous scheduling path, scheduling falls back to UTC and logs a warning.
- The job id is deterministic for a user plus normalized execution query plus normalized cron: `automation_<user_uuid>_<md5(query_to_run + '_' + crontime)>`.
- A duplicate automation with the same normalized execution query and cron usually collides on job id and surfaces as `500 Unable to create automation. Ensure the automation doesn't already exist.`

## Edit Behavior

`PUT /api/automation` requires a valid user-owned `automation_id`, non-empty `q`, non-empty `subject`, and valid `crontime`.

Editing does the following:

- Re-runs the scheduling actor for the new `q` to infer the updated execution query.
- Reapplies `/automated_task` prefixing and cron normalization.
- Rejects non-numeric minute fields with `400 Recurrence of every X minutes is unsupported. Please create a less frequent schedule.`
- Loads the existing job metadata, updates `scheduling_request`, `query_to_run`, `subject`, and `crontime`, and preserves the existing `conversation_id` when present.
- Creates a new conversation titled `Automation: <subject>` only if older metadata lacks a `conversation_id`.
- Modifies the APScheduler job kwargs to pass the new query, subject, original scheduling request, user, calling URL, and conversation id.
- Builds a new `CronTrigger` with the supplied timezone and reschedules the job only when the trigger changed.

Be careful: the edit path directly calls timezone parsing for `timezone`; clients should pass a valid timezone such as `UTC` or an IANA timezone name.

## Delete and Manual Trigger

Deletion validates that the job id belongs to the current user and still exists in the scheduler. A valid delete returns the metadata for the removed job; an invalid id returns `204` with no body.

Manual trigger validates the same ownership and existence checks, then starts the scheduled job function in a new Python thread using the job's stored args and kwargs. The API returns immediately after starting the thread and does not wait for chat execution, email delivery, or failure reporting. Invalid trigger ids return `403 Invalid automation`.

## Response Metadata

Automation metadata includes:

- `id`: APScheduler job id with the current user's UUID embedded.
- `subject`: email/task subject stored in job metadata.
- `query_to_run`: normalized execution query, usually prefixed with `/automated_task`.
- `scheduling_request`: original natural-language scheduling request.
- `schedule`: human-readable `cron_descriptor` description plus the next-run timezone abbreviation.
- `crontime`: normalized five-field cron string stored for the job.
- `next`: next run time formatted like `YYYY-MM-DD HH:MM AM/PM TZ`.

## Scheduling Actor Behavior

The scheduling actor is used to transform natural-language requests into three fields: `crontime`, `query`, and `subject`. Tests assert that it removes reminder-only wording from the execution query, preserves core task terms, and can infer daily or event-polling schedules. The API still validates and normalizes the actor output before storing a job.
