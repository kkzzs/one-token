"""Verify and restore split LFS weights to an explicit destination directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def restore(repo, destination, verify_only=False):
    manifest = json.loads((repo / 'weights-manifest.json').read_text())
    small = json.loads((repo / 'small-file-sha256.json').read_text())
    links = json.loads((repo / 'restore-links.json').read_text())
    for entry in manifest['entries']:
        target = destination / entry['relative_target']
        if not verify_only and (target.exists() or target.is_symlink()):
            raise FileExistsError(f'Refusing to overwrite: {target}')
    for link in links:
        target = destination / link['path']
        if not verify_only and (target.exists() or target.is_symlink()):
            raise FileExistsError(f'Refusing to overwrite: {target}')
    for entry in manifest['entries']:
        target = destination / entry['relative_target']
        temp = target.with_name(target.name + '.restoring')
        output = None
        try:
            if not verify_only:
                target.parent.mkdir(parents=True, exist_ok=True)
                output = temp.open('xb')
            total = 0
            for chunk in entry['chunks']:
                source = repo / chunk['path']
                expected = chunk.get('oid') or small.get(chunk['path'])
                if not expected:
                    raise ValueError(f'Missing SHA256: {source}')
                if not source.exists() or source.stat().st_size != chunk['size']:
                    source = repo / '.git/lfs/objects' / expected[:2] / expected[2:4] / expected
                if not source.exists() or source.stat().st_size != chunk['size']:
                    raise ValueError(f'{source}: missing or wrong size; run git lfs fetch origin main')
                digest = hashlib.sha256()
                with source.open('rb') as stream:
                    for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                        digest.update(block)
                        if output:
                            output.write(block)
                        total += len(block)
                if digest.hexdigest() != expected:
                    raise ValueError(f'SHA256 mismatch: {source}')
            if total != entry['size']:
                raise ValueError(f'Total size mismatch: {target}')
            if output:
                output.close()
                output = None
                temp.rename(target)
            print(f'OK {entry["relative_target"]}', flush=True)
        except Exception:
            if output:
                output.close()
                temp.unlink(missing_ok=True)
            raise
    if not verify_only:
        for link in links:
            path = destination / link['path']
            target = destination / link['target']
            if not target.exists():
                raise FileNotFoundError(target)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(os.path.relpath(target, path.parent))
    print('All weights verified.' if verify_only else 'All weights restored and verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True,
                        help='Restore root, e.g. /root on a fresh machine')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    restore(Path(__file__).resolve().parent, args.destination.resolve(), args.verify_only)
