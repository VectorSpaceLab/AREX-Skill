import argparse, json

def _vec(value):
    if not isinstance(value, list) or not value or not all(isinstance(item, (int, float)) for item in value):
        raise ValueError('sample must be a non-empty numeric vector')
    return [float(item) for item in value]

def build_records(x0_samples, x1_samples, times):
    if len(x0_samples) != len(x1_samples) or len(x0_samples) != len(times):
        raise ValueError('x0, x1, and times must have equal length')
    records = []
    for x0_raw, x1_raw, time_raw in zip(x0_samples, x1_samples, times):
        x0 = _vec(x0_raw); x1 = _vec(x1_raw); time = float(time_raw)
        if len(x0) != len(x1):
            raise ValueError('paired samples must share dimension')
        if not 0.0 <= time <= 1.0:
            raise ValueError('time must be in [0, 1]')
        xt = [(1.0 - time) * a + time * b for a, b in zip(x0, x1)]
        target = [b - a for a, b in zip(x0, x1)]
        records.append({'x0': x0, 'x1': x1, 't': time, 'xt': xt, 'target_velocity': target})
    return records

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = json.load(open(args.input, encoding='utf-8'))
    json.dump({'records': build_records(data['x0'], data['x1'], data['times'])}, open(args.output, 'w', encoding='utf-8'), indent=2)

if __name__ == '__main__':
    main()
