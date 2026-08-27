# API Contracts

## Purpose

Read this when a backend response, request payload, or route family changes and the frontend service layer or UI must stay in sync.

## Canonical contract sources

| Source | Why it matters |
| --- | --- |
| `frontend/services/api.ts` | Single endpoint registry used by all service clients. |
| `frontend/lib/auth.ts` | Shared auth/session headers and token-expiry behavior. |
| `frontend/services/*.ts` | Request/response mappers that adapt backend JSON to frontend state. |
| `frontend/types/*.ts` | Frontend-facing response and form shapes. |
| `frontend/const/*.ts` | Client-side enum/string constants used by request builders and stream handling. |

## Endpoint families

### Auth, session, and identity

- `user`, `oauth`, `cas` in `services/api.ts`
- Common consumers: `services/authService.ts`, `services/sessionService.ts`, `services/oauthService.ts`, `services/casService.ts`, `lib/session.ts`
- Key shapes: `types/auth.ts`
- Update these together when login/session headers, token refresh, or logout behavior changes.

### Conversation and chat

- `conversation`, `share`, `agent.run`, `agent.nl2agentRun`, `skills.nl2skillRun`, `stt`, `tts`
- Common consumers: `services/conversationService.ts`, `app/[locale]/chat/*`, `app/[locale]/newchat/*`
- Key shapes: `types/conversation.ts`, `types/chat.ts`
- `conversationService.runAgent()` is special: it returns either a stream reader or JSON when the backend returns `application/json` during resume/completed runs.

### Agent configuration and lifecycle

- `agent`, `agentAutomation`, `prompt`, `promptTemplates`, `agentEvaluations`, `evaluationSets`, `evaluators`
- Common consumers: `services/agentConfigService.ts`, `services/agentVersionService.ts`, `services/agentAutomationService.ts`, `services/promptService.ts`, `services/promptTemplateService.ts`, `services/evaluationService.ts`
- Key shapes: `types/agentConfig.ts`, `types/agentRepository.ts`, `types/agentEvaluation.ts`
- Important page owners: `app/[locale]/agents/`, `agent-space/`, `agent-tasks/`, `space/evaluation/`, `space/evaluators/`

### Models and platform config

- `model`, `config`, `tenantConfig`, `quota`, `monitoring`
- Common consumers: `services/modelService.ts`, `services/configService.ts`, `services/quotaService.ts`, `services/monitoringService.ts`, `hooks/useConfig.ts`
- Key shapes: `types/modelConfig.ts`, `types/quota.ts`, `types/monitoring.ts`
- The frontend normalizes model list records into `ModelOption` and global config into `GlobalConfig`.

### Knowledge bases and external KB backends

- `knowledgeBase`, `datamate`, `dify`, `ragflow`, `idata`, `haotian`, `aidp`, `aidpMgmt`
- Common consumers: `services/knowledgeBaseService.ts`, `services/knowledgeBasePollingService.ts`, `hooks/useKnowledgeBaseSelector.ts`
- Key shapes: `types/knowledgeBase.ts`, `types/agentConfig.ts`
- The client maps several backend dialects into `KnowledgeBase` so the pages can present one consistent UI.

### Memory

- `memory`
- Common consumers: `services/memoryService.ts`, `hooks/useMemory.ts`, `components/memory/*`
- Key shapes: `types/memory.ts`
- The memory pages mix manual long-term records with agent-generated short-term memory and embedding-status checks.

### Skills, MCP, market, and repository flows

- `skills`, `mcp`, `mcpTools`, `tool`, `agentRepository`, `skillRepository`, `market`, `users`, `groups`, `invitations`, `storage`, `notifications`, `a2a`
- Common consumers: `services/skillService.ts`, `services/skillRepositoryService.ts`, `services/mcpService.ts`, `services/mcpToolsService.ts`, `services/marketService.ts`, `services/storageService.ts`, `services/notificationService.ts`, plus repository/market pages
- Key shapes: `types/skill.ts`, `types/skillRepository.ts`, `types/mcpTools.ts`, `types/market.ts`, `types/notification.ts`

## Frontend-facing response shapes that matter most

| Shape | Used by | Notes |
| --- | --- | --- |
| `ApiResponse<T>` | most service clients | Standard `code/message/data` wrapper. |
| `ApiConversationResponse`, `StreamingMessage` | chat history and resume | Conversation detail may include persisted streaming data. |
| `ModelValidationResponse`, `CapacitySuggestion`, `CapacityCoverage` | model pages | Capacity suggestion fields are normalized from snake_case. |
| `KnowledgeBase`, `Document`, `KnowledgeBasesWithDataMateStatus` | knowledge pages | External KB backends are normalized into a shared shape. |
| `MemoryConfig`, `LongTermMemoryVersion` | memory pages | Manual and dreaming-backed long-term memory use the same UI. |
| `Agent`, `PublishedAgent`, `AgentRepositoryListingItem`, `MyEditableAgentItem` | agent pages and repository views | Agent list/detail services reshape backend responses before rendering. |
| `Skill`, `SkillRepositoryListingItem`, `MyEditableSkillItem` | skill pages and repository views | Skill repository and editable skill lists have separate shapes. |
| `McpServiceItem`, `CommunityMcpCard`, `RegistryMcpCard` | MCP pages | Transport/source/deployment fields are normalized for filters. |
| `MarketAgentListItem`, `MarketAgentDetail` | market page | The detail payload carries tools, MCP servers, and raw agent JSON. |

## Error-handling contract

`frontend/services/api.ts` and `frontend/lib/auth.ts` handle the frontend's common failure modes:

- `ErrorCode.TOKEN_EXPIRED` and `ErrorCode.TOKEN_INVALID` trigger session-expired handling.
- HTTP `401` also triggers session-expired handling.
- HTTP `413` is treated as quota or file-size pressure and may surface `TenantStorageFull` specially.
- Network failures are converted into user-friendly `ApiError` messages.

When a response shape changes, the safest edit order is:
1. Update the shared type.
2. Update the service mapper.
3. Update the page/component that reads the field.
4. Run `scripts/extract_frontend_api_calls.py` to confirm the affected endpoint family.

## Backend cross-check

If a change starts in the server layer, coordinate with `../backend-services-api/SKILL.md` before changing the frontend contract. The frontend should adapt to the server contract, not invent a new one.
