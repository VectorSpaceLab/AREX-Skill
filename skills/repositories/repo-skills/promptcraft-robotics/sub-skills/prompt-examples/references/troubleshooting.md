# Prompt example troubleshooting

This page covers the most common mistakes when adapting or classifying the repository's markdown examples.

## Ambiguous object identity

**Symptom**
- The draft prompt chooses one object even though the scene contains multiple objects of the same type.

**Likely cause**
- The clarification rule from the repository examples was dropped.

**Recovery**
- Ask a clarification question.
- Name the duplicate objects explicitly if the scene has them.

## Hypothetical function drift

**Symptom**
- The draft prompt uses a function that was never listed in the example context.

**Likely cause**
- The adaptation was written from memory instead of from the allowed function list.

**Recovery**
- Remove unsupported calls.
- Rebuild the solution using only the functions given in the prompt context.

## Coordinate-convention mistakes

**Symptom**
- The command appears correct in prose but is reversed when executed or explained.

**Likely cause**
- The prompt did not state its axis convention clearly enough.

**Recovery**
- Rewrite the prompt so forward/right/up or the relevant image-space mapping is explicit.
- Recompute the target motion instead of patching the prose only.

## Manipulation safety mistakes

**Symptom**
- A pick/place prompt touches objects at table level or stacks them with no safe-height reasoning.

**Likely cause**
- The adaptation skipped the object-height logic that the repository examples use.

**Recovery**
- Reintroduce the safe approach height.
- Place on top of the target surface or on the previous object in the stack.

## Prompt formatting drift

**Symptom**
- The rewritten prompt is understandable but no longer resembles the repository's style.

**Likely cause**
- The `Question` / `Code` / `Reason` structure or the equivalent response style was lost.

**Recovery**
- Restore the tag-based structure.
- Keep the code block and explanation order aligned with the source example family.

## Runtime-path leakage

**Symptom**
- A prompt or explanation tells future agents to open the original repository checkout.

**Likely cause**
- The adaptation was summarized too literally.

**Recovery**
- Replace source-repo links with the generated skill's bundled references or a self-contained explanation.
- Keep the runtime skill independent of the original checkout.
