
import json
from collections import Counter

def build_stream(samples, batch_size=1):
    if batch_size < 1:
        raise ValueError('batch_size must be positive')
    stream = []
    for index, sample in enumerate(samples):
        item = dict(sample)
        item['index'] = index
        item['batch_id'] = index // batch_size
        stream.append(item)
    domains = [s.get('domain','unknown') for s in stream]
    labels = [s.get('label') for s in stream]
    return {'samples': stream, 'batch_size': batch_size, 'domain_counts': dict(Counter(domains)), 'label_counts': dict(Counter(labels)), 'is_mixed_domain': len(set(domains)) > 1, 'is_label_imbalanced': len(set(Counter(labels).values())) > 1}

def deterministic_proxy_stream():
    samples = []
    domains = ['gaussian_noise','shot_noise','fog']
    labels = [0,0,0,0,0,1,0,0,2,0,1,0]
    for i, label in enumerate(labels):
        samples.append({'domain': domains[i % len(domains)], 'label': label, 'feature': [1.0 + 0.1*i, -0.5 + 0.03*i]})
    return build_stream(samples, batch_size=1)

def main():
    print(json.dumps(deterministic_proxy_stream(), indent=2))
if __name__ == '__main__':
    main()
