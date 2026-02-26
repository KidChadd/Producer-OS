from __future__ import annotations

from typing import TypedDict


class FLIconEntry(TypedDict):
    label: str
    icon_index: int
    code_hex: str
    tags: list[str]


def _entry(label: str, icon_hex: str, *tags: str) -> FLIconEntry:
    value = int(icon_hex, 16)
    return {
        "label": label,
        "icon_index": value,
        "code_hex": icon_hex.upper(),
        "tags": [t.lower() for t in tags],
    }


FL_ICON_FAVORITES: list[FLIconEntry] = [
    _entry("Folder", "F07B", "folder", "pack", "kit"),
    _entry("Music Note", "F001", "music", "melody", "audio"),
    _entry("Drum", "F569", "drum", "percussion", "kit"),
    _entry("Waveform", "F8F2", "wave", "sample", "audio"),
    _entry("Play", "F04B", "play", "run", "transport"),
    _entry("Stop", "F04D", "stop", "transport"),
    _entry("Sliders", "F1DE", "settings", "options", "controls"),
    _entry("Cog", "F013", "settings", "config"),
    _entry("Bolt", "F0E7", "fx", "effect", "fast"),
    _entry("Sparkles", "F890", "fx", "magic", "shine"),
    _entry("Fire", "F06D", "hot", "trap", "808"),
    _entry("Meteor", "F753", "impact", "fx", "cinematic"),
    _entry("Microphone", "F130", "vox", "vocal", "voice"),
    _entry("Headphones", "F025", "monitor", "audio", "listen"),
    _entry("Volume Up", "F028", "audio", "loud"),
    _entry("Keyboard", "F11C", "keys", "piano", "midi"),
    _entry("Guitar", "F7A6", "guitar", "instrument"),
    _entry("Bass Guitar", "F8D3", "bass", "instrument"),
    _entry("Bell", "F0A2", "bell", "pluck", "lead"),
    _entry("Magic Wand", "F0D0", "lead", "synth", "fx"),
    _entry("Clock", "F017", "loop", "time", "tempo"),
    _entry("Sync", "F2F1", "loop", "cycle", "repeat"),
    _entry("Redo", "F01E", "loop", "repeat"),
    _entry("Circle", "F111", "kick", "sub", "808"),
    _entry("Dot Circle", "F192", "snare", "clap", "hit"),
    _entry("Bullseye", "F140", "kick", "drum", "impact"),
    _entry("Asterisk", "F069", "hat", "cymbal", "shine"),
    _entry("Sun", "F185", "cymbal", "bright"),
    _entry("Cloud", "F0C2", "pad", "ambient", "fx"),
    _entry("Ghost", "F6E2", "fx", "spooky", "texture"),
    _entry("Robot", "F544", "vox", "robot", "vocal", "fx"),
    _entry("Wave Square", "F83E", "loop", "wave", "osc"),
    _entry("Chart Line", "F201", "glide", "808", "pitch"),
    _entry("Arrow Down", "F063", "down", "glide", "slide"),
    _entry("Arrow Up", "F062", "up", "rise", "fx"),
    _entry("Layer Group", "F5FD", "stack", "layers", "samples"),
    _entry("Boxes", "F468", "pack", "multi", "bundle"),
    _entry("File Audio", "F1C7", "audio", "sample", "file"),
    _entry("Clipboard", "F328", "one-shot", "shots", "clipboard"),
    _entry("Random", "F074", "perc", "shuffle", "variation"),
    _entry("Stars", "F762", "favorite", "premium"),
    _entry("Tag", "F02B", "label", "category"),
    _entry("Palette", "F53F", "color", "style", "theme"),
]

