# Baseline Attack Ideas

The public Nesa attack paper frames token recovery as a permutation-search
problem over a known vocabulary.

## Optimization framing

Let encrypted input/output sequences be `I_i` and `O_i`. Let `P` be a candidate
permutation that maps encrypted/private token IDs to original token IDs or text
tokens. A good `P` should make:

- decrypted inputs semantically meaningful;
- decrypted outputs semantically meaningful; and
- input/output pairs correspond to plausible LLM behavior.

The paper describes minimizing an average loss over released pairs, where the
loss measures semantic quality and correspondence. The search space can be as
large as `N!` for vocabulary size `N`, making exhaustive search infeasible for
Llama-scale vocabularies.

## Loss-function families

### LLM-as-a-judge

Ask a strong language model to score whether a candidate decrypted output is a
good answer to a candidate decrypted prompt. This may incorporate semantics but
can be expensive, noisy, and prompt-sensitive.

### Linguistic/domain heuristics

Use token frequency, common word/token guesses, grammar patterns, and prior
knowledge about conversational text. Examples include frequent tokens such as
articles, spaces, pronouns, punctuation, or common subword fragments.

## Optimizer families

### Brute force

Try every permutation and choose the lowest loss. This is infeasible beyond tiny
toy vocabularies because complexity is factorial.

### Random sampling / genetic search

Sample candidate permutations, score them, and keep the best. Genetic variants
can mix/crossover candidates. This is still uncertain and depends heavily on the
loss signal.

### Hill climbing

Start from an initial permutation and repeatedly swap two token assignments when
the move decreases loss. This can get stuck in local minima and needs a stop
budget.

## Safe use in an agent session

- Keep analysis local unless the user approves external LLM judge calls.
- Use toy vocabularies or user-provided practice data for runnable examples.
- Record assumptions: tokenizer family, known vocabulary, hints, released pairs,
  and scoring budget.
- Do not claim that a heuristic proves a real contest token mapping unless the
  user provides an evaluation signal.
