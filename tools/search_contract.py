"""Validate search artifacts against public inputs and pinned dependencies."""
import hashlib
import json
import pathlib
import re

from contracts import ROOT, ContractError

PAGES = ('index.html', 'work.html', 'teaching.html', 'speaking.html',
         'writing.html', 'tags.html', 'contact.html')
MANIFEST = 'build-manifest.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inputs(root=ROOT):
    result = {}
    for name in PAGES:
        text = (root / name).read_text()
        text = re.sub(r'<!-- search:start -->.*?<!-- search:end -->\n?', '', text, flags=re.S)
        result[name] = digest(text.encode())
    result['package-lock.json'] = digest((root / 'package-lock.json').read_bytes())
    return result


def artifacts(directory):
    return {str(p.relative_to(directory)): digest(p.read_bytes())
            for p in sorted(directory.rglob('*')) if p.is_file() and p != directory / MANIFEST}


def write_manifest(directory):
    data = {'inputs': inputs(), 'artifacts': artifacts(directory)}
    (directory / MANIFEST).write_text(json.dumps(data, sort_keys=True, indent=2) + '\n')


def validate_search(directory=None):
    directory = pathlib.Path(directory) if directory else ROOT / 'pagefind'
    path = directory / MANIFEST
    if not path.is_file():
        raise ContractError('Search manifest missing. Run ./build.')
    data = json.loads(path.read_text())
    if data.get('inputs') != inputs():
        raise ContractError('Search inputs are stale. Run ./build.')
    if not data.get('artifacts') or data['artifacts'] != artifacts(directory):
        raise ContractError('Search artifacts are missing or changed. Run ./build.')
