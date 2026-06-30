"""
path_parser.py — derive src (provider) and pk (pack name) from path parts.
"""

import re

# Sonniss stores files 3 levels deep: Sonniss / ArtistFolder / PackFolder / file
# All other providers are flat: Provider / PackFolder / [optional subfolders] / file
DEEP_PROVIDERS = {'Sonniss'}


def parse_path(parts: tuple) -> tuple:
    """
    Given path parts relative to the SFX Libraries root, return (src, pk).

    parts[0]  = provider folder   (always)
    parts[-1] = filename          (always)
    """
    src = parts[0]

    if len(parts) <= 2:
        return src, src

    if src in DEEP_PROVIDERS:
        # Use the deepest subfolder before the filename as the pack name
        pk_raw = parts[-2] if len(parts) >= 3 else parts[1]
    else:
        pk_raw = parts[1]

    pk = _clean_pack_name(pk_raw, src)
    return src, pk


def _clean_pack_name(raw: str, provider: str) -> str:
    """Remove redundant vendor prefixes and normalize separators."""
    pk = raw.replace('_', ' ').strip()

    # BlueZone: "Bluezone Corporation Free X Sound Effects" -> "X"
    if pk.lower().startswith('bluezone corporation free '):
        pk = pk[len('Bluezone Corporation Free '):]
        pk = re.sub(r'\s+Sound Effects$', '', pk, flags=re.IGNORECASE).strip()

    # 99Sounds: "#99S027 Cinematic Loops" -> "Cinematic Loops"
    pk = re.sub(r'^#\d+[A-Z]+\d*\s+', '', pk)

    # PremiumBeat: "PB - Foo" or "PB-foo-bar" -> "Foo" / "foo bar"
    pk = re.sub(r'^PB[-\s]+', '', pk, flags=re.IGNORECASE)

    # ActionVFX: "ActionVFX Free X SFX" -> "X SFX"
    pk = re.sub(r'^ActionVFX[_ ]+(Free[_ ]+)?', '', pk, flags=re.IGNORECASE)

    # FreePD: "Comedy mp3s" -> "Comedy"
    pk = re.sub(r'\s*mp3s?$', '', pk, flags=re.IGNORECASE)

    return pk.strip()
