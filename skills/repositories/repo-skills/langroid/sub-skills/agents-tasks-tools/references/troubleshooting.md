# Troubleshooting

Use this table when a Langroid agent/task/tool flow breaks.

| Symptom | Likely cause | Fix | Route elsewhere |
| --- | --- | --- | --- |
| Tool never fires | `request` name does not match the handler, or `enable_message` was never called | Match the tool `request` to the handler name and call `enable_message` before running the task | — |
| Tool handler exists but is ignored | `use=False`, `handle=False`, or the message is not enabled for the current agent | Re-enable the tool with the right flags | — |
| LLM keeps answering in prose | The model never emitted a tool, or the tool mode is wrong | Use `MockLM` first, then confirm `use_tools` / `use_functions_api` are set correctly | — |
| `MockLM` ignores your test mapping | The config used `response` instead of `response_dict` / `response_fn` / `default_response` | Switch to the supported fields | — |
| Task ends too early | `single_round`, `done_if_tool`, `done_sequences`, `DoneTool`, or `FinalResultTool` is triggering earlier than expected | Tighten the termination rule and inspect the event chain | — |
| Task never ends | No explicit end signal, or the termination pattern is too strict | Add `DoneTool`, `ResultTool`, `FinalResultTool`, or a clearer `done_sequences` rule | — |
| `done_sequences` does not match | The event chain is not consecutive, or the tool name/class name does not match | Check the exact sequence and the tool map used at `Task` construction | — |
| Recipient routing fails | `recognize_recipient_in_content` is off, recipient is missing, or the wrong tool is used | Use `RecipientTool`, or enable `require_recipient=True` when needed | — |
| `TaskTool` cannot use a delegated tool | The parent agent never enabled the tool, so the child cannot inherit it | Enable the delegated tool on the parent agent too | — |
| XML tool parsing is broken | JSON tool mode is still enabled, or the XML payload lost verbatim content | Keep `use_tools=True` and `use_functions_api=False`, and mark raw fields verbatim | — |
| JSON / tool recovery fails | Malformed JSON, missing required fields, or strict schema mismatch | Add examples, fix the payload, or inspect `try_get_tool_messages` / `strict_recovery` paths | — |
| Batch returns surprising `None` values | `output_map` mapped a result to `None`, so it does not count as valid | Check the mapped output, not the raw completion | — |
| Provider or API-key error | Model backends or credentials are misconfigured | Move to the provider skill | [llm-provider-config](../../llm-provider-config/SKILL.md) |

## Fast checks

### Missing tool handler due to request mismatch

- Confirm the tool class `request` string.
- Confirm the agent method name.
- Confirm `enable_message(MyTool)` was called on the correct agent.
- Confirm the message was not routed to a different recipient.

### Forgetting `enable_message`

If the LLM generates a tool but the agent never handles it, the most common cause is
that the tool was never enabled on that agent.

### Wrong `MockLMConfig` field

The supported fields are `response_dict`, `response_fn`, `response_fn_async`, and
`default_response`.
If a test uses any other field, the mapping will not behave as expected.

### Premature or late termination

Check these in order:

1. `single_round`
2. `done_if_tool`
3. `done_sequences`
4. `DoneTool` / `FinalResultTool`
5. `recognize_string_signals`
6. `handle_llm_no_tool`

### `use_tools` vs `use_functions_api`

- `use_tools=True` means Langroid-native prompt-based tools.
- `use_functions_api=True` means provider-native function/tool calling.
- For XML tools, use native tools only.
- If the behavior looks inconsistent, simplify to one mode before debugging.

### Malformed JSON or tool recovery

- Use deterministic test JSON from `MockLM`
- Confirm required fields are present
- Check whether the tool should be strict or permissive
- Use `try_get_tool_messages` while debugging to avoid hard parse failures

## Related debugging rule

If the failure is about provider setup, model endpoints, or credentials, do not keep
debugging the agent/task/tool flow here. Route to the provider sub-skill instead.
