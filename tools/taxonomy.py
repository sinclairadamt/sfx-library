"""
taxonomy.py — keyword-based SFX category and tag classification.
"""

import re
from typing import Tuple, List

# ---------------------------------------------------------------------------
# KEYWORD EXTRACTION
# Produces a cleaned, searchable string from a filename stem by stripping
# vendor catalog codes, sequential numbers, and provider name fragments.
# ---------------------------------------------------------------------------

_PROVIDER_FRAGMENTS = {
    'bluezone', 'premiumbeat', 'actionvfx', 'adobe', 'sonniss',
    'lucidsamples', 'seaweed', 'factory', 'freepd', 'shutterstock',
    '99sounds', 'flamesound', 'flame',
    'soundmorph', 'toyed', 'hzandbits', 'grit', 'sfxbible',
}

_FILLER_WORDS = {'the', 'and', 'or', 'a', 'an', 'of', 'for', 'in', 'on', 'at', 'to', 'by'}


def extract_keywords(stem: str) -> str:
    """
    Return a cleaned keyword string from a filename stem, e.g.:
      'Bluezone_BC0248_082_hit_classic'   -> 'hit classic'
      'BMW E46, Cars, Vehicles, Engine'   -> 'BMW E46 Cars Vehicles Engine'
      'SPDR - Solar Wind, Eruption'       -> 'SPDR Solar Wind Eruption'
      'BG_Swaziland_Jungle_Night_Rain_a'  -> 'Swaziland Jungle Night Rain'
    """
    # Normalize separators
    s = re.sub(r'[_\-,\.]+', ' ', stem)

    # Remove vendor catalog codes: 2+ letters followed by 3+ digits (BC0248, LS001)
    s = re.sub(r'\b[A-Za-z]{2,}\d{3,}\w*\b', '', s)

    # Remove Sonniss-style mixed-case library codes: 2+ uppercase immediately
    # followed by lowercase (MOTRSrvo, TOYMisc, GOREMisc, CREASmall, METLMvmt)
    s = re.sub(r'\b[A-Z]{2,}[a-z]\w*\b', '', s)

    # Remove standalone numbers and numbers-then-units (128BPM, 96kHz)
    s = re.sub(r'\b\d+[A-Za-z]*\b', '', s)

    words = s.split()
    result = []
    for w in words:
        if len(w) <= 2:                          # single chars and 2-letter codes
            continue
        if w.lower() in _FILLER_WORDS:
            continue
        if w.lower() in _PROVIDER_FRAGMENTS:
            continue
        result.append(w)

    return ' '.join(result)

# ---------------------------------------------------------------------------
# CATEGORY MAP
# Maps canonical category name -> trigger keywords (matched case-insensitively).
# Order matters: first match wins. More-specific entries go before general ones.
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "impulse_response": [
        "impulse response", "impulse_response", "reverb ir", "convolution",
        "midiverb", "lexicon", "EMT", "plate reverb", "hall reverb",
    ],
    "instrument": [
        "sample pack", "casio", "roland", "yamaha", "piano", "guitar",
        "bass guitar", "drum kit", "kick drum", "snare", "bass sample",
        "organ", "pad sample", "kontakt", "sfz instrument",
        " synth ", "synthesizer", "oscillator", "arpeggio", "arpeg",
    ],
    "explosion": [
        "explosion", "explode", "explo", "blast", "detonation", "detonate",
        "bomb", "grenade", "mortar", "missile", "dynamite", "nuke",
        "shockwave", "sonic boom", "cannon fire",
    ],
    "weapon": [
        "weapon", "gun", "rifle", "pistol", "shotgun", "firearm",
        "gunshot", "gunfire", "bullet", "shell", "reload", "cocking",
        "trigger", "suppressor", "silencer", "sword", "blade", "knife",
        "arrow", "bow", "crossbow", "axe", "machete", "whip",
        "laser weapon", "plasma weapon", "railgun",
        "howitzer", "artillery", "mortar fire", "haubits", "cannon fire",
        "sniper", "turret", "flamethrower", "bazooka", "rpg",
    ],
    "footsteps": [
        "footstep", "footsteps", "walking", "running", "jogging",
        "boot ", "shoe ", "heel ", "barefoot", "stomp", "stride", "march",
    ],
    "foley": [
        "foley", "cloth", "clothing", "clothes", "rustle", "creak",
        "door", "doorknob", "lock", "key ", "handle", "paper", "book",
        "bag ", "luggage", "zipper", "button", "wood creak", "floor creak",
        "silverware", "cutlery", "cleaver", "knife chop", "matchbox",
        "wrapper", "plastic bag", "measuring tape", "lever", "coins",
        "camera shutter", "camera click", "light switch", "staple",
        "ceramic", "pottery",
    ],
    "impact": [
        "impact", " hit ", "smash", "crash", "slam", "thud", "thump",
        "punch", "kick", "whack", "strike", "knock", "crunch",
        "collision", "bash", "debris", " drop ",
    ],
    "animal": [
        "animal", "bird", " dog ", " cat ", "wolf", "bear", "lion", "tiger",
        "horse", " cow ", " pig ", "sheep", "duck", "crow", "owl", "hawk",
        "frog", "cricket", "insect", "bee ", "snake", "lizard",
        "monkey", "gorilla", "elephant", "whale", "dolphin", "creature",
        "beast", "roar", "bark", "growl", "chirp", "tweet", "squawk",
        "hiss", "purr", "meow", "whinny", " moo ", "oink",
        " fish ", "deer", "rabbit", "fox ", "raccoon", "squirrel",
        "alligator", "crocodile", "turkey", "eagle", "parrot",
    ],
    "human": [
        "human", "voice", "vocal", "crowd", "people", "person",
        " male ", " female ", " man ", " woman ", "child", "baby",
        "breath", "breathe", "cough", "sneeze", "laugh", "cry", "scream",
        "grunt", "groan", "yell", "whisper", "sing", "shout", "moan",
        "burp", "hiccup", "snore", "sigh", "gasp", "walla",
    ],
    "fire": [
        "fire", "flame", "campfire", "fireplace", "torch", "ignite",
        "flare", "ember", "spark fire", "crackle fire", "blaze",
    ],
    "weather": [
        "rain", "thunder", "lightning", "storm", "wind",
        "snow", "hail", "blizzard", "hurricane", "tornado", "flood",
        "wave", "ocean", "sea", "beach", "river", "stream", "waterfall",
        "drip", "splash",
    ],
    "vehicle": [
        "vehicle", "transportation", " car ", " truck ", " bus ",
        "motorcycle", " bike ", "train", "airplane", "aircraft", " jet ",
        "helicopter", "chopper", " boat ", " ship ", "submarine", "tire", "engine",
        "motor", "exhaust", "horn", "siren", "brake", "skid",
        "driving", "flyby", "fly-by", "pass-by", "driveby",
        "ambulance", "firetruck", "police car",
        "ferrari", "lamborghini", "fiat", "porsche", "bugatti", "maserati",
        "ford", "dodge", "chevy", "mustang", "corvette", "camaro",
        "tugboat", "tug boat", "speedboat", "yacht", "onbrd", "on board",
    ],
    "scifi": [
        "sci-fi", "scifi", "science fiction", "alien", "spaceship",
        "spacecraft", "laser", "phaser", "blaster",
        "robot", "android", "cyborg", "hologram",
        "teleport", "force field", "warp", "hyperspace",
        "futuristic", "datastream", "servo", "raygun",
        "glitch", "motion graphic", "tech sfx", "digital noise",
        "transformation", "morph",
    ],
    "ui": [
        "user interface", " ui ", "notification", "alert", "beep",
        "button click", "menu", "confirm", "error tone", "success tone",
        "ping", "ding", "chime", "access granted", "power up", "power down",
        "startup", "shutdown", "interface",
    ],
    "horror": [
        "horror", "scary", "creepy", "eerie", "sinister",
        "haunted", "ghost", "demon", "monster", "screech",
        "ominous", "dread", "jump scare", "heartbeat",
        "zombie", "undead", "gore", "carnage", "flesh", "meat",
        "blood", "stab wound", "body fall", "death",
    ],
    "cinematic": [
        "cinematic", "trailer", "whoosh", "swish", "sweep",
        "riser", "braaam", "braam", "downer", "sting", "stab", "swell", "buildup",
        "countdown", "logo", "reveal", "title card",
    ],
    "drone": [
        "drone", " bed ", "texture", "sustained", " tone ",
        "rumble", " buzz ", "atmosphere bed", "tension",
        "low end", "sub bass", "throb", "pulsing", "pulse",
        "continuous", "sustained tone", "brown noise", "white noise",
        "pink noise",
    ],
    "ambience": [
        "ambience", "ambient", "atmosphere", "atmo", "background",
        "room tone", "roomtone", "walla", "environmental",
        "city ambience", "nature ambience", "rain ambience",
    ],
    "music": [
        "music", "loop", "musical", "melody", "chord", "jingle",
        "cinematic score", "underscore", "soundtrack", "sample pack",
        " clap ", "drum loop", " bpm ", "rhythm", "rhythmic", "groove",
        "stutter", "tribal", "perc ", "openhat", "rimshot", "one shot",
        "waltz", "ringmod", "break beat", "breakbeat",
    ],
    "nature": [
        "nature", "outdoor", "forest", "jungle", "woods", "field",
        "meadow", "grass", "leaves", " tree ", "birds singing",
        "crickets", "water flowing", "brook", " lake ",
    ],
    "mechanical": [
        "mechanical", "machine", "machinery", "industrial",
        "factory", "gear", "ratchet", "crank", "piston",
        "hydraulic", "pneumatic", "compressor",
        "drill", " saw ", "grinder", "wrench",
        " metal ", "metallic", "metal scrape", "metal rattle",
        "metal sheet", "metal clank", "brick", "concrete block",
    ],
    "electricity": [
        "electric", "electrical", "electricity", " spark ",
        " arc ", "static", " zap ", "crackle electric",
        "high voltage", "tesla",
    ],
    "glass": [
        "glass", "shatter", "break glass", "bottle smash",
        "window break", "mirror break", "crystal",
    ],
    "cartoon": [
        "cartoon", "comic", "comedy", "funny", "silly", "wacky",
        "boing", "boink", "wobble", "squeak", "slide whistle",
        "fart", "splat", "bonk", "twang", " spring ",
    ],
    "magic": [
        "magic", "magical", "fantasy", "spell", "enchant",
        "fairy", "sparkle", "shimmer", "twinkle", "mystical",
        "arcane", "potion", "wand", "dragon", "medieval",
    ],
    "underwater": [
        "underwater", "submerged", "submarine", "deep ocean",
        "sonar", "bubbles", "diving",
    ],
    "household": [
        "household", "kitchen", "cooking",
        "phone", "telephone", "alarm clock", "clock",
        "appliance", "washing machine", "dishwasher", "microwave",
        "hinge", " chair ", " table ",
    ],
    "sports": [
        "sports", "sport", "basketball", "football", "baseball",
        "soccer", "tennis", "golf", "crowd cheer",
        "whistle", "buzzer", "ball bounce",
    ],
}

# ---------------------------------------------------------------------------
# FOLDER CATEGORY MAP
# Direct mapping from known folder names (lowercase, underscores OK) to category.
# Checked first — more reliable than keyword scanning when present.
# ---------------------------------------------------------------------------
FOLDER_CATEGORY_MAP = {
    # Adobe sub-folders
    "ambience 1":           "ambience",
    "ambience 2":           "ambience",
    "ambience":             "ambience",
    "animals":              "animal",
    "cartoon":              "cartoon",
    "crashes":              "impact",
    "drones":               "drone",
    "emergency effects":    "vehicle",
    "fire and explosions":  "explosion",
    "foley":                "foley",
    "foley footsteps":      "footsteps",
    "horror":               "horror",
    "household":            "household",
    "human elements":       "human",
    "imaging elements":     "cinematic",
    "impacts":              "impact",
    "industry":             "mechanical",
    "liquid-water":         "weather",
    "multimedia":           "ui",
    "production elements":  "cinematic",
    "science fiction":      "scifi",
    "sports":               "sports",
    "technology":           "ui",
    "transportation":       "vehicle",
    "underwater":           "underwater",
    "weapons":              "weapon",
    "weather":              "weather",
    # BlueZone (underscores retained)
    "bluezone_corporation_free_ambience_sound_effects":         "ambience",
    "bluezone_corporation_free_cinematic_impact_sound_effects": "cinematic",
    "bluezone_corporation_free_creature_sound_effects":         "animal",
    "bluezone_corporation_free_destruction_sound_effects":      "impact",
    "bluezone_corporation_free_explosion_sound_effects":        "explosion",
    "bluezone_corporation_free_horror_sound_effects":           "horror",
    "bluezone_corporation_free_industrial_sound_effects":       "mechanical",
    "bluezone_corporation_free_mechanical_sound_effects":       "mechanical",
    "bluezone_corporation_free_metal_sound_effects":            "mechanical",
    "bluezone_corporation_free_nature_sound_effects":           "nature",
    "bluezone_corporation_free_organic_sound_effects":          "nature",
    "bluezone_corporation_free_robot_sound_effects":            "scifi",
    "bluezone_corporation_free_sci_fi_sound_effects":           "scifi",
    "bluezone_corporation_free_spaceship_sound_effects":        "scifi",
    "bluezone_corporation_free_steampunk_sound_effects":        "mechanical",
    "bluezone_corporation_free_trailer_sound_effects":          "cinematic",
    "bluezone_corporation_free_transformers_sound_effects":     "scifi",
    "bluezone_corporation_free_user_interface_sound_effects":   "ui",
    "bluezone_corporation_free_video_game_sound_effects":       "scifi",
    "bluezone_corporation_free_water_sound_effects":            "weather",
    "bluezone_corporation_free_weapon_sound_effects":           "weapon",
    "bluezone_corporation_free_wood_sound_effects":             "foley",
    # FreePD
    "comedy_mp3":           "cartoon",
    "comedy mp3":           "cartoon",
    "electronic_mp3":       "scifi",
    "electronic mp3":       "scifi",
    "epic_dramatic_mp3":    "cinematic",
    "epic dramatic mp3":    "cinematic",
    "fantasy_mp3":          "magic",
    "fantasy mp3":          "magic",
    "horror_mp3":           "horror",
    "horror mp3":           "horror",
    "world_mp3":            "ambience",
    "world mp3":            "ambience",
    # Reverb Impulse Files
    "reverb impulse files":                       "impulse_response",
    "alesis midiverb ii impulse response pack":   "impulse_response",
    "echotheifimpulseresponselibrary":            "impulse_response",
    # Seaweed Factory instruments
    "casio pt-10 sample pack":  "instrument",
    "casio_pt-10_sample_pack":  "instrument",
}

# ---------------------------------------------------------------------------
# TAG GROUPS
# Descriptor tags extracted from the filename stem after category is set.
# ---------------------------------------------------------------------------
TAG_GROUPS = {
    "close":       ["close up", "closeup", "close_up", " near ", " tight "],
    "distant":     ["distant", "distance", " far ", "faraway", "far_away"],
    "interior":    ["interior", "indoor", "inside"],
    "exterior":    ["exterior", "outdoor", "outside"],
    "large":       ["large", " big ", "heavy", "massive", "huge", "giant"],
    "small":       ["small", "tiny", "little", " mini ", " light "],
    "medium":      [" medium ", " mid ", " middle "],
    "metal":       ["metal", "metallic", "steel", "iron", "aluminum", "brass"],
    "wood":        [" wood ", "wooden", "timber", "plank"],
    "stone":       ["stone", " rock ", "concrete", "cement", "gravel", "dirt"],
    "water":       [" water ", " wet ", "liquid", "splash", " drip ", " flow "],
    "paper":       ["paper", "cardboard"],
    "fabric":      ["cloth", "fabric", "textile", "leather"],
    "clean":       [" clean ", " clear ", " dry "],
    "distorted":   ["distort", "corrupt", "glitch", "broken"],
    "reversed":    ["reverse", "reversed", "backward", "rewind"],
    "loop":        [" loop ", "looping", "cycled"],
    "designed":    ["designed", "processed", "synthesized"],
    "dark":        [" dark ", "evil", "sinister", "ominous", "creepy"],
    "bright":      ["bright", "happy", "warm", "cheerful"],
    "tense":       ["tension", "suspense", "tense", "thriller"],
    "epic":        ["epic", "powerful", "massive"],
    "crowd":       ["crowd", "walla", "audience", "spectators"],
    "stereo":      ["stereo", " lr ", "(lr)"],
    "mono":        [" mono ", "_mono"],
    "high_quality": ["96khz", "24bit", "24_96", "hires"],
}


def classify(stem: str, path_parts: tuple) -> Tuple[str, List[str]]:
    """
    Return (category, tags) for an audio file.

    Pass 1: check ancestor folder names against FOLDER_CATEGORY_MAP.
    Pass 2: keyword scan of stem + path parts against CATEGORY_MAP.
    """
    search_text = " " + " ".join(path_parts).lower() + " "
    stem_lower = " " + stem.lower().replace("_", " ").replace("-", " ") + " "

    # Pass 1 — folder-based lookup (most reliable for well-organized libraries)
    cat = None
    for part in reversed(path_parts[:-1]):
        key_us = part.lower().strip()
        key_sp = part.lower().replace("_", " ").strip()
        if key_us in FOLDER_CATEGORY_MAP:
            cat = FOLDER_CATEGORY_MAP[key_us]
            break
        if key_sp in FOLDER_CATEGORY_MAP:
            cat = FOLDER_CATEGORY_MAP[key_sp]
            break

    # Pass 2 — keyword scan
    if cat is None:
        for category, keywords in CATEGORY_MAP.items():
            for kw in keywords:
                kw_l = kw.lower()
                if kw_l in search_text:
                    cat = category
                    break
            if cat:
                break

    if cat is None:
        cat = "other"

    # Tag extraction from filename stem only
    tags: List[str] = []
    seen: set = set()
    for tag_name, keywords in TAG_GROUPS.items():
        for kw in keywords:
            if kw.lower() in stem_lower:
                if tag_name not in seen:
                    tags.append(tag_name)
                    seen.add(tag_name)
                break

    return cat, tags
