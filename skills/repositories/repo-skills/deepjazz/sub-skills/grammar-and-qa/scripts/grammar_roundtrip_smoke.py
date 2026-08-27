#!/usr/bin/env python
"""Tiny deepjazz grammar/QA smoke helper.

This script is self-contained: it imports only music21 plus the Python standard
library, builds synthetic voices, adapts deepjazz's grammar/QA behavior, and
prints structural signals. It deliberately avoids model training, MIDI parsing,
playback, downloads, network access, and file writes.
"""
from __future__ import print_function

import argparse
import copy
import json
import random
import sys

try:
    from itertools import izip_longest as _zip_longest
except ImportError:  # Python 3
    from itertools import zip_longest as _zip_longest

from music21 import chord, interval, note, scale, stream


def _round_down(num, mult):
    return float(num) - (float(num) % mult)


def _round_up(num, mult):
    return _round_down(num, mult) + mult


def _round_up_down(num, mult, up_down):
    if up_down < 0:
        return _round_down(num, mult)
    return _round_up(num, mult)


def _grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return _zip_longest(*args, fillvalue=fillvalue)


def _parse_duration(token):
    terms = token.split(',')
    if len(terms) < 2:
        raise ValueError('Malformed grammar token %r: expected TYPE,DURATION' % token)
    try:
        duration = float(terms[1])
    except ValueError:
        raise ValueError('Malformed duration in token %r: field 2 must be a float' % token)
    return terms, duration


def prune_grammar(curr_grammar):
    pruned = []
    for gram in curr_grammar.split(' '):
        if not gram:
            continue
        terms, duration = _parse_duration(gram)
        terms[1] = str(_round_up_down(duration, 0.250, random.choice([-1, 1])))
        pruned.append(','.join(terms))
    return ' '.join(pruned)


def prune_notes(curr_notes):
    """Return a safe list-copy equivalent of deepjazz's adjacent duplicate prune."""
    pruned = []
    for n1, n2 in _grouper(list(curr_notes), 2):
        if n1 is not None:
            pruned.append(n1)
        if n2 is None:
            continue
        if isinstance(n1, note.Note) and isinstance(n2, note.Note):
            if n1.nameWithOctave == n2.nameWithOctave:
                continue
        pruned.append(n2)
    return pruned


def _copy_element_preserve_offset(element):
    copied = copy.deepcopy(element)
    copied.offset = element.offset
    return copied


def clean_up_notes(curr_notes):
    """Return a safe list-copy equivalent of deepjazz's zero-length/offset QA."""
    source = list(curr_notes)
    cleaned = []
    ix = 0
    while ix < len(source):
        current = _copy_element_preserve_offset(source[ix])
        if current.quarterLength == 0.0:
            current.quarterLength = 0.250
        if ix < len(source) - 1:
            nxt = source[ix + 1]
            if source[ix].offset == nxt.offset and isinstance(nxt, note.Note):
                cleaned.append(current)
                ix += 2
                continue
        cleaned.append(current)
        ix += 1
    return cleaned


def _is_scale_tone(last_chord, curr_note):
    scale_type = scale.DorianScale()
    if last_chord.quality == 'major':
        scale_type = scale.MajorScale()
    derived = scale_type.derive(last_chord)
    note_names = set([pitch.name for pitch in derived.getPitches()])
    return curr_note.name in note_names


def _is_approach_tone(last_chord, curr_note):
    for chord_pitch in last_chord.pitches:
        step_up = chord_pitch.transpose(1)
        step_down = chord_pitch.transpose(-1)
        if (curr_note.name == step_down.name or
                curr_note.name == step_down.getEnharmonic().name or
                curr_note.name == step_up.name or
                curr_note.name == step_up.getEnharmonic().name):
            return True
    return False


def _is_chord_tone(last_chord, curr_note):
    return curr_note.name in [p.name for p in last_chord.pitches]


def _generate_chord_tone(last_chord):
    names = sorted([p.nameWithOctave for p in last_chord.pitches])
    return note.Note(random.choice(names))


def _generate_scale_tone(last_chord):
    scale_type = scale.WeightedHexatonicBlues()
    if last_chord.quality == 'major':
        scale_type = scale.MajorScale()
    derived = scale_type.derive(last_chord)
    note_names = sorted(set([pitch.name for pitch in derived.getPitches()]))
    note_name = random.choice(note_names)
    octaves = sorted([p.octave for p in last_chord.sortAscending().pitches])
    return note.Note('%s%s' % (note_name, random.choice(octaves)))


def _generate_approach_tone(last_chord):
    scale_note = _generate_scale_tone(last_chord)
    return scale_note.transpose(random.choice([1, -1]))


def parse_melody(full_measure_notes, full_measure_chords):
    measure = copy.deepcopy(full_measure_notes)
    chords = copy.deepcopy(full_measure_chords)
    measure.removeByNotOfClass([note.Note, note.Rest])
    chords.removeByNotOfClass([chord.Chord])
    if len(measure) == 0:
        raise ValueError('Synthetic melody voice has no notes/rests')
    if len(chords) == 0:
        raise ValueError('Chord voice has no chord.Chord elements')

    measure_start_time = measure[0].offset - (measure[0].offset % 4)
    full_grammar = ''
    prev_note = None
    num_non_rests = 0

    for ix, nr in enumerate(measure):
        try:
            last_chord = [n for n in chords if n.offset <= nr.offset][-1]
        except IndexError:
            chords[0].offset = measure_start_time
            last_chord = [n for n in chords if n.offset <= nr.offset][-1]

        if isinstance(nr, note.Rest):
            element_type = 'R'
        elif nr.name in last_chord.pitchNames or isinstance(nr, chord.Chord):
            element_type = 'C'
        elif _is_scale_tone(last_chord, nr):
            element_type = 'S'
        elif _is_approach_tone(last_chord, nr):
            element_type = 'A'
        else:
            element_type = 'X'

        note_info = '%s,%.3f' % (element_type, nr.quarterLength)
        interval_info = ''
        if isinstance(nr, note.Note):
            num_non_rests += 1
            if num_non_rests == 1:
                prev_note = nr
            else:
                note_dist = interval.Interval(noteStart=prev_note, noteEnd=nr)
                note_dist_upper = interval.add([note_dist, 'm3'])
                note_dist_lower = interval.subtract([note_dist, 'm3'])
                interval_info = ',<%s,%s>' % (
                    note_dist_upper.directedName,
                    note_dist_lower.directedName,
                )
                prev_note = nr

        full_grammar += note_info + interval_info + ' '

    return full_grammar.rstrip()


def _last_chord_at_or_before(chords, offset):
    try:
        return [n for n in chords if n.offset <= offset][-1]
    except IndexError:
        if len(chords) == 0:
            raise ValueError('Chord voice has no chord.Chord elements')
        chords[0].offset = 0.0
        return [n for n in chords if n.offset <= offset][-1]


def _pick_from_candidates(candidates, prev_element):
    if len(candidates) > 1:
        filtered = [i for i in candidates if i.nameWithOctave != prev_element.nameWithOctave]
        if filtered:
            return random.choice(filtered)
    if len(candidates) == 1:
        return candidates[0]
    return prev_element.transpose(random.choice([-2, 2]))


def _candidate_notes(low_pitch, high_pitch):
    num_notes = int(high_pitch.ps - low_pitch.ps + 1)
    if num_notes < 1:
        return []
    return [note.Note(low_pitch.transpose(i).simplifyEnharmonic())
            for i in range(0, num_notes)]


def unparse_grammar(m1_grammar, m1_chords):
    chords = copy.deepcopy(m1_chords)
    chords.removeByNotOfClass([chord.Chord])
    elements = stream.Voice()
    curr_offset = 0.0
    prev_element = None

    for grammar_element in m1_grammar.split(' '):
        if not grammar_element:
            continue
        terms, duration = _parse_duration(grammar_element)
        curr_offset += duration

        if terms[0] == 'R':
            rest_note = note.Rest(quarterLength=duration)
            elements.insert(curr_offset, rest_note)
            continue

        last_chord = _last_chord_at_or_before(chords, curr_offset)

        if len(terms) == 2:
            if terms[0] == 'C':
                insert_note = _generate_chord_tone(last_chord)
            elif terms[0] == 'S':
                insert_note = _generate_scale_tone(last_chord)
            else:
                insert_note = _generate_approach_tone(last_chord)
            insert_note.quarterLength = duration
            if insert_note.octave < 4:
                insert_note.octave = 4
            elements.insert(curr_offset, insert_note)
            prev_element = insert_note
            continue

        if prev_element is None:
            raise ValueError('Interval token %r appears before any generated note' % grammar_element)
        if len(terms) < 4:
            raise ValueError('Malformed interval token %r: expected TYPE,DURATION,<UPPER,LOWER>' % grammar_element)

        interval1 = interval.Interval(terms[2].replace('<', ''))
        interval2 = interval.Interval(terms[3].replace('>', ''))
        if interval1.cents > interval2.cents:
            upper_interval, lower_interval = interval1, interval2
        else:
            upper_interval, lower_interval = interval2, interval1
        low_pitch = interval.transposePitch(prev_element.pitch, lower_interval)
        high_pitch = interval.transposePitch(prev_element.pitch, upper_interval)
        candidates = _candidate_notes(low_pitch, high_pitch)

        if terms[0] == 'C':
            relevant = [n for n in candidates if _is_chord_tone(last_chord, n)]
        elif terms[0] == 'S':
            relevant = [n for n in candidates if _is_scale_tone(last_chord, n)]
        else:
            relevant = [n for n in candidates if _is_approach_tone(last_chord, n)]

        insert_note = _pick_from_candidates(relevant, prev_element)
        if insert_note.octave < 3:
            insert_note.octave = 3
        insert_note.quarterLength = duration
        elements.insert(curr_offset, insert_note)
        prev_element = insert_note

    return elements


def _note_at(name, quarter_length, offset):
    n = note.Note(name)
    n.quarterLength = quarter_length
    n.offset = offset
    return n


def _rest_at(quarter_length, offset):
    r = note.Rest(quarterLength=quarter_length)
    r.offset = offset
    return r


def build_synthetic_voices():
    chords = stream.Voice()
    c_major = chord.Chord(['C4', 'E4', 'G4'])
    c_major.quarterLength = 2.0
    g_major = chord.Chord(['G3', 'B3', 'D4'])
    g_major.quarterLength = 2.0
    chords.insert(0.0, c_major)
    chords.insert(2.0, g_major)

    melody = stream.Voice()
    for offset, element in [
            (0.0, _note_at('C4', 0.250, 0.0)),   # chord tone
            (0.25, _note_at('D4', 0.125, 0.25)), # scale tone
            (0.375, _rest_at(0.125, 0.375)),     # rest
            (0.5, _note_at('C#4', 0.250, 0.5)),  # approach tone to C
            (0.75, _note_at('A#3', 0.250, 0.75)),# arbitrary/catch-all
            (2.0, _note_at('D4', 0.250, 2.0)),   # chord tone after chord change
    ]:
        melody.insert(offset, element)
    return melody, chords


def _as_signal_items(items):
    signals = []
    for item in items:
        kind = 'Note' if isinstance(item, note.Note) else 'Rest' if isinstance(item, note.Rest) else item.__class__.__name__
        signals.append({
            'type': kind,
            'offset': round(float(item.offset), 3),
            'quarterLength': round(float(item.quarterLength), 3),
        })
    return signals


def _make_prune_fixture(generated_items):
    notes = [_copy_element_preserve_offset(i) for i in generated_items if isinstance(i, note.Note)]
    if not notes:
        return []
    duplicate = _copy_element_preserve_offset(notes[0])
    duplicate.offset = notes[0].offset + 0.125
    return [notes[0], duplicate] + notes[1:]


def _make_cleanup_fixture():
    first = _note_at('C4', 0.0, 0.0)
    duplicate_same_offset = _note_at('E4', 0.250, 0.0)
    next_note = _note_at('D4', 0.250, 0.250)
    return [first, duplicate_same_offset, next_note]


def run_smoke(seed):
    random.seed(seed)
    melody, chords = build_synthetic_voices()
    raw_grammar = parse_melody(melody, chords)
    token_types = [tok.split(',')[0] for tok in raw_grammar.split(' ') if tok]
    pruned_grammar = prune_grammar(raw_grammar)
    roundtrip_voice = unparse_grammar(pruned_grammar, chords)
    generated_items = list(roundtrip_voice)
    pruned_items = prune_notes(generated_items)
    cleaned_items = clean_up_notes(pruned_items)

    prune_fixture = _make_prune_fixture(generated_items)
    prune_fixture_after = prune_notes(prune_fixture)
    cleanup_fixture = _make_cleanup_fixture()
    cleanup_after = clean_up_notes(cleanup_fixture)

    checks = {
        'has_note': any(isinstance(i, note.Note) for i in cleaned_items),
        'has_rest': any(isinstance(i, note.Rest) for i in cleaned_items),
        'all_cleaned_lengths_positive': all(float(i.quarterLength) > 0.0 for i in cleaned_items),
        'prune_fixture_removed_duplicate': len(prune_fixture_after) == max(len(prune_fixture) - 1, 0),
        'cleanup_fixture_removed_same_offset_note': len(cleanup_after) == 2,
        'cleanup_fixture_fixed_zero_length': float(cleanup_after[0].quarterLength) == 0.250,
    }
    checks['ok'] = all(checks.values())

    return {
        'seed': seed,
        'grammar': {
            'raw': raw_grammar,
            'pruned': pruned_grammar,
            'token_count': len(token_types),
            'token_types': token_types,
            'has_interval_tokens': any(len(tok.split(',')) > 2 for tok in raw_grammar.split(' ') if tok),
        },
        'roundtrip': {
            'generated_count': len(generated_items),
            'after_prune_notes_count': len(pruned_items),
            'after_clean_up_count': len(cleaned_items),
            'signals': _as_signal_items(cleaned_items),
        },
        'qa_fixtures': {
            'prune_notes_before': len(prune_fixture),
            'prune_notes_after': len(prune_fixture_after),
            'clean_up_notes_before': len(cleanup_fixture),
            'clean_up_notes_after': len(cleanup_after),
        },
        'checks': checks,
    }


def print_text(summary):
    print('deepjazz grammar/QA smoke')
    print('seed: %s' % summary['seed'])
    print('raw grammar: %s' % summary['grammar']['raw'])
    print('pruned grammar: %s' % summary['grammar']['pruned'])
    print('token types: %s' % ' '.join(summary['grammar']['token_types']))
    print('generated elements after cleanup: %s' % summary['roundtrip']['after_clean_up_count'])
    print('structural signals:')
    for signal in summary['roundtrip']['signals']:
        print('  - {type} offset={offset:.3f} ql={quarterLength:.3f}'.format(**signal))
    print('qa fixture counts: prune %s->%s, cleanup %s->%s' % (
        summary['qa_fixtures']['prune_notes_before'],
        summary['qa_fixtures']['prune_notes_after'],
        summary['qa_fixtures']['clean_up_notes_before'],
        summary['qa_fixtures']['clean_up_notes_after'],
    ))
    print('ok: %s' % summary['checks']['ok'])


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Run a tiny self-contained deepjazz grammar/QA smoke check using music21 only.'
    )
    parser.add_argument('--seed', type=int, default=7,
                        help='Random seed for deterministic debugging output. Default: 7.')
    parser.add_argument('--json', action='store_true', dest='as_json',
                        help='Print a JSON summary instead of text.')
    args = parser.parse_args(argv)

    try:
        summary = run_smoke(args.seed)
    except Exception as exc:  # pragma: no cover - used for CLI diagnostics
        if args.as_json:
            print(json.dumps({'ok': False, 'error': str(exc)}, sort_keys=True))
        else:
            print('ERROR: %s' % exc, file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    return 0 if summary['checks']['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
