#!/usr/bin/env python
"""Safely inspect a MIDI file for deepjazz-style preprocessing assumptions.

This helper is bundled with the generated skill. It does not import the
original deepjazz source, train a model, play audio, write MIDI, or require a
specific checkout layout.

Example:
    python inspect_midi_structure.py --midi-file song.mid \
        --melody-part 5 --accompaniment-parts 0,1,6,7 \
        --start-offset 476 --end-offset 548
"""
from __future__ import print_function

import argparse
import json
import sys


def _fail(message, as_json=False):
    if as_json:
        print(json.dumps({'status': 'error', 'errors': [message]}, indent=2, sort_keys=True))
    else:
        print('ERROR: %s' % message, file=sys.stderr)
    return 2


def _parse_int_list(text):
    values = []
    if not text:
        return values
    for item in text.split(','):
        item = item.strip()
        if item:
            values.append(int(item))
    return values


def _iter_recurse(obj):
    try:
        return obj.recurse()
    except Exception:
        try:
            return obj.flat
        except Exception:
            return obj


def _count_by_class(part, music21_modules):
    note_mod, chord_mod, stream_mod = music21_modules
    counts = {
        'notes': 0,
        'rests': 0,
        'chords': 0,
        'voices': 0,
        'elements': 0,
        'min_offset': None,
        'max_offset': None,
    }
    try:
        voices = part.getElementsByClass(stream_mod.Voice)
        counts['voices'] = len(voices)
    except Exception:
        counts['voices'] = 0

    for element in _iter_recurse(part):
        counts['elements'] += 1
        offset = getattr(element, 'offset', None)
        if isinstance(offset, (int, float)):
            if counts['min_offset'] is None or offset < counts['min_offset']:
                counts['min_offset'] = float(offset)
            if counts['max_offset'] is None or offset > counts['max_offset']:
                counts['max_offset'] = float(offset)
        if isinstance(element, note_mod.Note):
            counts['notes'] += 1
        elif isinstance(element, note_mod.Rest):
            counts['rests'] += 1
        elif isinstance(element, chord_mod.Chord):
            counts['chords'] += 1
    return counts


def _count_window(part, start_offset, end_offset, music21_modules):
    note_mod, chord_mod, _stream_mod = music21_modules
    counts = {'notes': 0, 'rests': 0, 'chords': 0, 'elements': 0}
    for element in _iter_recurse(part):
        offset = getattr(element, 'offset', None)
        if not isinstance(offset, (int, float)):
            continue
        if offset < start_offset or offset > end_offset:
            continue
        counts['elements'] += 1
        if isinstance(element, note_mod.Note):
            counts['notes'] += 1
        elif isinstance(element, note_mod.Rest):
            counts['rests'] += 1
        elif isinstance(element, chord_mod.Chord):
            counts['chords'] += 1
    return counts


def inspect_midi(args):
    try:
        from music21 import converter, note, chord, stream
    except Exception as exc:
        return {
            'status': 'error',
            'errors': ['music21 import failed: %s: %s' % (exc.__class__.__name__, exc)],
            'warnings': [],
        }

    try:
        score = converter.parse(args.midi_file)
    except Exception as exc:
        return {
            'status': 'error',
            'errors': ['music21 converter.parse failed: %s: %s' % (exc.__class__.__name__, exc)],
            'warnings': [],
        }

    parts = list(score)
    modules = (note, chord, stream)
    part_summaries = []
    for index, part in enumerate(parts):
        summary = _count_by_class(part, modules)
        summary['index'] = index
        summary['window'] = _count_window(part, args.start_offset, args.end_offset, modules)
        part_summaries.append(summary)

    warnings = []
    selected = {
        'melody_part': args.melody_part,
        'accompaniment_parts': args.accompaniment_parts,
        'start_offset': args.start_offset,
        'end_offset': args.end_offset,
    }

    if args.melody_part < 0 or args.melody_part >= len(parts):
        warnings.append('melody part index %s is outside available part range 0..%s' % (args.melody_part, max(len(parts) - 1, -1)))
    else:
        melody = part_summaries[args.melody_part]
        if melody['voices'] < 1:
            warnings.append('selected melody part has no music21 Voice elements; legacy parser expects voices')
        if melody['window']['notes'] + melody['window']['rests'] == 0:
            warnings.append('selected melody part has no notes/rests in requested window')

    chord_total = 0
    for part_index in args.accompaniment_parts:
        if part_index < 0 or part_index >= len(parts):
            warnings.append('accompaniment part index %s is outside available part range' % part_index)
            continue
        chord_total += part_summaries[part_index]['window']['chords']
    if args.accompaniment_parts and chord_total == 0:
        warnings.append('selected accompaniment parts have no chord objects in requested window')

    if args.end_offset <= args.start_offset:
        warnings.append('end offset must be greater than start offset')

    return {
        'status': 'ok' if not warnings else 'warn',
        'midi_file': args.midi_file,
        'part_count': len(parts),
        'selected': selected,
        'parts': part_summaries,
        'warnings': warnings,
        'errors': [],
    }


def _print_human(report):
    print('status: %s' % report.get('status'))
    if report.get('errors'):
        print('errors:')
        for item in report['errors']:
            print('  - %s' % item)
        return
    print('part_count: %s' % report.get('part_count'))
    selected = report.get('selected', {})
    print('selected: melody_part=%s accompaniment_parts=%s window=[%s,%s]' % (
        selected.get('melody_part'), selected.get('accompaniment_parts'),
        selected.get('start_offset'), selected.get('end_offset')))
    print('parts:')
    for part in report.get('parts', []):
        print('  part {index}: notes={notes} rests={rests} chords={chords} voices={voices} offsets={min_offset}..{max_offset} window_notes={wn} window_chords={wc}'.format(
            index=part['index'], notes=part['notes'], rests=part['rests'],
            chords=part['chords'], voices=part['voices'],
            min_offset=part['min_offset'], max_offset=part['max_offset'],
            wn=part['window']['notes'], wc=part['window']['chords']))
    if report.get('warnings'):
        print('warnings:')
        for item in report['warnings']:
            print('  - %s' % item)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Inspect MIDI structure for deepjazz preprocessing assumptions without training or playback.')
    parser.add_argument('--midi-file', required=True, help='MIDI file to inspect')
    parser.add_argument('--melody-part', type=int, default=5, help='candidate melody part index; legacy default is 5')
    parser.add_argument('--accompaniment-parts', default='0,1,6,7', help='comma-separated accompaniment part indices; legacy default is 0,1,6,7')
    parser.add_argument('--start-offset', type=float, default=476.0, help='solo/window start offset; legacy default is 476')
    parser.add_argument('--end-offset', type=float, default=548.0, help='solo/window end offset; legacy default is 548')
    parser.add_argument('--json', action='store_true', help='emit JSON report')
    args = parser.parse_args(argv)
    try:
        args.accompaniment_parts = _parse_int_list(args.accompaniment_parts)
    except Exception as exc:
        return _fail('invalid --accompaniment-parts: %s' % exc, args.json)
    report = inspect_midi(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report.get('status') in ('ok', 'warn') else 2


if __name__ == '__main__':
    sys.exit(main())
