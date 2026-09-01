from dataclasses import dataclass

@dataclass(frozen=True)
class RawExample:
    text: str
    label: str
    domain: str

def build_stream(domains):
    stream=[]
    audit=[]
    index=0
    for domain, examples in domains:
        for ex in examples:
            text,label=ex
            stream.append({'id': index, 'text': text, 'label': label})
            audit.append({'id': index, 'domain': domain})
            index += 1
    return stream, audit

def retention_split(stream, audit, domain):
    ids={row['id'] for row in audit if row['domain']==domain}
    return [row for row in stream if row['id'] in ids]
