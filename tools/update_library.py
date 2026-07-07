#!/usr/bin/env python3
"""
update_library.py — regenerate data.json and publish it to GitHub.

Desktop-launcher entry point for the "Update Library" action: runs the same
scan/classify logic as build_index.py against the local SFX Libraries folder,
then commits and pushes data.json to the sfx-library repo if it changed.
Reports the outcome in a native macOS dialog.
"""

import json
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

TOOLS_DIR = Path(__file__).parent
REPO_DIR = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from build_index import iter_audio_files, build_entry  # noqa: E402
from mac_ui import show_popup  # noqa: E402

LOCAL_SFX_DIR = Path("/Users/thompson/Library/CloudStorage/OneDrive-SinclairCommunityCollege/Sinclair/SFX Libraries")
DATA_JSON = REPO_DIR / "data.json"
WORKERS = 8


def run_git(*args):
    return subprocess.run(
        ['git', *args], cwd=REPO_DIR, check=True,
        capture_output=True, text=True,
    )


def scan_library():
    files = list(iter_audio_files(LOCAL_SFX_DIR))

    entries = []
    errors = []
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_map = {executor.submit(build_entry, f, LOCAL_SFX_DIR): f for f in files}
        for fut in as_completed(future_map):
            try:
                entries.append(fut.result())
            except Exception as e:
                errors.append((str(future_map[fut]), str(e)))

    entries.sort(key=lambda e: (
        e.get('src', '').lower(),
        e.get('pk', '').lower(),
        e.get('n', '').lower(),
    ))
    return entries, errors


def main():
    if not LOCAL_SFX_DIR.is_dir():
        show_popup("Library Update Error", f"Directory not found!\nCheck path:\n{LOCAL_SFX_DIR}")
        sys.exit(1)

    old_count = 0
    if DATA_JSON.exists():
        try:
            old_count = len(json.loads(DATA_JSON.read_text(encoding='utf-8')))
        except Exception:
            pass

    entries, errors = scan_library()

    DATA_JSON.write_text(
        json.dumps(entries, separators=(',', ':'), ensure_ascii=False),
        encoding='utf-8',
    )

    status = run_git('status', '--porcelain', '--', 'data.json')
    if not status.stdout.strip():
        show_popup(
            "Sinclair Sound Library",
            f"Scan complete!\n\nTotal Library Size: {len(entries)} sounds\nNo changes detected. Skipping GitHub push.",
        )
        return

    message = f"Update Complete!\n\nTotal Library Size: {len(entries)} sounds\n"
    delta = len(entries) - old_count
    if delta > 0:
        message += f"New files added: {delta}\n"
    elif delta < 0:
        message += f"Files removed: {-delta}\n"

    try:
        run_git('add', 'data.json')
        run_git('commit', '-m', 'Automated library update via update_library.py')
        run_git('push', 'origin', 'main')
        message += "\nSuccessfully pushed to GitHub!"
    except subprocess.CalledProcessError as e:
        message += f"\nGitHub push failed:\n{e.stderr or e.stdout}"

    if errors:
        message += f"\n\n{len(errors)} file(s) failed to process (see terminal log)."
        for path, msg in errors[:10]:
            print(f"  {path}: {msg}", file=sys.stderr)

    show_popup("Sinclair Sound Library", message)


if __name__ == '__main__':
    main()
