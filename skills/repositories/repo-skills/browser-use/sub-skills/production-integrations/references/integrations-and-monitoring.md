# Integrations and Monitoring

Read this when Browser Use is embedded in a service, bot, webhook worker, or observability stack. Keep external credentials in environment variables or a secret manager, and never put tokens or cookies in prompts, logs, or generated files.

## External App Pattern

For Slack, Discord, email, support queues, or webhook-triggered agents:

1. Verify the inbound request with the platform's signing secret or bot token before starting a browser run.
2. Deduplicate event ids to avoid duplicate browser sessions.
3. Acknowledge quickly when the platform has a short response deadline.
4. Queue Browser Use work in a background task, worker, or sandbox run.
5. Use `ChatBrowserUse()` by default for browser automation unless the user selected another model.
6. Use cloud profiles or domain-scoped custom tools for authenticated sites.
7. Return `history.final_result()` or a Pydantic structured output, not raw logs with secrets.

## Email and 2FA

- For Gmail, AgentMail, one-time passwords, or authenticator flows, prefer a custom tool that returns the code or message content from a trusted service.
- Tell the agent task to use the custom action for 2FA and never scrape codes from unrelated page text.
- If the integration needs file uploads or downloads, route the file security details to `../../tools-and-actions/SKILL.md`.

## Webhook Worker Shape

```python
from browser_use import Agent, Browser, ChatBrowserUse

async def handle_verified_event(event):
    browser = Browser(use_cloud=True, allowed_domains=["*.example.com"])
    agent = Agent(
        task=event["task"],
        browser=browser,
        llm=ChatBrowserUse(),
        max_failures=3,
    )
    history = await agent.run(max_steps=30)
    return {"result": history.final_result(), "success": history.is_successful()}
```

Use `@sandbox` instead when the whole function should run in Browser Use managed infrastructure.

## Monitoring and Telemetry

- Browser Use anonymous telemetry can be disabled with `ANONYMIZED_TELEMETRY=false` before importing `browser_use`.
- Cloud sessions provide task/session ids and live URLs; only share live URLs when they do not expose sensitive accounts.
- Cost tracking for LLM calls belongs in `../../llm-and-output/SKILL.md`; production logging should include model name, task id, session id, Browser Use version, and sanitized error categories.
- Third-party monitoring patterns such as Laminar/OpenLIT should keep vendor keys in env vars and be initialized before long-running agent tasks.

## Production Log Checklist

Capture these fields for support without leaking secrets:

- Browser Use package version and Python version.
- Runtime mode: local browser, cloud browser, `@sandbox`, REST Cloud task, MCP, or hosted skill.
- Model provider/model name exactly as configured.
- Task/session id, timestamps, and sanitized exception type.
- Whether `BROWSER_USE_API_KEY` is present, not its value.
- Browser mode, domain restrictions, proxy country, and profile id presence when relevant.

## Integration Failure Boundaries

- Browser/session/profile/CDP failures: route to `../../browser-control/SKILL.md`.
- Custom tool, file, upload, or secret-injection failures: route to `../../tools-and-actions/SKILL.md`.
- Model credentials, structured output, or fallback model failures: route to `../../llm-and-output/SKILL.md`.
- CLI daemon/session/tunnel failures: route to `../../cli-and-sessions/SKILL.md`.
