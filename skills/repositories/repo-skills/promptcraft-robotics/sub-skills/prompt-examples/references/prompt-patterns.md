# Prompt patterns

The repository's examples reuse a small number of prompt shapes. Preserve these when adapting or rewriting examples.

## Core response pattern

| Tag | Meaning | Typical use |
| --- | --- | --- |
| `Question` | Ask for clarification when the task is ambiguous | Duplicate objects, missing target identity, incomplete scene information |
| `Code` | Return the actionable robot command or snippet | The task can be executed with the allowed functions |
| `Reason` | Explain the choice after the code | The repository's examples often pair code with a short explanation |

## Common structure rules

- Start by naming the allowed functions and nothing else.
- State the object list or scene context when the example depends on it.
- Tell the assistant not to invent extra functions.
- Keep the motion or manipulation units explicit.
- Clarify duplicated objects instead of guessing.
- Use short comments inside code when the example style benefits from them.

## Family-specific patterns

### Aerial robotics

- Use drone primitives such as yaw, waypoint motion, altitude, and object location.
- For inspection tasks, describe paths or sweeps rather than single-point motion.
- For obstacle avoidance, move in small steps and re-check the scene between actions.
- Keep the camera / heading logic explicit when the prompt cares about the direction of inspection.

### Embodied agents

- Use perception-first loops where the agent looks, detects, then moves.
- Favor turn/move traces that can be executed one step at a time.
- Preserve the instruction to explore if the object is not visible at first.

### Manipulation

- Move to a safe height before touching an object.
- Place or stack objects by reasoning about object height and top surfaces.
- Use release/grab logic only after a safe approach.

### Multiple robots

- Separate the control logic by robot type.
- Respect each robot's constraints instead of trying to reuse one command set everywhere.
- Comment the code so the mapping from robot to primitive is obvious.

### Spatial-temporal reasoning

- Treat the camera image as the primary evidence.
- Explain how image-space error maps to control output.
- When asked for an SVG, show the geometry with a simple, readable shape.

### Basic robotics

- Use compact, defensible control math.
- State coordinate conventions before deriving a controller.
- Keep the example focused on the control concept rather than the full implementation stack.

## Rewriting checklist

1. Keep the original task family.
2. Replace object names, scene details, or coordinates with the new scenario.
3. Preserve the allowed function list.
4. Preserve the clarification behavior.
5. Keep the response tags or the repo's equivalent structure.
6. Validate the draft with the bundled script if the prompt is going to be reused.
