import argparse, json

def initial_params(dim):
    return {'w_x': [0.0] * dim, 'w_t': [0.0] * dim, 'b': [0.0] * dim}

def predict(record, params):
    return [params['w_x'][i] * record['xt'][i] + params['w_t'][i] * record['t'] + params['b'][i] for i in range(len(record['xt']))]

def loss(records, params):
    total = 0.0; count = 0
    for record in records:
        pred = predict(record, params)
        for p, y in zip(pred, record['target_velocity']):
            total += (p - y) ** 2; count += 1
    return total / max(count, 1)

def train(records, params=None, lr=0.05, steps=1):
    if not records:
        raise ValueError('records are required')
    dim = len(records[0]['xt'])
    params = {k: [float(x) for x in v] for k, v in (params or initial_params(dim)).items()}
    before = {k: list(v) for k, v in params.items()}
    loss_before = loss(records, params)
    for _ in range(steps):
        grads = {'w_x': [0.0] * dim, 'w_t': [0.0] * dim, 'b': [0.0] * dim}
        denom = len(records) * dim
        for record in records:
            pred = predict(record, params)
            for i, (p, y) in enumerate(zip(pred, record['target_velocity'])):
                g = 2.0 * (p - y) / denom
                grads['w_x'][i] += g * record['xt'][i]
                grads['w_t'][i] += g * record['t']
                grads['b'][i] += g
        for key in params:
            for i in range(dim):
                params[key][i] -= lr * grads[key][i]
    loss_after = loss(records, params)
    return {'params_before': before, 'params_after': params, 'loss_before': loss_before, 'loss_after': loss_after, 'optimizer_state_changed': before != params}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--input', required=True); parser.add_argument('--output', required=True); parser.add_argument('--lr', type=float, default=0.05); parser.add_argument('--steps', type=int, default=1)
    args = parser.parse_args(); data = json.load(open(args.input, encoding='utf-8'))
    json.dump(train(data['records'], data.get('params'), args.lr, args.steps), open(args.output, 'w', encoding='utf-8'), indent=2)

if __name__ == '__main__':
    main()
