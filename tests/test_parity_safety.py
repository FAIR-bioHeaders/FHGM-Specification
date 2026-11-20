"""Source-bound parity refusals; all synthetic mutations stay outside frozen trees."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_header_parity as parity


class ParitySafetyTests(unittest.TestCase):
    def record(self):
        return {'source': {'repository':'FAIR-bioHeaders/FAIR-bioHeaders-Specification', 'commit': '0' * 40}, 'copied': [{
            'local': 'header/sample.txt', 'upstream': 'sample.txt',
            'size': 2, 'sha256': hashlib.sha256(b'ok').hexdigest()}], 'imports': []}

    def test_malformed_and_escaping_records_refuse_before_file_reads(self):
        cases = []
        item = self.record(); item['copied'][0].pop('upstream'); cases.append(item)
        item = self.record(); item['copied'][0]['local'] = '../outside'; cases.append(item)
        item = self.record(); item['copied'][0]['local'] = '/outside'; cases.append(item)
        item = self.record(); item['copied'][0]['local'] = 'outside'; cases.append(item)
        item = self.record(); item['copied'][0]['sha256'] = None; cases.append(item)
        item = self.record(); item['copied'][0]['sha256'] = int('1'*64); cases.append(item)
        item = self.record(); item['source']['commit'] = int('1'*40); cases.append(item)
        item = self.record(); item['source'].pop('repository'); cases.append(item)
        item = self.record(); item['copied'][0]['size'] = True; cases.append(item)
        item = self.record(); item['copied'] = []; cases.append(item)
        item = self.record(); item['copied'] *= 2; cases.append(item)
        with tempfile.TemporaryDirectory() as d:
            record = Path(d) / 'provenance.json'
            for item in cases:
                record.write_text(json.dumps(item))
                with self.subTest(item=item), mock.patch.object(parity, 'PROVENANCE', record):
                    with self.assertRaisesRegex(SystemExit, 'error:'):
                        parity.load_provenance()
        self.assertEqual(parity.validate_provenance(self.record()), self.record())

    def test_symlink_bytes_do_not_count_as_a_regular_copy(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / 'header').mkdir()
            (root / 'actual').write_bytes(b'ok')
            (root / 'header/sample.txt').symlink_to(root / 'actual')
            with mock.patch.object(parity, 'ROOT', root):
                errors, _ = parity.check_local(self.record())
            self.assertTrue(any('symlink' in error for error in errors))

    def test_unlisted_subtree_is_not_hidden_outside_old_strict_directories(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); target = root / 'header/extra/hidden.txt'
            target.parent.mkdir(parents=True); target.write_text('unclassified')
            with mock.patch.object(parity, 'ROOT', root):
                errors = parity.check_extras({})
            self.assertTrue(any('header/extra/hidden.txt' in error for error in errors))

    def test_git_replacement_cannot_supply_different_pinned_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            def git(*args):
                return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null',
                    '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    '-C', str(root), *args], stderr=subprocess.DEVNULL)
            git('init', '--quiet')
            (root / 'sample.txt').write_bytes(b'original')
            git('add', 'sample.txt'); git('commit', '--quiet', '--no-gpg-sign', '-m', 'original')
            original = git('rev-parse', 'HEAD').decode().strip()
            (root / 'sample.txt').write_bytes(b'replacement')
            git('commit', '--quiet', '--no-gpg-sign', '-am', 'replacement')
            replacement = git('rev-parse', 'HEAD').decode().strip()
            git('replace', original, replacement)
            self.assertEqual(git('show', original + ':sample.txt'), b'replacement')
            self.assertEqual(parity.git_show(root, original, 'sample.txt'), b'original')
