# Scheduler Runtime

Khoj uses APScheduler with a Django-backed job store for automations. The scheduler is initialized during server startup, and only one elected schedule leader process should execute scheduled jobs at a time.

## Components

- `BackgroundScheduler`: process-local APScheduler instance stored in shared application state.
- `DjangoJobStore`: persistent APScheduler job store added as the `default` job store.
- `CronTrigger.from_crontab`: converts normalized five-field cron strings into run triggers.
- `ProcessLock`: database-backed lock model used for scheduler leadership and per-job execution locks.
- `run_with_process_lock`: APScheduler-callable wrapper that runs scheduled work while holding a process lock.
- `scheduled_chat`: automation task function that calls Khoj's chat API and optionally sends or returns a formatted result.

## Startup and Scheduler Defaults

During startup, Khoj creates a `BackgroundScheduler` configured with:

- Scheduler timezone `UTC`.
- Job default `misfire_grace_time` of 60 seconds.
- Job default `coalesce` set to true, so delayed duplicate run slots can collapse into one run.
- A `DjangoJobStore` named `default`.

The scheduler is started either active or paused depending on schedule leader election. Workers that are not the leader can still add, edit, and delete jobs through the shared job store, but should not execute scheduled jobs.

## Schedule Leader Election

Khoj stores scheduler leadership in a process lock named `schedule_leader` with a twelve-hour maximum duration.

Startup behavior:

- If a `schedule_leader` lock already exists, the worker starts its scheduler paused.
- If no leader lock exists, the worker creates the lock, starts the scheduler active, and records the lock in application state.
- If another worker wins the database race and lock creation raises an integrity error, the current worker starts paused.

Shutdown behavior:

- A worker that holds the leader lock removes it during scheduler shutdown.
- Scheduler shutdown errors are logged at debug level and ignored.

Ongoing wakeup behavior:

- A lightweight periodic wakeup checks whether the current leader lock is still valid.
- If the current process's leader lock expired, the process clears it and pauses its scheduler.
- If no valid leader exists, the process creates a new `schedule_leader` lock, records it, resumes the scheduler, and logs that leadership was acquired.
- If the process is not the leader, it keeps the scheduler paused.

## Per-Automation Job Locks

Each automation job wraps `scheduled_chat` in `run_with_process_lock`. The operation name is based on `scheduled_job`, the user UUID, and the automation query hash. The wrapper exits early if a matching lock is already active, preventing concurrent duplicate executions. Stale locks are deleted after their configured maximum duration.

Automation jobs use `max_instances=2` so a second instance can start and clear a stale lock path if needed, while the process lock remains the real guard against duplicate work.

## Timezones and Cron

API create/edit normalize cron strings before calling scheduler code:

- Strip surrounding whitespace.
- Use only the first five cron fields if more were supplied.
- Replace `?` with `*`.
- Reject non-numeric minute fields.

Scheduling then parses the timezone and creates `CronTrigger.from_crontab(crontime, user_timezone)`. The stored scheduler default timezone is UTC, but each automation trigger can carry the user's timezone. Returned metadata formats schedule descriptions with `cron_descriptor` and the next run time's timezone abbreviation.

The synchronous scheduler path falls back to UTC when a timezone string is invalid. The async scheduling helper uses direct timezone parsing and expects a valid timezone.

## Scheduled Chat Execution

When a scheduled job runs:

1. If a job id is present, Khoj checks the most recent successful execution for that job.
2. If the job executed within the last six hours, the function returns early to reduce duplicate execution and rate-limit risk.
3. Khoj rewrites the original automation request URL into a JSON payload for `/api/chat?client=khoj`.
4. It replaces the query with the normalized `query_to_run` and injects the stored `conversation_id` when available.
5. If the stored conversation no longer exists, Khoj deletes the automation and exits.
6. If anonymous mode is off, Khoj adds a bearer token for the user.
7. It posts to the chat API, follows common redirect responses manually, and stops if the final status is not `200`.
8. It removes the `/automated_task` prefix for notification formatting.
9. It asks the notification decision actor whether the result should notify the user.
10. If notification is appropriate, it formats the automation response and sends email when the email provider is enabled; otherwise it can return the formatted response.

Manual trigger uses the same stored scheduled function and kwargs, but starts it in a new thread and returns immediately to the API caller.

## Operational Implications

- Non-leader workers can appear healthy and can mutate jobs, but their schedulers are intentionally paused.
- A stale `schedule_leader` lock can delay execution until the wakeup path recognizes it as expired or a worker reacquires leadership.
- Missing conversations are treated as invalid automation state; the job is deleted rather than recreated automatically.
- Invalid timezone handling differs between API edit and lower-level scheduling helpers, so prefer validating timezone at API/client boundaries.
- Cron strings should be normalized and validated before comparing job ids, diagnosing duplicate jobs, or checking expected metadata.
