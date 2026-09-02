import argparse, json, math

def _pred(z, t, params):
    return [params['w_x'][i] * z[i] + params['w_t'][i] * t + params['b'][i] for i in range(len(z))]

def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def simulate(z0_samples, params, steps=4):
    outputs = []
    for start in z0_samples:
        z = [float(x) for x in start]
        path_length = 0.0
        for step in range(steps):
            t = step / float(steps)
            v = _pred(z, t, params)
            new_z = [x + v_i / steps for x, v_i in zip(z, v)]
            path_length += _dist(z, new_z)
            z = new_z
        direct = _dist(start, z)
        outputs.append({'z0': [float(x) for x in start], 'z1': z, 'path_length': path_length, 'direct_distance': direct, 'straightness_ratio': path_length / max(direct, 1e-12), 'squared_cost': direct ** 2})
    mean_ratio = sum(item['straightness_ratio'] for item in outputs) / len(outputs)
    mean_cost = sum(item['squared_cost'] for item in outputs) / len(outputs)
    return {'paths': outputs, 'mean_straightness_ratio': mean_ratio, 'mean_squared_cost': mean_cost}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--input', required=True); parser.add_argument('--output', required=True); parser.add_argument('--steps', type=int, default=4)
    args = parser.parse_args(); data = json.load(open(args.input, encoding='utf-8'))
    json.dump(simulate(data['z0'], data['params'], args.steps), open(args.output, 'w', encoding='utf-8'), indent=2)

if __name__ == '__main__':
    main()
