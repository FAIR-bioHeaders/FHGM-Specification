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

    def test_missing_metadata_and_floating_reference_are_preserved_for_the_engine(self):
        for field in ('ref', 'commit', 'path', 'sha256'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for relative in RECORDS:
                    dest = root / relative
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / relative, dest)
                file = root / RECORDS[1]
                record = json.loads(file.read_text())
                record['bases'][0].pop(field)
                file.write_text(json.dumps(record))
                row = next(r for r in adapter.inventory(root)['references']
                           if r['id'].startswith('fhgm-registry-base:'))
                value = row.get({'ref': 'revision', 'commit': 'commit'}[field]) if field in ('ref', 'commit') else row['files'][0].get(field)
                self.assertIsNone(value)
                if field == 'ref':
                    record['bases'][0]['ref'] = 'main'
                    file.write_text(json.dumps(record))
                    row = next(r for r in adapter.inventory(root)['references']
                               if r['id'] == 'fhgm-registry-base:main')
                    self.assertEqual('main', row['revision'])
                    self.assertEqual('branch', row['revisionKind'])

    def test_unverified_checker_cannot_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'checker'
            source.mkdir()
            marker = root / 'EXECUTED'
            (source / 'scripts').mkdir()
            script = source / 'scripts/check_references.py'
            script.write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("bad")\n')
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(source), '-c', 'commit.gpgsign=false',
                '-c', 'user.name=Checker guard fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'fixture'], check=True)
            commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
            (root / 'references').mkdir()
            pinfile = root / 'references/checker.json'
            pin = {'repository': 'FAIR-bioHeaders/FAIR-bioHeaders-Specification',
                   'commit': commit, 'path': 'scripts/check_references.py', 'sha256': '0' * 64}
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

    def test_joint_worktree_digest_tamper_and_invalid_source_metadata_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            (source / 'scripts').mkdir(parents=True)
            script = source / 'scripts/check_references.py'
            script.write_text('print("original")\n')
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(source), '-c', 'commit.gpgsign=false',
                '-c', 'user.name=Immutable fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'fixture'], check=True)
            commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
            pin = {'repository': 'FAIR-bioHeaders/FAIR-bioHeaders-Specification', 'commit': commit,
                   'path': 'scripts/check_references.py', 'sha256': hashlib.sha256(script.read_bytes()).hexdigest()}
            (root / 'references').mkdir()
            file = root / 'references/checker.json'
            file.write_text(json.dumps(pin))
            self.assertEqual(script.read_bytes(), adapter.verified_checker(source, root))
            for key, value in (('repository', 'example/other'), ('commit', 'main'),
                    ('path', '../outside.py'), ('path', '/tmp/outside.py'),
                    ('path', 'scripts/other.py')):
                bad = dict(pin, **{key: value})
                file.write_text(json.dumps(bad))
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    adapter.verified_checker(source, root)
            script.write_text('print("tampered")\n')
            bad = dict(pin, sha256=hashlib.sha256(script.read_bytes()).hexdigest())
            file.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, 'immutable Git blob'):
                adapter.verified_checker(source, root)
            script.unlink()
            replacement = root / 'replacement.py'
            replacement.write_text('print("original")\n')
            script.symlink_to(replacement)
            file.write_text(json.dumps(pin))
            with self.assertRaisesRegex(ValueError, 'Symlink'):
                adapter.verified_checker(source, root)

    def test_isolated_execution_ignores_unverified_neighbor_stdlib_shadow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / 'SHADOW_EXECUTED'
            (root / 'json.py').write_text('from pathlib import Path\nPath(' + repr(str(marker))
                + ').write_text("shadow")\nraise RuntimeError("unverified shadow")\n')
            script = root / 'checker.py'
            script.write_text('import json\nprint(json.dumps({"advisory": True, "wrote": []}))\n')
            negative = subprocess.run([__import__('sys').executable, str(script)],
                                      capture_output=True, text=True)
            self.assertNotEqual(0, negative.returncode)
            self.assertTrue(marker.exists())
            marker.unlink()
            report = adapter.execute(script.read_bytes(), {'inventoryVersion': 1, 'references': []}, root, [])
            self.assertEqual({'advisory': True, 'wrote': []}, report)
            self.assertFalse(marker.exists())

    def test_replacement_ref_cannot_substitute_a_pinned_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            (source / 'scripts').mkdir(parents=True)
            script = source / 'scripts/check_references.py'
            script.write_bytes(b'print("original")\n')
            def git(*args):
                return subprocess.check_output(['git', '-C', str(source), *args], stderr=subprocess.DEVNULL)
            git('init', '-q')
            def commit():
                git('add', '.')
                git('-c', 'commit.gpgsign=false', '-c', 'user.name=Replacement fixture',
                    '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
                return git('rev-parse', 'HEAD').decode().strip()
            original = commit()
            script.write_bytes(b'print("replacement")\n')
            replacement = commit()
            git('checkout', '-q', original)
            git('replace', original, replacement)
            script.write_bytes(b'print("replacement")\n')
            self.assertEqual(script.read_bytes(), git('show', original + ':scripts/check_references.py'))
            (root / 'references').mkdir()
            (root / 'references/checker.json').write_text(json.dumps({
                'repository': 'FAIR-bioHeaders/FAIR-bioHeaders-Specification',
                'commit': original, 'path': 'scripts/check_references.py',
                'sha256': hashlib.sha256(script.read_bytes()).hexdigest()}))
            with self.assertRaisesRegex(ValueError, 'immutable Git blob'):
                adapter.verified_checker(source, root)

    def test_execution_uses_verified_bytes_after_source_is_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = root / 'source'
            (checkout / 'scripts').mkdir(parents=True)
            source = checkout / 'scripts/check_references.py'
            source.write_bytes(b'import json\nprint(json.dumps({"advisory":True,"wrote":[]}))\n')
            subprocess.run(['git', 'init', '-q', str(checkout)], check=True)
            subprocess.run(['git', '-C', str(checkout), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(checkout), '-c', 'commit.gpgsign=false',
                '-c', 'user.name=Snapshot fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'fixture'], check=True)
            commit = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
            (root / 'references').mkdir()
            (root / 'references/checker.json').write_text(json.dumps({
                'repository': 'FAIR-bioHeaders/FAIR-bioHeaders-Specification', 'commit': commit,
                'path': 'scripts/check_references.py', 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}))
            verified = adapter.verified_checker(checkout, root)
            source.write_text('raise RuntimeError("unverified replacement must not execute")\n')
            self.assertEqual({'advisory': True, 'wrote': []},
                adapter.execute(verified, {'inventoryVersion': 1, 'references': []}, root, []))


if __name__ == '__main__':
    unittest.main()
