"""Apply the v1.0.0 xdelta with input, patch and output hash verification.

    python tools/apply_release.py --xdelta xdelta3.exe --source "<원본 ISO>" \
        --patch VMP_Korean_v1.0.0.xdelta --output "<새 ISO>"

The original must be the unmodified Japanese ISO listed in README.md; the
output path must not exist yet.  Nothing is overwritten and a result whose
SHA-256 does not match is reported as a failure, not a success.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

SOURCE_SIZE = 612728832
SOURCE_MD5 = '5b4355c58f0dd9e0091ba17dda8783c6'
SOURCE_SHA = '76df5a15c4441b8c738bb97b850ef2feba28b7582e96c22a3c51d489a929bfbc'
PATCH_SHA = '069572210bcfa7105a9cb52f3a93b25ecd470f1955598461eb5a83ffaf252470'
OUTPUT_SHA = 'dcfb4ca92cd2eed5784ba25c11576a6646030d63fb04cf847fc5b116f4e76a54'


def digest(path, kind='sha256'):
    h = hashlib.new(kind)
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('xdelta', 'source', 'patch', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    source, patch, output, exe = (p.resolve() for p in (args.source, args.patch, args.output, args.xdelta))
    if output.exists() or output in (source, patch, exe):
        raise ValueError('Output must be a new file, different from all inputs.')
    if source.stat().st_size != SOURCE_SIZE or digest(source, 'md5') != SOURCE_MD5 or digest(source) != SOURCE_SHA:
        raise ValueError('Original ISO hash mismatch. Use the unmodified Japanese ISO (ULJM05332 v1.01) listed in README.')
    if digest(patch) != PATCH_SHA:
        raise ValueError('Patch SHA-256 mismatch.')
    print('Input and patch verified. Applying...', flush=True)
    # xdelta3 refuses to overwrite an existing output on its own; the check
    # above already guarantees the path is new.
    subprocess.run([str(exe), '-d', '-s', str(source), str(patch), str(output)], check=True)
    if output.stat().st_size != SOURCE_SIZE or digest(output) != OUTPUT_SHA:
        raise ValueError('Output verification failed. Do not use the resulting file.')
    print('PASS: output SHA-256 = ' + OUTPUT_SHA)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
