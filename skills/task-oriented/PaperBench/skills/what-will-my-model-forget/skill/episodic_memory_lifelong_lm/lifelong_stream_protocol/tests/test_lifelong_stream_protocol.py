import sys
sys.path.insert(0, 'scripts')
from stream_protocol import build_stream, retention_split
stream,audit=build_stream([('a',[('old token','0')]),('b',[('new token','1')])])
assert 'domain' not in stream[0]
assert retention_split(stream,audit,'a')[0]['text']=='old token'
