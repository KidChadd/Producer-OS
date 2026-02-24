import json
import os
from pathlib import Path

import sys
import pytest

# Add the src directory to sys.path so that producer_os can be imported
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from producer_os.engine import ProducerOSEngine
from producer_os.styles_service import StyleService
from producer_os.bucket_service import BucketService


def create_dummy_inbox(tmp_path: Path) -> Path:
    """Create a dummy inbox with a single pack containing a few files."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    pack = inbox / "PackA"
    pack.mkdir()
    # Create files: one clearly 808, one kick, one unknown
    (pack / "808_sub.wav").write_text("dummy", encoding="utf-8")
    (pack / "kick.wav").write_text("dummy", encoding="utf-8")
    (pack / "unknown.txt").write_text("dummy", encoding="utf-8")
    return inbox


def load_default_styles() -> dict:
    """Load the bundled default style definitions."""
    here = Path(__file__).resolve().parents[1]
    style_path = here / "src" / "bucket_styles.json"
    assert style_path.exists(), f"Default styles file missing at {style_path}"
    return json.loads(style_path.read_text(encoding="utf-8"))


def test_nfo_placement_and_no_per_wav(tmp_path):
    inbox = create_dummy_inbox(tmp_path)
    hub = tmp_path / "hub"
    hub.mkdir()
    style_data = load_default_styles()
    style_service = StyleService(style_data)
    bucket_service = BucketService({})
    engine = ProducerOSEngine(inbox, hub, style_service, config={}, bucket_service=bucket_service)
    # Run copy mode
    report = engine.run(mode="copy")
    # Expect at least one file processed
    assert report["files_processed"] > 0
    # Category nfo should exist for Samples (the primary category for 808s and kicks)
    category_nfo = hub / "Samples.nfo"
    assert category_nfo.exists(), "Category .nfo missing"
    # There should be no .nfo files next to individual audio files
    for root, dirs, files in os.walk(hub):
        for f in files:
            if f.endswith(".nfo"):
                continue
            # Ensure no file has a sibling nfo with same stem
            stem = Path(f).stem
            sibling_nfo = Path(root) / f"{stem}.nfo"
            assert not sibling_nfo.exists(), f"Per-file .nfo found for {f}"
    # Bucket and pack .nfo files exist in some directory under hub
    nfo_files = list(hub.rglob("*.nfo"))
    # Expect at least 3 distinct .nfo files: category, bucket, pack
    assert len(nfo_files) >= 3


def test_idempotency(tmp_path):
    inbox = create_dummy_inbox(tmp_path)
    hub = tmp_path / "hub"
    hub.mkdir()
    style_data = load_default_styles()
    style_service = StyleService(style_data)
    bucket_service = BucketService({})
    engine = ProducerOSEngine(inbox, hub, style_service, config={}, bucket_service=bucket_service)
    # First run copies files
    report1 = engine.run(mode="copy")
    first_moved = report1["files_copied"]
    # Second run should not copy any additional files
    report2 = engine.run(mode="copy")
    second_moved = report2["files_copied"]
    assert second_moved == 0, "Second run should not copy any files"


# ----------------------------------------------------------------------
# New tests for hybrid classification

import numpy as np
import soundfile as sf

def generate_sine(duration: float, sr: int = 44100, freq: float = 60.0) -> np.ndarray:
    """Generate a pure sine wave for the given duration and frequency."""
    t = np.linspace(0.0, duration, int(sr * duration), False)
    return np.sin(2 * np.pi * freq * t)

def generate_transient_kick(duration: float = 0.3, sr: int = 44100, freq: float = 60.0) -> np.ndarray:
    """Generate a kick-like transient: strong attack and rapid decay."""
    t = np.linspace(0.0, duration, int(sr * duration), False)
    envelope = np.exp(-t * 8.0)
    x = envelope * np.sin(2 * np.pi * freq * t)
    # Emphasize the initial attack
    attack_len = int(0.01 * sr)
    if attack_len > 0:
        x[:attack_len] *= 4.0
    return x

def generate_glide(duration: float = 1.0, sr: int = 44100, f_start: float = 65.0, f_end: float = 45.0) -> np.ndarray:
    """Generate a decaying sine with a downward pitch glide."""
    t = np.linspace(0.0, duration, int(sr * duration), False)
    # Exponential frequency glide
    ratio = f_end / f_start
    inst_freq = f_start * (ratio ** (t / duration))
    # Integrate instantaneous frequency to phase
    phase = 2 * np.pi * np.cumsum(inst_freq) / sr
    x = np.sin(phase) * np.exp(-t)  # apply decay envelope
    return x

def test_folder_hint_detection(tmp_path):
    """Files in folders containing bucket keywords should receive strong folder hint."""
    inbox = tmp_path / "inbox"
    pack = inbox / "808sPack"
    pack.mkdir(parents=True)
    sr = 22050
    x = generate_sine(0.5, sr)
    (pack / "01.wav").parent.mkdir(parents=True, exist_ok=True)
    sf.write(pack / "01.wav", x, sr)
    hub = tmp_path / "hub"
    hub.mkdir()
    style_service = StyleService(load_default_styles())
    engine = ProducerOSEngine(inbox, hub, style_service, config={}, bucket_service=BucketService({}))
    report = engine.run(mode="copy")
    # Inspect the reported bucket for our file
    packs = report["packs"]
    found_bucket = None
    for p in packs:
        for f in p["files"]:
            if f["source"].endswith("01.wav"):
                found_bucket = f["bucket"]
    assert found_bucket == "808s", f"Folder hint failed: expected '808s', got {found_bucket}"

def test_audio_override_kick(tmp_path):
    """Kick-like audio should override folder hint for 808s when evidence strong."""
    inbox = tmp_path / "inbox"
    pack = inbox / "808sFolder"
    pack.mkdir(parents=True)
    sr = 22050
    x = generate_transient_kick(duration=0.3, sr=sr, freq=60.0)
    sf.write(pack / "kicktest.wav", x, sr)
    hub = tmp_path / "hub"
    hub.mkdir()
    style_service = StyleService(load_default_styles())
    engine = ProducerOSEngine(inbox, hub, style_service, config={}, bucket_service=BucketService({}))
    report = engine.run(mode="copy")
    found_bucket = None
    for p in report["packs"]:
        for f in p["files"]:
            if f["source"].endswith("kicktest.wav"):
                found_bucket = f["bucket"]
    assert found_bucket == "Kicks", f"Audio override failed: expected 'Kicks', got {found_bucket}"

def test_glide_detection(tmp_path):
    """Tonal glide audio should be classified as 808s and detect glide."""
    inbox = tmp_path / "inbox"
    pack = inbox / "pack"
    pack.mkdir(parents=True)
    sr = 22050
    x = generate_glide(duration=1.0, sr=sr, f_start=65.0, f_end=45.0)
    sf.write(pack / "glide.wav", x, sr)
    hub = tmp_path / "hub"
    hub.mkdir()
    style_service = StyleService(load_default_styles())
    engine = ProducerOSEngine(inbox, hub, style_service, config={}, bucket_service=BucketService({}))
    # Use internal classification to inspect glide detection details
    file_path = pack / "glide.wav"
    bucket, category, confidence, candidates, low_confidence, reason = engine._classify_file(file_path)
    assert bucket == "808s", f"Glide detection bucket mismatch: expected '808s', got {bucket}"
    glide_summary = reason.get("glide_summary", {})
    assert glide_summary.get("glide_detected", False), "Glide not detected for glide sample"

def test_low_confidence_marking(tmp_path):
    """Ambiguous noise should result in low confidence but still choose a bucket."""
    inbox = tmp_path / "inbox"
    pack = inbox / "noisePack"
    pack.mkdir(parents=True)
    # Generate random noise
    sr = 22050
    x = np.random.randn(int(sr * 0.5)) * 0.1
    sf.write(pack / "noise.wav", x, sr)
    hub = tmp_path / "hub"
    hub.mkdir()
    style_service = StyleService(load_default_styles())
    engine = ProducerOSEngine(inbox, hub, style_service, config={}, bucket_service=BucketService({}))
    bucket, category, confidence, candidates, low_confidence, reason = engine._classify_file(pack / "noise.wav")
    assert low_confidence, "Noise sample should be marked as low confidence"
    # Ensure a bucket is still chosen (not None)
    assert bucket is not None, "Noise sample should still choose a bucket"
