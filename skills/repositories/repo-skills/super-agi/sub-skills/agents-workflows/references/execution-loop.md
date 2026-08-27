# Execution Loop

## When to Read

Read this when you need to understand how a user request becomes a running
agent execution or scheduled Celery task.

## High-Level Flow

1. An agent or schedule is created through the API and associated with a
   workflow/template.
2. `main.py` startup seeds workflow rows and tool registrations when the app
   boots with a valid database.
3. `superagi.worker` defines Celery tasks for:
   - executing waiting workflows,
   - initializing scheduled agents,
   - executing the next agent step,
   - summarizing resources,
   - and sending webhook callbacks.
4. `AgentExecutor`/`AgentIterationStepHandler` and related classes build the
   prompt, select tools, parse the output, and store new execution state.
5. `TaskQueue` in Redis tracks pending and completed tasks for task-based flows.
6. Permission and wait steps can interrupt the loop until the user or timer
   resolves the checkpoint.

## Source Objects That Matter

- `AgentPromptTemplate` defines the canonical prompt families.
- `AgentPromptBuilder` constructs the final prompt text.
- `AgentSchemaOutputParser` and `AgentSchemaToolOutputParser` convert model
  output into structured tool actions.
- `ToolExecutor` runs the selected tool and reports success, error, or retry.
- `TaskQueue` stores queue items and completed-task history in Redis.
- `AgentWorkflowSeed` and `IterationWorkflowSeed` install default workflow
  definitions.

## Failure Modes

- Missing database records can break seed, fetch, or update steps.
- Redis failures can make the task queue appear empty or stuck.
- Invalid parser output can cause a retry loop or an unknown-tool error.
- A permission step that is never answered can leave the run waiting.
- A schedule that is not seeded or not advanced can prevent future task starts.
