"""
metadata.py — extract audio duration using mutagen with a struct fallback for WAV.
"""

import struct
from pathlib import Path


def get_duration(path: Path):
    """Return duration in seconds (float), or None on failure."""
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(path)
        if audio is not None and audio.info is not None:
            return float(audio.info.length)
    except Exception:
        pass

    if path.suffix.lower() == '.wav':
        return _wav_duration_fallback(path)
    return None


def _wav_duration_fallback(path: Path):
    """
    Parse WAV RIFF header for duration without mutagen.
    Works for standard PCM WAVs where the data chunk starts at byte 36.
    """
    try:
        with open(path, 'rb') as f:
            header = f.read(44)
        if len(header) < 44:
            return None
        if header[:4] != b'RIFF' or header[8:12] != b'WAVE':
            return None
        byte_rate = struct.unpack_from('<I', header, 28)[0]
        data_size = struct.unpack_from('<I', header, 40)[0]
        if byte_rate == 0:
            return None
        return data_size / byte_rate
    except Exception:
        return None
