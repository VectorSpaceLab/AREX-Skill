# SuperAGI Data Models

## When to Read

Read this when an API, migration, or controller problem depends on the shape of
stored records.

## Core Model Families

### Identity and Organization

- `User(id, name, email, password, organisation_id, first_login_source)`
- `Organisation(id, name, description)`
- `Project(id, name, organisation_id, description)`

### Agents and Execution

- `Agent(id, name, project_id, description, agent_workflow_id, is_deleted)`
- `AgentConfiguration(id, agent_id, key, value)`
- `AgentExecution(id, status, name, agent_id, last_execution_time, num_of_calls,
  num_of_tokens, current_agent_step_id, permission_id,
  iteration_workflow_step_id, current_feed_group_id, last_shown_error_id)`
- `AgentExecutionConfiguration(id, agent_execution_id, key, value)`
- `AgentExecutionFeed(id, agent_execution_id, agent_id, feed, role,
  extra_info, feed_group_id, error_message)`
- `AgentExecutionPermission(id, agent_execution_id, agent_id, status,
  tool_name, user_feedback, question, assistant_reply)`
- `AgentSchedule(id, agent_id, start_time, next_scheduled_time,
  recurrence_interval, expiry_date, expiry_runs, current_runs, status)`

### Workflows

- `AgentWorkflow(id, name, description)`
- `AgentWorkflowStep(id, agent_workflow_id, unique_id, step_type, action_type,
  action_reference_id, next_steps)`
- `AgentWorkflowStepTool(id, tool_name, unique_id, input_instruction,
  output_instruction, history_enabled, completion_prompt)`
- `AgentWorkflowStepWait(id, name, description, unique_id, delay,
  wait_begin_time, status)`
- `IterationWorkflow(id, name, description, has_task_queue)`
- `IterationWorkflowStep(id, iteration_workflow_id, unique_id, prompt,
  variables, output_type, step_type, next_step_id, history_enabled,
  completion_prompt)`

### Tools and Toolkits

- `Toolkit(id, name, description, show_toolkit, organisation_id, tool_code_link)`
- `Tool(id, name, description, folder_name, class_name, file_name, toolkit_id)`
- `ToolConfig(id, key, value, toolkit_id, key_type, is_secret, is_required)`
- `ApiKey(id, org_id, name, key, is_expired)`
- `Configuration(id, organisation_id, key, value)`

### Resources, Knowledge, and Vector Stores

- `Resource(id, name, storage_type, path, size, type, channel, agent_id,
  agent_execution_id, summary)`
- `Knowledges(id, name, description, vector_db_index_id, organisation_id,
  contributed_by)`
- `KnowledgeConfigs(id, knowledge_id, key, value)`
- `Vectordbs(id, name, db_type, organisation_id)`
- `VectordbIndices(id, name, vector_db_id, dimensions, state)`
- `VectordbConfigs(id, vector_db_id, key, value)`

### Models and Providers

- `Models(id, model_name, description, end_point, model_provider_id,
  token_limit, type, version, org_id, model_features, context_length)`
- `ModelsConfig(id, provider, api_key, org_id)`
- `OauthTokens(id, user_id, organisation_id, toolkit_id, key, value)`

### Telemetry and Webhooks

- `CallLogs(id, agent_execution_name, agent_id, tokens_consumed, tool_used,
  model, org_id)`
- `Event(id, event_name, event_value, event_property, agent_id, org_id)`
- `MarketPlaceStats(id, reference_id, reference_name, key, value)`
- `WebhookEvents(id, agent_id, run_id, event, status, errors)`
- `Webhooks(id, name, org_id, url, headers, is_deleted, filters)`

## Relationship Hints

- `Agent` belongs to a `Project` and points at an `AgentWorkflow`.
- `AgentExecution` belongs to an `Agent` and stores status and counters.
- `AgentWorkflowStep` can point at tool, wait, or iteration step records by
  action reference.
- `Tool` belongs to a `Toolkit`, and `ToolConfig` is keyed by toolkit id.
- `Resource` can be tied to both agent and execution ids.
- `VectordbIndices` belongs to a `Vectordbs` row; `Knowledges` points to an
  index.

## Practical Use

- If a controller wants a record by id and returns `404`, look for the owning
  model's `find_by_id` or `find_or_create_by_name` helper in the source.
- If a route error mentions organisation mismatch, inspect the `organisation_id`
  on the relevant model family before assuming the controller is wrong.
- If an execution or permission route is missing a foreign key, the current run
  may not have been seeded or scheduled correctly.
