# SPDX-License-Identifier: MPL-2.0
"""Normalize current FHGM declarations and invoke the verified central advisory checker."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = 'FAIR-bioHeaders/FHGM-Specification'
SOURCE_PATTERNS = ['fhgff3_linkml.yml', 'docs/FHGFF3.md', 'examples/fhgff3/*',
                   'conformance/valid/fhgff3-*', 'conformance/invalid/fhgff3-*']
HEADER_EXCLUSIONS = ['header/PROVENANCE.md', 'header/README.md', 'header/conformance/README.md',
                     'header/docs/README.md', 'header/provenance.json']


def load(root, relative):
    return json.loads((root / relative).read_text())


def inventory(root=ROOT):
    """Read declarations, never rewrite them or infer a newer contract pin."""
    header = load(root, 'header/provenance.json')
    bases = load(root, 'development/model/base-schemas.json')['bases']
    suite = load(root, 'development/conformance/provenance.json')
    source = header['source']
    rows = []

    def row(identifier, record, category, repository, revision, commit, files, **extra):
        rows.append({'id': identifier, 'consumer': CONSUMER, 'record': record,
            'class': category, 'repository': repository, 'revision': revision,
            'revisionKind': 'tag', 'commit': commit, 'files': files, **extra})

    row('fhgm-header-copy', 'header/provenance.json', 'copied-tree', source['repository'],
        source['ref'], source['commit'],
        [{'local': f['local'], 'path': f['upstream'], 'sha256': f['sha256']}
         for f in header['copied']], materialStatus='released', sourcePatterns=SOURCE_PATTERNS,
        localTree='header', localExclusions=HEADER_EXCLUSIONS)
    for item in header['imports']:
        category = 'conformance-suite' if item['upstream'] == 'conformance/manifest.json' else 'released-contract'
        row('fhgm-header-import:' + item['upstream'], 'header/provenance.json', category,
            source['repository'], source['ref'], source['commit'],
            [{'local': None, 'path': item['upstream'], 'sha256': item['sha256']}])
    claims = {}
    for base in bases:
        key = (base['repository'], base['ref'], base['commit'], base['path'], base['sha256'])
        claims[base['ref']] = key
        row('fhgm-registry-base:' + base['ref'], 'development/model/base-schemas.json',
            'base-carrier', base['repository'], base['ref'], base['commit'],
            [{'local': None, 'path': base['path'], 'sha256': base['sha256']}])
    gaps = []
    for role in ('baseSchema', 'matrixBaseSchema'):
        base = suite[role]
        key = (base['repository'], base['ref'], base['commit'], base['path'], base['sha256'])
        if claims.get(base['ref']) != key:
            gaps.append('Carrier declaration disagreement: conformance ' + role + ' vs model registry')
        row('fhgm-conformance-base:' + role, 'development/conformance/provenance.json',
            'base-carrier', base['repository'], base['ref'], base['commit'],
            [{'local': None, 'path': base['path'], 'sha256': base['sha256']}])
    return {'inventoryVersion': 1, 'advisory': True, 'consumer': CONSUMER,
            'coverage': 'Current declared external header/import/carrier references; local FHGM draft artifacts are owning material.',
            'declarations': [{'path': relative, 'sha256': hashlib.sha256((root / relative).read_bytes()).hexdigest()}
                             for relative in ('header/provenance.json', 'development/model/base-schemas.json',
                                              'development/conformance/provenance.json')],
            'coverageGaps': gaps, 'references': rows}


def verified_checker(checker_root, root=ROOT):
    pin = load(root, 'references/checker.json')
    if pin.get('repository') != 'FAIR-bioHeaders/FAIR-bioHeaders-Specification':
        raise ValueError('Unexpected central checker repository')
    if not re.fullmatch('[0-9a-f]{40}', pin.get('commit', '')):
        raise ValueError('Central checker requires a full immutable commit')
    relative = pin.get('path', '')
    path = PurePosixPath(relative)
    if (not relative or path.is_absolute() or '..' in path.parts or '\\' in relative
            or path.as_posix() != relative):
        raise ValueError('Unsafe central checker relative path')
    if relative != 'scripts/check_references.py':
        raise ValueError('Unexpected central checker script path')
    if not re.fullmatch('[0-9a-f]{64}', pin.get('sha256', '')):
        raise ValueError('Invalid central checker digest')
    head = subprocess.check_output(['git', '-C', str(checker_root), 'rev-parse', 'HEAD'], text=True).strip()
    if head != pin['commit']:
        raise ValueError('Central checker checkout HEAD differs from immutable implementation pin')
    file = checker_root / relative
    cursor = checker_root
    if cursor.is_symlink():
        raise ValueError('Symlink checker root is not accepted')
    for part in path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError('Symlink checker path is not accepted')
    blob = subprocess.check_output(['git', '-C', str(checker_root), 'show', pin['commit'] + ':' + relative])
    data = file.read_bytes()
    if data != blob:
        raise ValueError('Central checker worktree differs from immutable Git blob')
    if hashlib.sha256(blob).hexdigest() != pin['sha256']:
        raise ValueError('Central checker bytes differ from immutable implementation digest')
    return file


def execute(checker, table, root, checkouts):
    with tempfile.TemporaryDirectory() as directory:
        record = Path(directory) / 'inventory.json'
        record.write_text(json.dumps(table, indent=2) + '\n')
        command = [sys.executable, '-I', str(checker), '--inventory', str(record),
                   '--consumer', CONSUMER, '--consumer-root', str(root)]
        for authority in checkouts:
            command.extend(['--checkout', authority])
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    report = json.loads(result.stdout)
    if report.get('advisory') is not True or report.get('wrote') != []:
        raise ValueError('Central audit did not return a read-only advisory report')
    return report


def run(checker_root, root=ROOT, checkouts=(), inventory_output=None):
    checker = verified_checker(checker_root, root)
    table = inventory(root)
    if inventory_output:
        inventory_output.write_text(json.dumps(table, indent=2) + '\n')
    return execute(checker, table, root, checkouts)


def exercise_controls(checker_root):
    """Exercise the pinned engine against a real temporary git authority, offline."""
    from copy import deepcopy
    checker = verified_checker(checker_root)
    with tempfile.TemporaryDirectory() as directory:
        authority = Path(directory) / 'authority'
        authority.mkdir()
        data = b'{"synthetic_reference_audit_control":true}\n'
        (authority / 'fixture.json').write_bytes(data)
        def git(*args):
            return subprocess.check_output(['git', '-C', str(authority), *args], stderr=subprocess.DEVNULL)
        git('init', '-q')
        git('add', '.')
        git('-c', 'commit.gpgsign=false', '-c', 'user.name=Advisory control fixture',
            '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        git('tag', 'v0.0.0-fixture')
        commit = git('rev-parse', 'HEAD').decode().strip()
        fresh = {'id': 'fresh', 'consumer': CONSUMER, 'class': 'base-carrier',
            'repository': 'example/authority', 'revision': 'v0.0.0-fixture',
            'revisionKind': 'tag', 'commit': commit,
            'files': [{'path': 'fixture.json', 'sha256': hashlib.sha256(data).hexdigest()}]}
        drift, absent, failed = (deepcopy(fresh) for _ in range(3))
        drift['id'] = 'drift'
        old = json.dumps(drift, sort_keys=True).encode()
        digest = drift['files'][0]['sha256']
        drift['files'][0]['sha256'] = ('0' if digest[0] != '0' else '1') + digest[1:]
        if old == json.dumps(drift, sort_keys=True).encode():
            raise ValueError('Wrong-digest control did not change any recorded bytes')
        absent['id'] = 'absent'
        absent['files'][0]['path'] = 'missing.json'
        failed['id'] = 'query-failed'
        failed['repository'] = 'example/unmapped'
        table = {'inventoryVersion': 1, 'references': [fresh, drift, absent, failed]}
        report = execute(checker, table, authority, ['example/authority=' + str(authority)])
        actual = {row['id']: row['verdict'] for row in report['references']}
        wanted = {'fresh': 'FRESH', 'drift': 'DRIFT', 'absent': 'ABSENT', 'query-failed': 'QUERY_FAILED'}
        if actual != wanted:
            raise ValueError('Reference controls disagreed: ' + str(actual))
        if (authority / 'fixture.json').read_bytes() != data:
            raise ValueError('Advisory modified the actual authority bytes')
        return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checker-root', type=Path, required=True)
    parser.add_argument('--checkout', action='append', default=[])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--inventory-output', type=Path)
    parser.add_argument('--exercise-controls', action='store_true', help='run required offline fixture controls before the advisory')
    args = parser.parse_args()
    try:
        controls = exercise_controls(args.checker_root) if args.exercise_controls else None
        report = run(args.checker_root, checkouts=args.checkout, inventory_output=args.inventory_output)
        report['implementation'] = load(ROOT, 'references/checker.json')
        if controls is not None:
            report['controls'] = controls
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.exit(2, 'Reference advisory execution refused: ' + str(error) + '\n')
    rendered = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end='')


if __name__ == '__main__':
    main()
