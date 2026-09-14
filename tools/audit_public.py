"""Audit the files Git will publish; nothing outside ``git ls-files`` is read.

The working directory also holds the ISOs, the extracted game files and every
texture dump, so the repository is an allow-list (see .gitignore) and this
script checks what actually made it through: only UTF-8 text of the permitted
kinds, no NUL bytes, no credential patterns, no embedded hex dumps, every JSON
parses, every Python module compiles.  It then writes publication_manifest.json
with the size and SHA-256 of each published file.

    python tools/audit_public.py
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'.py', '.json', '.txt', '.md', '.csv'}
SECRET = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}'
                    r'|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')
# Files that would only ever hold game data, whatever their suffix.
FORBIDDEN_NAMES = re.compile(r'(?i)(?:^|/)(?:eboot|boot|pspfont|init0|asm|world0|make0|title0|result0|map\d{3})'
                             r'(?:_[a-z]+)?\.(?:bin|dat|dec)$')


def main():
    listed = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                            cwd=ROOT, check=True, capture_output=True).stdout
    paths = sorted(p for p in listed.decode('utf-8').split('\0') if p)
    errors, records = [], []
    for rel in paths:
        path = ROOT / rel
        if not path.is_file():
            continue
        if path.suffix not in ALLOWED and path.name != '.gitignore':
            errors.append(f'{rel}: unexpected file type')
            continue
        if FORBIDDEN_NAMES.search(rel):
            errors.append(f'{rel}: game data file name')
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeError:
            errors.append(f'{rel}: not UTF-8 text')
            continue
        if b'\0' in raw or SECRET.search(text):
            errors.append(f'{rel}: binary content or credential pattern')
        if re.search(r'[0-9a-fA-F]{1024,}', text):
            errors.append(f'{rel}: possible embedded binary hex dump')
        if path.suffix == '.json':
            json.loads(text)
        if path.suffix == '.py':
            ast.parse(text, filename=rel)
        if rel != 'publication_manifest.json':
            records.append({'path': rel, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    if errors:
        raise SystemExit('\n'.join(errors))
    (ROOT / 'publication_manifest.json').write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: {len(records)} UTF-8 source/document/translation files; '
          'no forbidden file types or detected credentials.')


if __name__ == '__main__':
    main()
