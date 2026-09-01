---
name: context_sense_tagger
description: Select or defer WordNet-style sense pointers using current and previous sentence context.
---

# Context Sense Tagger

Use this skill to emulate the ConText output contract from the WordNet report. It consumes preprocessed token records and a WordNet-style taxonomy, then emits selected sense pointers or explicit unresolved reasons.

## Inputs
- Sentence records from the collocation/morphology preprocessor.
- A taxonomy created with the lexical taxonomy schema skill.

## Outputs
- Tagged token records with `sense_id` and confidence when selected.
- Unresolved records with a reason such as `no_wordnet_entry_for_lemma_pos`, `ambiguous_context_tie`, or `insufficient_context`.

## Workflow
1. Build a lemma/POS index over taxonomy synsets.
2. Gather context terms from the current and previous sentence.
3. Filter candidates by uninflected lemma and POS.
4. Score candidates by overlap with gloss and related-synset lemmas.
5. Select only a unique supported candidate; otherwise record a reason instead of inventing a pointer.

## Validation
Run `python tests/test_sense_tagger.py` or `validate_skill_tree.py --run-tests`.

## Limitations
The scorer is deterministic and small. It captures the paper mechanism for recovery, not a full automatic word-sense-disambiguation system.
