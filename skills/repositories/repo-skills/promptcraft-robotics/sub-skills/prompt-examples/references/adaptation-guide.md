# Adaptation guide

Use this guide when you want to turn one repository example into a new robotics prompt without losing the repository's style.

## 1) Identify the closest family

Pick one of the example families in `category-map.md`.
Do not start from the file name alone; start from the robot, the sensing mode, and the task family.

## 2) Preserve the contract

Keep the allowed function set exactly aligned with the new scene.
If the scene is ambiguous, preserve the repository's clarification rule.
If the task depends on units or coordinate frames, state them explicitly in the prompt.

## 3) Adapt the task, not the structure

Replace:

- object names;
- scene counts;
- motion distances or heights;
- robot-specific primitive names;
- any object-height reasoning needed for grasping or placing.

Keep:

- the overall response style;
- the clarification policy;
- the distinction between code and explanation;
- the safe, incremental control logic when the example uses it.

## 4) Check for family-specific pitfalls

### Aerial robotics

- Make sure the prompt says whether the drone should face the goal, sweep an area, or maintain altitude.
- If there are multiple turbines, panels, or landmarks, ask for clarification instead of choosing one.
- Be explicit about the axis convention and the meaning of forward/right/up.

### Embodied agents

- Use stepwise exploration if the object is not visible immediately.
- Keep the turn/move commands consistent with the scene description.
- If the example uses perception, keep the perception-to-action loop clear.

### Manipulation

- Compute a safe height before grasping or releasing.
- Place objects on top of the target surface, not at table level.
- Maintain the correct stacking order and object count.

### Multiple robots

- Separate the controller by robot type.
- Do not apply car motion to a drone or drone altitude logic to an embodied agent.
- Comment the code so the robot-specific branch is obvious.

### Spatial-temporal reasoning

- Define the image-space assumption before mapping vision to control.
- If the example asks for SVG output, keep the geometry readable and centered on the intended condition.

## 5) Validate the draft

Use `scripts/validate-prompt-example.py` when you want a quick structural check.
That script is not a semantic proof; it only helps catch missing tags, missing code blocks, or obvious contract drift.

## 6) Final review questions

Before you consider a rewritten prompt ready, ask:

- Does it still fit the chosen family?
- Would a future agent know when to ask a clarification question?
- Does the prompt avoid hypothetical functions?
- Are the units and coordinate conventions explicit enough to avoid guessing?
- Could the prompt be understood without reopening the original repository?
