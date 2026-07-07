#!/usr/bin/env python3
"""
remove_duplicates.py — find exact duplicate audio files (same name + size) and
quarantine the extras, after confirming with the user.

Desktop-launcher entry point for the "Remove Duplicates" action.
"""

import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))
from mac_ui import show_popup, ask_yes_no  # noqa: E402

LOCAL_SFX_DIR = Path("/Users/thompson/Library/CloudStorage/OneDrive-SinclairCommunityCollege/Sinclair/SFX Libraries")
QUARANTINE_DIR = LOCAL_SFX_DIR.parent / "_Duplicates_Quarantine"
REPORT_FILE = QUARANTINE_DIR / "quarantine_log.txt"
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".aiff", ".aif", ".ogg", ".flac", ".m4a"}


def find_exact_duplicates():
    file_map = defaultdict(list)

    for root, dirs, files in os.walk(LOCAL_SFX_DIR):
        if QUARANTINE_DIR.name in root:
            continue
        for file in files:
            if file.startswith('.'):
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue
            full_path = os.path.join(root, file)
            try:
                size = os.path.getsize(full_path)
            except OSError:
                continue
            file_map[(file.lower(), size)].append(full_path)

    return {key: paths for key, paths in file_map.items() if len(paths) > 1}


def quarantine(duplicates):
    QUARANTINE_DIR.mkdir(exist_ok=True)
    moved_count = 0

    with open(REPORT_FILE, "w", encoding="utf-8") as log:
        log.write("--- DUPLICATE QUARANTINE LOG ---\n")
        log.write("Use this log to verify the files that were moved.\n\n")

        for (filename, size), paths in duplicates.items():
            kept_file = paths[0]
            dupes = paths[1:]

            log.write(f"EXACT MATCH SET: {filename} ({size} bytes)\n")
            log.write(f"   KEPT IN LIBRARY: {kept_file.replace(str(LOCAL_SFX_DIR), '')}\n")

            for dup_path in dupes:
                relative_dir = os.path.relpath(os.path.dirname(dup_path), LOCAL_SFX_DIR)
                sub_dir = QUARANTINE_DIR / relative_dir
                sub_dir.mkdir(parents=True, exist_ok=True)
                target_path = sub_dir / os.path.basename(dup_path)
                try:
                    shutil.move(dup_path, str(target_path))
                    moved_count += 1
                    log.write(f"   QUARANTINED: {dup_path.replace(str(LOCAL_SFX_DIR), '')}\n")
                except Exception as e:
                    log.write(f"   FAILED TO MOVE: {dup_path} ({e})\n")
            log.write("\n")

    return moved_count


def main():
    if not LOCAL_SFX_DIR.is_dir():
        show_popup("Remove Duplicates Error", f"Directory not found!\nCheck path:\n{LOCAL_SFX_DIR}")
        sys.exit(1)

    duplicates = find_exact_duplicates()

    if not duplicates:
        show_popup("Remove Duplicates", "No exact duplicates (same name and size) were found.")
        return

    dup_file_count = sum(len(paths) - 1 for paths in duplicates.values())
    confirmed = ask_yes_no(
        "Remove Duplicates",
        f"Found {len(duplicates)} duplicate set(s), {dup_file_count} extra file(s).\n\n"
        f"Move the extras to a quarantine folder for review?",
        yes_label="Quarantine",
        no_label="Skip",
    )

    if not confirmed:
        show_popup("Remove Duplicates", "No files were moved.")
        return

    moved_count = quarantine(duplicates)
    show_popup(
        "Remove Duplicates",
        f"Quarantined {moved_count} duplicate file(s).\n\nLog saved to:\n{REPORT_FILE}",
    )


if __name__ == '__main__':
    main()
