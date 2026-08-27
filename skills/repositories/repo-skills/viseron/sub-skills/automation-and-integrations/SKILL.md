---
name: automation-and-integrations
description: "Guides Viseron MQTT/Home Assistant automation, webhooks,
  notifications, Telegram/PTZ control, events, templates, and integration
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Automation and Integrations

Use this sub-skill when the user needs Viseron to publish automation state, trigger external actions, send notifications, control cameras from Telegram, or reason about system events and Jinja template conditions.

## Route by task

- **MQTT, Home Assistant discovery, MQTT state topics, manual recording switches, or external MQTT motion input**: read [MQTT and Home Assistant](references/mqtt-and-home-assistant.md).
- **Webhook delivery, HTTP headers/auth/TLS, Discord/Gotify/Telegram notifications, Telegram commands, or ONVIF PTZ control**: read [webhooks, notifications, and PTZ](references/webhooks-notifications-and-ptz.md).
- **Event names, data-stream topics, webhook template context, or Jinja condition behavior**: read [events and templates](references/events-and-templates.md). Use [scripts/render_template_condition.py](scripts/render_template_condition.py) to test a condition or payload locally before applying it to a live config.
- **Entities missing, webhooks overfiring, notifications not sent, Telegram commands denied, PTZ not moving, or template errors**: read [troubleshooting](references/troubleshooting.md).

## Boundaries

This sub-skill owns automation outputs and control surfaces: MQTT/Home Assistant discovery, webhooks, Discord/Gotify/Telegram notifications, Telegram/PTZ commands, Viseron event names, data-stream topics, and Jinja template conditions.

Route detailed detector label semantics, masks, zones, and model choices to `detection-and-ai-components`. Route camera stream setup, recorder internals, storage tiers, and clip lifecycle to `camera-recording-pipeline`. Route global deployment, webserver authentication/API basics, secrets, and startup validation to `configuration-and-deployment`. Route writing or extending integration components to `developer-extension`.

## Safe operating defaults

1. Redact tokens, webhook URLs, chat IDs, basic-auth credentials, ONVIF passwords, and broker credentials in user-visible output.
2. Treat MQTT brokers, webhook targets, Discord/Gotify/Telegram services, Telegram bots, ONVIF cameras, and public image URLs as external requirements unless the user explicitly asks for live verification.
3. Validate event names and Jinja conditions locally before enabling an action that could send messages or move a camera.
4. Prefer exact camera identifiers and explicit label lists in automation filters; do not infer detector label behavior beyond the event payload and notifier filter rules documented here.
