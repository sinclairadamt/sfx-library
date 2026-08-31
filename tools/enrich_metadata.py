#!/usr/bin/env python3
"""
enrich_metadata.py — generate AI keyword metadata for the SFX library using Claude.

Walks the local "SFX Libraries" folder, and for every audio file asks Claude
(via the Anthropic Messages Batches API) to generate a rich set of search
keywords based on the filename and folder path. Existing signal already
available locally — the category/tags/keywords build_index.py derived into
data.json, and any tags embedded in the audio file itself (ID3/RIFF INFO
comments, titles, etc.) — is passed along as hints so Claude isn't guessing
from the filename alone.

Files are grouped into chunks (several files per API request) and submitted
through the Batches API, which is well suited to a one-time bulk job like this
one: 50% cheaper than synchronous requests, and it doesn't require holding
tens of thousands of requests open at once.

Writes the enriched result to a master metadata.json in the project root.

Usage:
    python3 enrich_metadata.py --root "/path/to/SFX Libraries" --out "../metadata.json"

Options:
    --root              Path to the top-level "SFX Libraries" folder (required)
    --data-json         Existing data.json to reuse as hints [default: ../data.json]
    --out               Output path for the master metadata.json [default: ../metadata.json]
    --model             Claude model to use [default: claude-opus-5]
    --files-per-request Number of files bundled into each API request [default: 40]
    --batch-size        Max requests per Batches API submission [default: 20000]
    --limit             Only process the first N files (for a quick test run)

Requires:
    pip install anthropic mutagen
    ANTHROPIC_API_KEY set in the environment (or `ant auth login`)
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

# These modules live alongside this script
sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import classify, extract_keywords
from path_parser import parse_path

AUDIO_EXTENSIONS = {'.wav', '.mp3', '.aif', '.aiff', '.flac', '.ogg'}
SKIP_DIRS = {'__MACOSX', '.Spotlight-V100', '.fseventsd', '.TemporaryItems'}

DEFAULT_MODEL = "claude-opus-5"
POLL_INTERVAL_SECONDS = 60

# Tags mutagen exposes under different keys depending on container format
EMBEDDED_TAG_KEYS = ('TIT2', 'title', 'COMM::eng', 'comment', 'description', '\xa9nam', 'ICMT', 'IKEY')

KEYWORDS_SCHEMA = {
    "type": "object",
    "properties": {
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The id given for this file in the prompt, echoed back unchanged.",
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "8-15 concise, lowercase search keywords: what the sound is, "
                            "what it could be used for, its texture/mood, and near-synonyms "
                            "a student might search for."
                        ),
                    },
                },
                "required": ["id", "keywords"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["files"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You are tagging sound effect files for a searchable library used by video "
    "production students. For each file described below, return a rich, specific "
    "list of search keywords covering: what the sound is, what it could be used "
    "for in a video project, its texture/mood, and near-synonyms a student might "
    "search for. Keywords should be lowercase, 1-3 words each, with no duplicates "
    "and no vendor or catalog codes. Return one entry per file, matched by id."
)


def iter_audio_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
        for fname in filenames:
            p = Path(dirpath) / fname
            if p.suffix.lower() in AUDIO_EXTENSIONS:
                yield p


def load_existing_index(data_json_path):
    """Load build_index.py's data.json, keyed by (pack, filename), for reuse as hints."""
    if not data_json_path.is_file():
        return {}
    with open(data_json_path, encoding='utf-8') as f:
        entries = json.load(f)
    return {(e.get('pk', ''), e.get('n', '')): e for e in entries}


def extract_embedded_metadata(path):
    """Best-effort read of embedded tags (title/comment/description) via mutagen."""
    try:
        from mutagen import File as MutagenFile
    except ImportError:
        return {}
    try:
        audio = MutagenFile(path)
    except Exception:
        return {}
    if audio is None or not getattr(audio, 'tags', None):
        return {}

    hints = {}
    for key in EMBEDDED_TAG_KEYS:
        try:
            value = audio.tags.get(key)
        except Exception:
            continue
        if not value:
            continue
        text = str(value[0]) if isinstance(value, list) else str(value)
        text = text.strip()
        if text:
            hints[key] = text
    return hints


def build_record(abs_path, root, existing_index):
    """Collect everything known about a file: baseline fields + hint text for the prompt."""
    rel = abs_path.relative_to(root)
    parts = rel.parts
    stem = abs_path.stem

    src, pk = parse_path(parts)
    cat, tags = classify(stem, parts)
    cleaned_kw = extract_keywords(stem)

    hint_entry = existing_index.get((pk, abs_path.name), {})
    embedded = extract_embedded_metadata(abs_path)

    lines = [
        f"Filename: {abs_path.name}",
        f"Folder path: {' / '.join(parts[:-1]) or '(root)'}",
        f"Provider: {src}",
        f"Pack: {pk}",
    ]
    if cat and cat != 'other':
        lines.append(f"Existing category guess: {cat}")
    if tags:
        lines.append(f"Existing descriptor tags: {', '.join(tags)}")
    if cleaned_kw:
        lines.append(f"Cleaned filename keywords: {cleaned_kw}")
    if hint_entry.get('kw'):
        lines.append(f"Previously indexed keywords: {hint_entry['kw']}")
    if hint_entry.get('tags'):
        lines.append(f"Previously indexed tags: {', '.join(hint_entry['tags'])}")
    for key, text in embedded.items():
        lines.append(f"Embedded metadata ({key}): {text}")

    return {
        "n": abs_path.name,
        "p": str(rel).replace('\\', '/'),
        "src": src,
        "pk": pk,
        "cat": cat,
        "ext": abs_path.suffix.lower().lstrip('.'),
        "tags": tags,
        "kw": cleaned_kw,
        "_prompt_lines": lines,
    }


def chunk(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def build_chunk_prompt(records):
    blocks = []
    for i, rec in enumerate(records):
        blocks.append(f"[{i}]\n" + "\n".join(rec["_prompt_lines"]))
    return "\n\n".join(blocks)


def make_custom_id(chunk_index):
    digest = hashlib.sha1(f"chunk-{chunk_index}".encode('utf-8')).hexdigest()[:16]
    return f"c{chunk_index}-{digest}"


def submit_and_wait(client, requests_list, batch_size):
    """Submit requests in batches, poll each to completion, and return {custom_id: result}."""
    all_results = {}
    for start in range(0, len(requests_list), batch_size):
        piece = requests_list[start:start + batch_size]
        batch = client.messages.batches.create(requests=piece)
        print(f"  Batch {batch.id}: {len(piece):,} requests submitted")

        while True:
            batch = client.messages.batches.retrieve(batch.id)
            if batch.processing_status == "ended":
                break
            counts = batch.request_counts
            print(
                f"    ...processing: {counts.processing} pending, "
                f"{counts.succeeded} succeeded, {counts.errored} errored"
            )
            time.sleep(POLL_INTERVAL_SECONDS)

        print(
            f"  Batch {batch.id} complete — "
            f"succeeded={batch.request_counts.succeeded}, errored={batch.request_counts.errored}"
        )

        for result in client.messages.batches.results(batch.id):
            all_results[result.custom_id] = result

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Enrich SFX metadata with Claude-generated keywords.")
    parser.add_argument('--root', required=True, help='Path to the top-level "SFX Libraries" folder')
    parser.add_argument('--data-json', default='../data.json',
                        help='Existing data.json to reuse as hints (from build_index.py)')
    parser.add_argument('--out', default='../metadata.json', help='Output path for the master metadata.json')
    parser.add_argument('--model', default=DEFAULT_MODEL, help='Claude model to use')
    parser.add_argument('--files-per-request', type=int, default=40,
                        help='Number of files bundled into each API request')
    parser.add_argument('--batch-size', type=int, default=20_000,
                        help='Max requests per Batches API submission')
    parser.add_argument('--limit', type=int, default=None, help='Only process the first N files (testing)')
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    data_json_path = Path(args.data_json).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()

    if not root.is_dir():
        print(f"ERROR: Root directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning: {root}")
    files = list(iter_audio_files(root))
    if args.limit:
        files = files[:args.limit]
    print(f"Found {len(files):,} audio files")

    existing_index = load_existing_index(data_json_path)
    print(f"Loaded {len(existing_index):,} existing entries from {data_json_path}")

    records = [build_record(f, root, existing_index) for f in files]

    client = anthropic.Anthropic()

    max_output_tokens = min(8192, 300 + args.files_per_request * 120)
    requests_list = []
    chunks = list(chunk(records, args.files_per_request))
    for i, group in enumerate(chunks):
        requests_list.append(Request(
            custom_id=make_custom_id(i),
            params=MessageCreateParamsNonStreaming(
                model=args.model,
                max_tokens=max_output_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_chunk_prompt(group)}],
                output_config={"format": {"type": "json_schema", "schema": KEYWORDS_SCHEMA}},
            ),
        ))

    print(
        f"Submitting {len(requests_list):,} requests "
        f"({len(records):,} files, {args.files_per_request} per request)"
    )
    results = submit_and_wait(client, requests_list, args.batch_size)
    print(f"Collected {len(results):,} chunk results")

    entries = []
    errors = []
    for i, group in enumerate(chunks):
        custom_id = make_custom_id(i)
        result = results.get(custom_id)

        keywords_by_id = {}
        if result is None:
            errors.append((custom_id, "no result returned"))
        elif result.result.type == "succeeded":
            text_block = next((b for b in result.result.message.content if b.type == "text"), None)
            try:
                parsed = json.loads(text_block.text) if text_block else {}
                for file_entry in parsed.get("files", []):
                    keywords_by_id[file_entry["id"]] = file_entry.get("keywords", [])
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                errors.append((custom_id, f"unparsable response: {e}"))
        else:
            errors.append((custom_id, f"{result.result.type}: {getattr(result.result, 'error', '')}"))

        for j, rec in enumerate(group):
            entry = {k: v for k, v in rec.items() if not k.startswith('_')}
            entry["keywords"] = keywords_by_id.get(j, [])
            entries.append(entry)

    entries.sort(key=lambda e: (e.get('src', '').lower(), e.get('pk', '').lower(), e.get('n', '').lower()))

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(entries, f, separators=(',', ':'), ensure_ascii=False)

    size_mb = out.stat().st_size / 1_048_576
    print(f"\nWrote {len(entries):,} entries -> {out}  ({size_mb:.1f} MB)")

    missing_kw = sum(1 for e in entries if not e["keywords"])
    if missing_kw:
        print(f"{missing_kw:,} entries have no AI keywords (see chunk errors below)")

    if errors:
        print(f"\n{len(errors)} chunk(s) had issues (first 10):")
        for custom_id, msg in errors[:10]:
            print(f"  {custom_id}: {msg}")


if __name__ == '__main__':
    main()
