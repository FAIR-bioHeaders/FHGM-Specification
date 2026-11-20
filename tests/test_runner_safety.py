"""Regeneration identity and advisory fetch refusals; no pinned artifacts are rewritten."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'development/conformance'))
import run_conformance as runner


class RunnerSafetyTests(unittest.TestCase):
    def test_generator_identity_disambiguates_equal_basenames(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); vectors = []; generators = {}
            for name, value in [('first', b'first'), ('second', b'second')]:
                script = root / (name + '.py')
                script.write_text('from pathlib import Path\nimport sys\n'
                    f'Path(sys.argv[1], "same.fhgff3.gff3").write_bytes({value!r})\n')
                expected = root / name / 'same.fhgff3.gff3'
                expected.parent.mkdir(); expected.write_bytes(value)
                generators[name] = script
                vectors.append({'id':name, 'generator':name, 'file':str(expected)})
            with mock.patch.object(runner, 'GENERATORS', generators), \
                    mock.patch.object(runner, 'path_of', side_effect=lambda v: Path(v['file'])):
                self.assertEqual(runner.regenerate(vectors), {'first':True, 'second':True})

    def test_same_generator_ambiguous_output_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); script = root / 'generator.py'
            script.write_text('from pathlib import Path\nimport sys\n'
                'for folder in ("a","b"):\n'
                ' p=Path(sys.argv[1],folder);p.mkdir();(p/"same.fhgff3.gff3").write_bytes(b"x")\n')
            with mock.patch.object(runner, 'GENERATORS', {'one':script}):
                with self.assertRaisesRegex(runner.Failure, 'ambiguous generated filename'):
                    runner.regenerate([{'id':'one','generator':'one','file':'same.fhgff3.gff3'}])

    def pin(self, url='https://raw.githubusercontent.com/org/repo/main/pin.json'):
        return {'name':'test pin', 'tracks':'model.json', 'url':url,
                'pointer':'/pin', 'field':'sha256'}

    def test_unapproved_urls_refuse_before_outbound_request(self):
        for url in ['file:///etc/passwd','http://api.github.com/pin',
                    'https://example.org/pin','https://user@api.github.com/pin']:
            with self.subTest(url=url), mock.patch.object(runner, 'open_pin_url') as fetch:
                problems = runner.check_downstream_pins({'downstreamPins':[self.pin(url)]})
                self.assertTrue(problems); fetch.assert_not_called()

    def test_redirect_is_checked_before_following(self):
        captured = []
        def opener(handler):
            captured.append(handler)
            return SimpleNamespace(open=lambda *a,**kw: None)
        with mock.patch('urllib.request.build_opener', side_effect=opener):
            runner.open_pin_url(self.pin()['url'])
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            captured[0].redirect_request(None, None, 302, 'redirect', {}, 'http://127.0.0.1/private')

    def test_missing_remote_measurement_is_not_reported_as_drift_or_freshness(self):
        class Response(io.BytesIO):
            def geturl(self): return 'https://raw.githubusercontent.com/org/repo/main/pin.json'
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / 'model.json').write_bytes(b'{}')
            for remote, valid in [(None,False), (hashlib.sha256(b'{}').hexdigest(),True)]:
                response = Response(json.dumps({'pin':{'sha256':remote}}).encode())
                output = io.StringIO()
                with mock.patch.object(runner, 'REPO', root), \
                        mock.patch.object(runner, 'open_pin_url', return_value=response), \
                        contextlib.redirect_stdout(output):
                    problems = runner.check_downstream_pins({'downstreamPins':[self.pin()]})
                self.assertEqual(not problems, valid)
                if valid: self.assertIn('fresh:', output.getvalue())
                else:
                    self.assertNotIn('fresh:', output.getvalue())
                    self.assertNotIn('STALE:', output.getvalue())
