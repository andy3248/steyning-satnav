"""Interrupted national-download ranges must resume without duplicating bytes."""
import contextlib,http.client,io,unittest
from unittest.mock import patch
from fetch_addresses import RangeStream

class Response:
 def __init__(self,offset,parts,status=206):self.status=status;self.headers={'Content-Range':f'bytes {offset}-4/5'};self.parts=iter(parts)
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,n):
  p=next(self.parts,b'')
  if isinstance(p,Exception):raise p
  return p

class FetchTests(unittest.TestCase):
 def test_partial_range_resumes_at_exact_byte(self):
  stream=RangeStream.__new__(RangeStream);stream.size=5;stream.chunk=5;stream.url='https://example.test/source.zip';ranges=[]
  responses=iter([Response(0,[b'ab',http.client.IncompleteRead(b'c',2)]),Response(3,[b'de'])])
  def open_request(req,timeout):ranges.append(req.get_header('Range'));return next(responses)
  with patch('urllib.request.urlopen',open_request),patch('time.sleep'),contextlib.redirect_stdout(io.StringIO()):data=stream.fetch(0)
  self.assertEqual(data,b'abcde');self.assertEqual(ranges,['bytes=0-4','bytes=3-4'])
 def test_ignored_range_is_rejected(self):
  stream=RangeStream.__new__(RangeStream);stream.size=5;stream.chunk=5;stream.url='https://example.test/source.zip'
  with patch('urllib.request.urlopen',return_value=Response(0,[b'abcde'],status=200)):
   with self.assertRaises(ValueError):stream.fetch(0)

if __name__=='__main__':unittest.main()
