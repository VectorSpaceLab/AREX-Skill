# Skills and Negotiation

Skills are advertised capability descriptions; the handler implements behavior.

## Skill files

A skill directory can contain `skill.yaml`, `SKILL.md`, or both. Minimum metadata:

```yaml
name: question-answering
description: "Answer natural-language questions over supplied context."
```

Useful metadata: `version`, `author`, `tags`, `input_modes`, `output_modes`, `examples`, `capabilities_detail`, `requirements`, `performance`, and `assessment`.

## Config registration

```python
config = {
    "author": "you@example.com",
    "name": "research-agent",
    "deployment": {"url": "http://localhost:3773"},
    "skills": ["skills/question-answering"],
}
```

The TypeScript SDK sends raw skill content through gRPC so the Python core does not need access to the SDK project directory.

## Skill endpoints

| Endpoint | Returns |
|---|---|
| `GET /agent/skills` | Summary list: id, name, description, version, tags, input/output modes. |
| `GET /agent/skills/{skill_id}` | Detail without full documentation content; includes `has_documentation`. |
| `GET /agent/skills/{skill_id}/documentation` | Full raw YAML/Markdown documentation. |

`/.well-known/agent.json` includes compact skill summaries and documentation paths, not full docs.

## Private skills

Private skill files use the same shape but live in `private_skills` config. They appear only in `/agent/private.json` for authenticated allowlisted DIDs. Public skill endpoints list public skills only.

## Negotiation

`POST /agent/negotiation` scores a task against skills, I/O compatibility, performance metadata, load, and cost constraints.

```json
{
  "task_summary": "Extract table data from a PDF invoice",
  "input_mime_types": ["application/pdf"],
  "output_mime_types": ["application/json"],
  "max_latency_ms": 30000,
  "max_cost_amount": "0.05",
  "min_score": 0.0
}
```

Response fields include `accepted`, `score`, `confidence`, optional `rejection_reason`, `skill_matches`, `matched_tags`, `matched_capabilities`, `latency_estimate_ms`, `queue_depth`, and `subscores`.

Practical rule: write specific skill names, descriptions, tags, input/output modes, and assessment metadata so the calculator has real signals.
