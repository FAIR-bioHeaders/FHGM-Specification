# SPDX-License-Identifier: MPL-2.0
"""Test the local declaration adapter and immutable implementation guard."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fhgm_reference_adapter', ROOT / 'scripts/reference_audit.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
RECORDS = ('header/provenance.json', 'development/model/base-schemas.json',
           'development/conformance/provenance.json')


class Declarations(unittest.TestCase):
    def test_normalization_preserves_every_declared_header_import_and_carrier(self):
        table = adapter.inventory()
        header = json.loads((ROOT / RECORDS[0]).read_text())
        row = next(r for r in table['references'] if r['id'] == 'fhgm-header-copy')
        self.assertEqual([(f['upstream'], f['local'], f['sha256']) for f in header['copied']],
                         [(f['path'], f['local'], f['sha256']) for f in row['files']])
        self.assertEqual(header['source']['ref'], row['revision'])
        self.assertEqual(header['source']['commit'], row['commit'])
        self.assertEqual('released', row['materialStatus'])
        imported = [r for r in table['references'] if r['id'].startswith('fhgm-header-import:')]
        self.assertEqual({f['upstream'] for f in header['imports']}, {r['files'][0]['path'] for r in imported})
        self.assertEqual([], table['coverageGaps'])
        bases = json.loads((ROOT / RECORDS[1]).read_text())['bases']
        registry = [r for r in table['references'] if r['id'].startswith('fhgm-registry-base:')]
        expected_bases = {(b['repository'], b['ref'], b['commit'], b['path'], b['sha256']) for b in bases}
        self.assertEqual(expected_bases, {(r['repository'], r['revision'], r['commit'],
            r['files'][0]['path'], r['files'][0]['sha256']) for r in registry})
        self.assertEqual({'fhgm-conformance-base:baseSchema', 'fhgm-conformance-base:matrixBaseSchema'},
            {r['id'] for r in table['references'] if r['id'].startswith('fhgm-conformance-base:')})
        self.assertTrue(all(r['revisionKind'] == 'tag' for r in table['references']))

    def test_disagreeing_duplicate_claim_is_retained_and_reported_never_repaired(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in RECORDS:
                dest = root / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, dest)
            file = root / RECORDS[2]
            data = json.loads(file.read_text())
            digest = data['matrixBaseSchema']['sha256']
            changed = ('0' if digest[0] != '0' else '1') + digest[1:]
            data['matrixBaseSchema']['sha256'] = changed
            file.write_text(json.dumps(data))
            before = {r: (root / r).read_bytes() for r in RECORDS}
            table = adapter.inventory(root)
            claim = next(r for r in table['references'] if r['id'] == 'fhgm-conformance-base:matrixBaseSchema')
            self.assertEqual(changed, claim['files'][0]['sha256'])
            self.assertTrue(table['coverageGaps'])
            self.assertEqual(before, {r: (root / r).read_bytes() for r in RECORDS})

    def test_unverified_checker_cannot_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'checker'
            source.mkdir()
            marker = root / 'EXECUTED'
            script = source / 'check.py'
            script.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("bad")\n')
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(source), '-c', 'commit.gpgsign=false',
                '-c', 'user.name=Checker guard fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'fixture'], check=True)
            commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
            (root / 'references').mkdir()
            pinfile = root / 'references/checker.json'
            pin = {'commit': commit, 'path': 'check.py', 'sha256': '0' * 64}
            pinfile.write_text(json.dumps(pin))
            with self.assertRaisesRegex(ValueError, 'digest'):
                adapter.run(source, root)
            self.assertFalse(marker.exists())
            pin['sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
            pin['commit'] = '0' * 40
            pinfile.write_text(json.dumps(pin))
            with self.assertRaisesRegex(ValueError, 'HEAD'):
                adapter.run(source, root)
            self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
