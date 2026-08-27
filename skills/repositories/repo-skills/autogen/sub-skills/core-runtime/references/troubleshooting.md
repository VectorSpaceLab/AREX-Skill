# Core Runtime Troubleshooting

Use this matrix for low-level `autogen_core` failures before escalating to AgentChat or extension-specific debugging.

| Symptom | Likely cause | Diagnosis | Fix |
| --- | --- | --- | --- |
| `send_message` raises `Recipient not found` or `Agent type ... does not exist` | `AgentId.type` does not match a registered type. | Print registered type strings and compare with `AgentId(type=...)`; check factory registration order. | Register the target type before sending, or use the correct logical type string. |
| Publish appears to succeed but no handler runs | No matching subscription or wrong topic type/source. | Compare `DefaultTopicId(type=...)` with `type_subscription(...)` or `TypeSubscription.topic_type`; inspect whether source maps to expected key. | Add/update subscription and publish to the agreed topic type; use explicit source during debugging. |
| Handler never matches although message class looks right | Routed dispatch uses exact runtime type, not inheritance or similar class names. | Log `type(message)` in `on_unhandled_message`; check duplicate message classes imported from different modules. | Register a handler for the exact class or normalize message imports. |
| Decorator raises missing `message` or return annotation assertion | Handler signature is not the required async typed shape. | Check for `async def handler(self, message: MyType, ctx: MessageContext) -> ReturnType`. | Add concrete message and return annotations; return `None` explicitly for events. |
| `CantHandleException` from strict handler | Message concrete type is outside handler target types. | Inspect `handler.target_types` and the actual message type. | Fix the caller message type or temporarily use `strict=False` only to observe legacy behavior. |
| `ValueError` about return type | Handler returned a type outside its return annotation under strict validation. | Print the returned value and compare with the annotated return types. | Correct the annotation or return value; avoid returning implicit `None` from an RPC handler annotated with a response type. |
| Background publish exceptions seem hidden | `ignore_unhandled_exceptions=True` stores or suppresses publish handler failures until later lifecycle calls. | Re-run with `SingleThreadedAgentRuntime(ignore_unhandled_exceptions=False)` and await `stop_when_idle()`/`stop()`. | Use `False` during debugging; always drain and stop the runtime in tests. |
| Test hangs or process exits before publish handler completes | Runtime not drained/stopped after `publish_message`. | Check for missing `await runtime.stop_when_idle()` after publish. | Await `stop_when_idle()` for publish fan-out; await direct `send_message` responses. |
| Runtime reports pending/unprocessed messages | Lifecycle order is incomplete or handler enqueued more work. | Inspect `runtime.unprocessed_messages_count` and handler publish/send calls. | Wait for idle, add termination conditions in custom loops, and avoid unbounded recursive publishes. |
| `buffer_size must be greater than 0` | Invalid `BufferedChatCompletionContext` argument. | Inspect context constructor call. | Use positive `buffer_size`; add validation to config ingestion. |
| Token-limited context fails on token counting | Supplied model client lacks required token methods or is not configured. | Check `count_tokens` and `remaining_tokens` on the model client. | Route concrete model-client setup to `extensions-integrations`; use buffered context if no token counter is available. |
| `FunctionTool` schema errors | Missing type annotations, unsupported defaults under strict mode, or ambiguous function signature. | Inspect `inspect.signature(func)` and generated `tool.schema`. | Annotate every parameter and return; set `strict=True` only when required by structured output. |
| `StaticWorkbench.call_tool` says tool not found | Name mismatch caused by tool override or wrong original name. | Call `await workbench.list_tools()` and compare requested name. | Use the displayed schema name; avoid override-name collisions. |
| Component loading raises invalid provider/import/trust error | Provider string is malformed, module unavailable, namespace not trusted, or class is not a component. | Inspect `ComponentModel.provider`; attempt an import in the runtime environment. | Use public provider overrides; install/import required package; set `AUTOGEN_ALLOWED_PROVIDER_NAMESPACES` only for trusted custom namespaces. |
| Component schema validation fails | Config fields do not match installed package version. | Compare dumped `version`, `component_version`, and config keys with installed package. | Regenerate config with the current package or write explicit migration code. |
| Loading `FunctionTool` warns about security | Tool config contains executable imports/source. | Confirm the config source and `global_imports`. | Only load trusted configs; never load user-submitted tool config directly. |
| Cancellation does not stop work | Token was not passed to the operation or long-running code does not cooperate. | Trace the `CancellationToken` from caller to runtime/tool/handler; check linked futures. | Pass one token through the operation tree and check/link it inside long-running tasks. |
| Intervention makes messages disappear or mutate unexpectedly | Runtime intervention handler drops or transforms messages. | Temporarily run without `intervention_handlers`; log before/after message identity and content. | Keep interventions deterministic, narrowly scoped, and documented. |
| Distributed runtime fails but local runtime works | Transport, serializer, provider import, worker registration, or version skew problem. | Run the same minimal case locally; then compare package versions, serializers, provider imports, and topic/subscription registration on each process. | Route concrete gRPC/runtime extension setup to `extensions-integrations`; keep core logic unchanged until transport boundary is isolated. |
| Protobuf/gRPC confusion with .NET or protocol docs | Protocol concepts are being treated as Python implementation APIs. | Identify whether the task is conceptual protocol compatibility or concrete Python runtime code. | Use protocol docs only to reason about IDs/messages/services; implement Python work through `autogen_core` and `autogen_ext` APIs. |

## Fast Debug Checklist

1. Set `ignore_unhandled_exceptions=False` while reproducing.
2. Print `AgentId`, `TopicId`, concrete message type, and handler name.
3. Verify registration and subscription before inspecting handler logic.
4. Await the correct lifecycle method: response for direct sends, `stop_when_idle()` for publishes, `stop()` for final cleanup.
5. Reduce component/tool failures to a single dump/load or `run_json` call.
6. Reproduce locally before adding distributed runtime or model-client dependencies.

## Version-Boundary Notes

`autogen-core`, `autogen-agentchat`, and `autogen-ext` 0.7.x can coexist for current Python maintenance. Some tooling packages historically pin older AutoGen ranges, especially Studio and Magentic-One CLI variants; do not force them into the same environment when diagnosing core runtime behavior. Treat those as separate tooling/version-boundary tasks.
