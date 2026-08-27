# SuperAGI Workflow Reference

## When to Read

Read this when you need to choose or explain a SuperAGI workflow name or step
sequence.

## Workflow Families

### Goal Based Workflow

- Seeded by `AgentWorkflowSeed.build_goal_based_agent`.
- Uses an `IterationWorkflow` named `Goal Based Agent-I` and a single trigger
  step from `AgentPromptTemplate.get_super_agi_single_prompt()`.
- The step loops back to itself until the workflow completes.

### Dynamic Task Workflow

- Seeded by `AgentWorkflowSeed.build_task_based_agent` and
  `IterationWorkflowSeed.build_task_based_agents`.
- Uses the `Initialize Tasks-I` and `Dynamic Task Queue-I` iteration workflows.
- Emphasizes task analysis, task creation, and task prioritization.

### Fixed Task Workflow

- Seeded by `AgentWorkflowSeed.build_fixed_task_based_agent`.
- Uses `Initialize Tasks-I` and `Fixed Task Queue-I`.
- Maintains a fixed queue with repeated queue-step execution until complete.

### Sales Engagement Workflow

- Demonstrates a longer tool-driven workflow using file listing/reading,
  search, permission gating, email drafting, waiting, and another loop through
  task queue-like logic.

### Recruitment Workflow

- Demonstrates reading resumes, classifying candidates, and choosing accept or
  reject email paths via `YES/NO` branching.

### SuperCoder Workflow

- Built from `WriteSpecTool`, `WriteTestTool`, `CodingTool`, and a permission
  checkpoint.
- Useful when the user wants code/spec/test generation behavior.

## Step Types Observed in the Source

- `TRIGGER`
- `NORMAL`
- `TASK_QUEUE`
- `WAIT_FOR_PERMISSION`
- wait steps with timed delays
- tool steps with tool names and instructions

## Practical Interpretation

- Workflow names are stored in the database and reused by agents/templates.
- A workflow name mismatch can break template selection even when the model and
  tools are otherwise configured.
- Task queue behavior is backed by Redis, so queue errors often come from Redis
  connection problems rather than workflow logic itself.
