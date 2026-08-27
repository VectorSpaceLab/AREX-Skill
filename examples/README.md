# DisCo Examples

These self-contained HTML exports show complete DisCo sessions. Clone or
download the repository, open an HTML file in a browser, and expand the tool
calls you want to inspect. No DisCo installation or network connection is
required to read an export.

## Creator

### FlagEmbedding Repository Skill

- [FlagOpen/FlagEmbedding repository](https://github.com/FlagOpen/FlagEmbedding)
- [Open the sanitized session](creator/disco-creator-FlagEmbedding.html)
- [Browse the resulting skill](../skills/repositories/repo-skills/flag-embedding/SKILL.md)

This session follows Creator as it inspects FlagOpen/FlagEmbedding, prepares
the working environment, scopes and writes the operating skill graph, verifies
its references and helper scripts, and reviews the result. Near the middle of
the run, the session reaches a context boundary and the user sends `continue`;
the following entries resume the same creation workflow.

## Researcher

### Gymnasium and Stable-Baselines3 Battery Dispatch

- [Farama-Foundation/Gymnasium repository](https://github.com/Farama-Foundation/Gymnasium)
- [DLR-RM/stable-baselines3 repository](https://github.com/DLR-RM/stable-baselines3)
- [Open the sanitized session](researcher/disco-researcher-Gymnasium-Stable-Baselines3.html)
- [Browse the Gymnasium skill](../skills/repositories/repo-skills/gymnasium/SKILL.md)
- [Browse the Stable-Baselines3 skill](../skills/repositories/repo-skills/stable-baselines3/SKILL.md)

This session follows Researcher as it routes a battery-dispatch task through
`repo-skills-router`, progressively loads the relevant Gymnasium and
Stable-Baselines3 guidance, implements a custom environment, and trains and
reloads a PPO controller. It also verifies the environment, preserves
train-only preprocessing and baseline construction, evaluates every held-out
test day, and writes reproducible audit artifacts. The reported result is kept
intact: PPO improves on the no-battery baseline but not the train-derived rule
baseline.

## Sanitization

Runtime provider and agent-model identifiers, workstation-specific home paths,
session identifiers, provider signatures, response identifiers, system
prompts, and personal contact details are sanitized in the public exports.
Task inputs, tool activity, generated code, measurements, and reported outcomes
are preserved.
