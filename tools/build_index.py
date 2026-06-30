#!/usr/bin/env python3
"""
build_index.py — regenerate data.json for the sfx-library GitHub Pages site.

Walks the local SFX Libraries folder, reads embedded audio metadata and parses
filenames, then writes an enriched data.json with category, tags, duration,
provider, and pack fields for better client-side search and filtering.

Usage:
    python3 build_index.py --root "/path/to/SFX Libraries" --out "../data.json"

Options:
    --root          Path to the top-level "SFX Libraries" folder (required)
    --out           Output path for data.json  [default: ../data.json]
    --workers       Parallel workers for duration extraction [default: 8]
    --skip-duration Skip reading audio headers (much faster; no dur field)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# These modules live alongside this script
sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import classify, extract_keywords
from path_parser import parse_path

AUDIO_EXTENSIONS = {'.wav', '.mp3', '.aif', '.aiff', '.flac', '.ogg'}
SKIP_DIRS = {'__MACOSX', '.Spotlight-V100', '.fseventsd', '.TemporaryItems'}

# Prefix prepended to relative paths to match SharePoint URL structure
SHAREPOINT_PREFIX = "Sinclair/SFX Libraries/"


def iter_audio_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune system directories in-place so os.walk skips them
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith('.')
        ]
        for fname in filenames:
            p = Path(dirpath) / fname
            if p.suffix.lower() in AUDIO_EXTENSIONS:
                yield p


def build_entry(abs_path: Path, root: Path) -> dict:
    rel = abs_path.relative_to(root)
    parts = rel.parts  # e.g. ('Adobe', 'Fire and Explosions', 'file.wav')

    src, pk = parse_path(parts)
    stem = abs_path.stem
    cat, tags = classify(stem, parts)

    kw = extract_keywords(stem)

    entry = {
        "n":   abs_path.name,
        "p":   SHAREPOINT_PREFIX + str(rel).replace('\\', '/'),
        "src": src,
        "pk":  pk,
        "cat": cat,
        "ext": abs_path.suffix.lower().lstrip('.'),
    }
    if kw:
        entry["kw"] = kw
    if tags:
        entry["tags"] = tags

    return entry


def simple_progress(iterable, total, desc=""):
    """Fallback progress indicator when tqdm is not installed."""
    done = 0
    interval = max(1, total // 20)
    for item in iterable:
        yield item
        done += 1
        if done % interval == 0 or done == total:
            pct = done * 100 // total
            print(f"\r{desc}: {done:,}/{total:,} ({pct}%)", end="", flush=True)
    print()


def main():
    parser = argparse.ArgumentParser(description="Build enriched data.json for sfx-library.")
    parser.add_argument('--root', required=True,
                        help='Path to the top-level "SFX Libraries" folder')
    parser.add_argument('--out', default='../data.json',
                        help='Output path for data.json')
    parser.add_argument('--workers', type=int, default=8,
                        help='Parallel worker threads')
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()

    if not root.is_dir():
        print(f"ERROR: Root directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning: {root}")
    files = list(iter_audio_files(root))
    print(f"Found {len(files):,} audio files")

    print(f"Workers: {args.workers}")

    entries = []
    errors = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(build_entry, f, root): f
            for f in files
        }
        completed = as_completed(future_map)
        if HAS_TQDM:
            completed = tqdm(completed, total=len(files), desc="Processing")
        else:
            completed = simple_progress(completed, total=len(files), desc="Processing")

        for fut in completed:
            try:
                entries.append(fut.result())
            except Exception as e:
                errors.append((str(future_map[fut]), str(e)))

    # Sort: provider -> pack -> filename (stable diffs on re-run)
    entries.sort(key=lambda e: (
        e.get('src', '').lower(),
        e.get('pk', '').lower(),
        e.get('n', '').lower(),
    ))

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(entries, f, separators=(',', ':'), ensure_ascii=False)

    size_mb = out.stat().st_size / 1_048_576
    print(f"\nWrote {len(entries):,} entries -> {out}  ({size_mb:.1f} MB)")

    if errors:
        print(f"\nEncountered {len(errors)} errors (first 10):")
        for path, msg in errors[:10]:
            print(f"  {path}: {msg}")

    # Quick quality check
    cat_counts = {}
    for e in entries:
        c = e.get('cat', 'other')
        cat_counts[c] = cat_counts.get(c, 0) + 1
    other_pct = cat_counts.get('other', 0) * 100 / max(len(entries), 1)
    print(f"\nCategory 'other': {cat_counts.get('other', 0):,} ({other_pct:.1f}%)")
    if other_pct > 15:
        print("  TIP: High 'other' count — consider adding keywords to taxonomy.py")



if __name__ == '__main__':
    main()
