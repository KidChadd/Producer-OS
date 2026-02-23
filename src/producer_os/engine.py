"""Core engine for Producer OS (v2).

The :class:`ProducerOSEngine` exposes methods to scan an inbox
directory, classify audio files into deterministic buckets, move or
copy them into a structured hub directory, write `.nfo` sidecar
files with styling information, and generate logs and reports.  It
also supports undoing the last run and repairing inconsistent
styles.

This v2 version introduces support for bucket rename mappings via
:class:`producer_os.bucket_service.BucketService` and uses the
standard *src layout* for packaging.  It remains intentionally
decoupled from any user interface and depends only on
:class:`producer_os.config_service.ConfigService`,
:class:`producer_os.styles_service.StyleService`, and
:class:`producer_os.bucket_service.BucketService`.  This separation
allows both the GUI wizard and the command‑line interface to share the
same core logic.
"""

from __future__ import annotations

import csv
import datetime
import json
import os
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .styles_service import StyleService
from .bucket_service import BucketService

import numpy as np  # type: ignore
import librosa  # type: ignore
import soundfile as sf  # type: ignore
import re

# ---------------------------------------------------------------------------
# Tuning constants
# These constants control the weighting and thresholds used by the hybrid
# classification algorithm.  They can be overridden at runtime via a
# `tuning.json` file placed in the Producer OS configuration directory.  See
# the specification for details.
FOLDER_HINT_WEIGHT = 50
FILENAME_HINT_WEIGHT = 25
FOLDER_HINT_CAP = 80
FILENAME_HINT_CAP = 40

LOW_CONFIDENCE_THRESHOLD = 0.75
PARENT_FOLDER_LEVELS_TO_SCAN = 5

FEATURE_THRESHOLDS = {
    "808_duration_min": 0.45,
    "kick_duration_max": 0.35,
    "lowfreq_ratio_808": 0.60,
    "lowfreq_ratio_hat_max": 0.20,
    "centroid_bright": 4000,
    "centroid_low": 300,
    "transient_kick_min": 3.0,
    "zcr_tonal_max": 0.08,
    "flatness_high": 0.3,
    "zcr_high": 0.1,
    "centroid_moderate_low": 1000,
    "centroid_moderate_high": 3000,
}

AUDIO_WEIGHTS = {
    "duration": 10,
    "lowfreq": 15,
    "centroid": 10,
    "transient": 20,
    "zcr": 10,
    "flatness": 10,
}

PITCH_WEIGHTS = {
    "median_f0_low": 20,
    "voiced_ratio": 10,
    "glide_bonus": 10,
    "stability_bonus": 10,
}

def _clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamp val between min_val and max_val."""
    return max(min_val, min(max_val, val))


# A classification is represented as a tuple:
# (bucket_name or None, category_name, confidence, list of (bucket, score) candidates)
ClassificationResult = Tuple[Optional[str], str, float, List[Tuple[str, int]]]


@dataclass
class ProducerOSEngine:
    """Producer OS engine responsible for file routing and styling."""

    inbox_dir: Path
    hub_dir: Path
    style_service: StyleService
    config: Dict[str, any]
    bucket_service: BucketService = field(default_factory=BucketService)
    ignore_rules: Iterable[str] = field(default_factory=lambda: ["__MACOSX", ".DS_Store", "._"])
    confidence_threshold: float = 0.75

    # Bucket rules: maps bucket names to lists of substrings to search for
    BUCKET_RULES: Dict[str, List[str]] = field(default_factory=lambda: {
        "808s": ["808", "808s"],
        "Kicks": ["kick", "kicks"],
        "Snares": ["snare", "snares"],
        "Claps": ["clap", "claps"],
        "HiHats": ["hihat", "hi-hat", "hat", "hats"],
        "Percs": ["perc", "percs", "percussion"],
        "Cymbals": ["cymbal", "cymbals", "crash", "ride", "bell"],
        "Bass": ["bass"],
        "Leads": ["lead", "leads"],
        "Vox": ["vox", "vocal", "vocals", "acapella"],
        "FX": ["fx", "effect", "effects", "sweep", "sweeps", "riser", "risers", "impact", "impacts"],
        "DrumLoop": [
            "drumloop",
            "drum_loop",
            "drum loop",
            "drum-loop",
            "loop drum",
            "loop_drums",
        ],
        "MelodyLoop": [
            "melodic loop",
            "melodyloop",
            "melody_loop",
            "melody loop",
            "loop melody",
            "melod",
            "chord",
            "chords",
            "guitar loop",
            "piano loop",
        ],
        "MIDI": [".mid", "mid file"],
    })
    # Map buckets to categories
    CATEGORY_MAP: Dict[str, str] = field(default_factory=lambda: {
        "808s": "Samples",
        "Kicks": "Samples",
        "Snares": "Samples",
        "Claps": "Samples",
        "HiHats": "Samples",
        "Percs": "Samples",
        "Cymbals": "Samples",
        "Bass": "Samples",
        "Leads": "Samples",
        "Vox": "Samples",
        "FX": "Samples",
        "DrumLoop": "Loops",
        "MelodyLoop": "Loops",
        "MIDI": "MIDI",
    })

    # Internal caches and tuning overrides
    # These fields are initialised in __post_init__
    _feature_cache: Dict[str, dict] = field(init=False, default_factory=dict)
    _tuning_loaded: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        """Post-initialisation hook to load tuning constants and feature cache."""
        # Load tuning overrides from config if available
        self._load_tuning_overrides()
        # Load persistent feature cache
        self._load_feature_cache()

    # ------------------------------------------------------------------
    # Tuning overrides and feature caching
    def _load_tuning_overrides(self) -> None:
        """
        Load tuning constant overrides from a tuning.json file in the
        configuration directory.  The tuning file should be a JSON
        object with keys matching the global constants defined above.
        Unknown keys are ignored.  Only simple float/int values are
        allowed.  This method updates the module‑level constants via
        globals().  It is safe to call this multiple times; values are
        only overridden once.
        """
        if self._tuning_loaded:
            return
        # Determine potential locations for tuning.json.  First check
        # configuration path in self.config, then hub directory.
        tuning_paths = []
        # config may specify a 'config_path' or similar; fallback to app data
        if isinstance(self.config, dict):
            for key in ["config_path", "config_dir", "tuning_path"]:
                path = self.config.get(key)
                if path:
                    tuning_paths.append(Path(path) / "tuning.json")
        # Always check hub directory for tuning.json
        tuning_paths.append(self.hub_dir / "tuning.json")
        for path in tuning_paths:
            try:
                if path and path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Update constants if keys match
                    for key, value in data.items():
                        if key in globals():
                            try:
                                # Only accept numeric or dict values
                                if isinstance(value, (int, float)):
                                    globals()[key] = value
                                elif isinstance(value, dict):
                                    # Update nested dicts like FEATURE_THRESHOLDS
                                    if isinstance(globals()[key], dict):
                                        globals()[key].update(value)
                            except Exception:
                                continue
                    self._tuning_loaded = True
                    break
            except Exception:
                continue

    def _load_feature_cache(self) -> None:
        """Load feature cache from a persistent JSON file in the hub directory."""
        cache_path = self.hub_dir / "feature_cache.json"
        self._feature_cache = {}
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._feature_cache = data
            except Exception:
                # ignore cache errors
                self._feature_cache = {}

    def _save_feature_cache(self) -> None:
        """Persist feature cache to JSON in the hub directory."""
        cache_path = self.hub_dir / "feature_cache.json"
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(self._feature_cache, f)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Feature extraction and scoring
    def _get_folder_hint_scores(self, file_path: Path) -> Dict[str, int]:
        """
        Compute folder hint scores for each bucket by scanning up to
        ``PARENT_FOLDER_LEVELS_TO_SCAN`` parent directories.  Each
        occurrence of a bucket keyword in a parent directory name adds
        ``FOLDER_HINT_WEIGHT`` points, capped at ``FOLDER_HINT_CAP``.
        """
        scores: Dict[str, int] = {bucket: 0 for bucket in self.BUCKET_RULES.keys()}
        # Resolve relative to inbox to avoid scanning outside project root
        parts = list(file_path.parent.parts)[-PARENT_FOLDER_LEVELS_TO_SCAN:]
        for part in parts:
            part_lower = part.lower()
            for bucket, patterns in self.BUCKET_RULES.items():
                for pat in patterns:
                    if pat.lower() in part_lower:
                        scores[bucket] += FOLDER_HINT_WEIGHT
        # Cap scores
        for bucket in scores:
            if scores[bucket] > FOLDER_HINT_CAP:
                scores[bucket] = FOLDER_HINT_CAP
        return scores

    def _get_filename_hint_scores(self, filename: str) -> Dict[str, int]:
        """
        Compute filename hint scores for each bucket by counting keyword
        occurrences.  Each match adds ``FILENAME_HINT_WEIGHT`` points,
        capped at ``FILENAME_HINT_CAP``.
        """
        scores: Dict[str, int] = {bucket: 0 for bucket in self.BUCKET_RULES.keys()}
        lower_name = filename.lower()
        for bucket, patterns in self.BUCKET_RULES.items():
            count = 0
            for pat in patterns:
                # skip MIDI special case (handled separately via BUCKET_RULES)
                if pat == ".mid":
                    continue
                if pat.lower() in lower_name:
                    count += 1
            if count > 0:
                val = count * FILENAME_HINT_WEIGHT
                if val > FILENAME_HINT_CAP:
                    val = FILENAME_HINT_CAP
                scores[bucket] = val
        return scores

    def _extract_features(self, file_path: Path) -> dict:
        """
        Extract audio features from a WAV file.  Results are cached
        across runs using file path, size and modification time as
        keys.  The returned dictionary contains duration, low
        frequency ratio, spectral centroid, transient strength, zero
        crossing rate, spectral flatness, pitch features and glide
        metrics.
        """
        # Build cache key
        try:
            stat = file_path.stat()
            key = f"{file_path}|{stat.st_size}|{int(stat.st_mtime)}"
        except Exception:
            key = str(file_path)
        # Return cached features if present
        if key in self._feature_cache:
            return self._feature_cache[key]
        features: dict = {}
        try:
            # Load audio
            # Use soundfile first for reliability; fallback to librosa if needed
            data, sr = sf.read(str(file_path), always_2d=False)
            if isinstance(data, list) or isinstance(data, tuple):
                data = np.array(data)
            # Convert to mono if necessary
            if data.ndim == 2:
                data = np.mean(data, axis=1)
            y = data.astype(float)
            # Normalise for analysis (do not modify original file)
            max_val = np.max(np.abs(y)) if np.max(np.abs(y)) > 0 else 1.0
            y_norm = y / max_val
            N = len(y_norm)
            duration = float(N) / float(sr)
            features["duration"] = duration
            # Frame params
            win = 2048
            hop = 512
            # Compute STFT magnitude
            S = np.abs(librosa.stft(y_norm, n_fft=win, hop_length=hop, window="hann"))
            # Power spectrum
            P = S ** 2
            # Frequencies for FFT bins
            freqs = librosa.fft_frequencies(sr=sr, n_fft=win)
            # Total power and low frequency power
            total_power = np.sum(P)
            low_mask = freqs < 120.0
            low_power = np.sum(P[low_mask, :]) if P.size > 0 else 0.0
            low_ratio = float(low_power) / float(total_power + 1e-9)
            features["low_freq_ratio"] = low_ratio
            # RMS per frame
            rms = librosa.feature.rms(S=S, hop_length=hop)[0]
            # Transient strength: early vs mid
            # Determine number of frames for early and mid windows
            early_frames = int(np.ceil(0.08 * sr / hop))
            mid_frames = int(np.ceil(0.20 * sr / hop))
            if len(rms) > 0:
                peak_early = float(np.max(rms[:early_frames])) if early_frames > 0 else float(np.max(rms))
                start_mid = early_frames
                end_mid = min(start_mid + mid_frames, len(rms))
                if end_mid > start_mid:
                    median_mid = float(np.median(rms[start_mid:end_mid]))
                else:
                    median_mid = float(np.median(rms))
                transient_strength = peak_early / (median_mid + 1e-9)
            else:
                transient_strength = 0.0
            features["transient_strength"] = transient_strength
            # Spectral centroid per frame
            centroid = librosa.feature.spectral_centroid(S=S, sr=sr, hop_length=hop)[0]
            centroid_mean = float(np.mean(centroid)) if centroid.size > 0 else 0.0
            # Early centroid: first 100ms
            early_centroid_frames = int(np.ceil(0.10 * sr / hop))
            if centroid.size > 0 and early_centroid_frames > 0:
                centroid_early = float(np.mean(centroid[:early_centroid_frames]))
            else:
                centroid_early = centroid_mean
            features["centroid_mean"] = centroid_mean
            features["centroid_early"] = centroid_early
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y_norm, frame_length=win, hop_length=hop)[0]
            zcr_mean = float(np.mean(zcr)) if zcr.size > 0 else 0.0
            features["zcr_mean"] = zcr_mean
            # Spectral flatness
            flatness = librosa.feature.spectral_flatness(S=S)[0]
            flatness_mean = float(np.mean(flatness)) if flatness.size > 0 else 0.0
            features["flatness_mean"] = flatness_mean
            # Pitch detection using librosa.yin
            try:
                f0 = librosa.yin(y_norm, fmin=20, fmax=2000, sr=sr, frame_length=win, hop_length=hop)
                # Mark invalid frames as NaN; librosa.yin returns np.nan for unvoiced
                valid_mask = ~np.isnan(f0)
                voiced_ratio = float(np.sum(valid_mask)) / float(len(f0)) if len(f0) > 0 else 0.0
                features["voiced_ratio"] = voiced_ratio
                if np.any(valid_mask):
                    median_f0 = float(np.median(f0[valid_mask]))
                    features["median_f0"] = median_f0
                    # Convert to semitones for stability and glide detection
                    s = 12.0 * np.log2(f0[valid_mask] / 55.0)
                    s_std = float(np.std(s)) if s.size > 0 else 0.0
                    features["pitch_std"] = s_std
                else:
                    median_f0 = None
                    s_std = None
                    features["median_f0"] = 0.0
                    features["pitch_std"] = 0.0
                # Glide detection
                glide_info = self._detect_glide(f0, sr, win, hop)
                features.update(glide_info)
            except Exception:
                features["voiced_ratio"] = 0.0
                features["median_f0"] = 0.0
                features["pitch_std"] = 0.0
                features.update({"glide_detected": False, "glide_confidence": 0.0, "glide_drop": 0.0})
        except Exception:
            # If audio cannot be processed, return zeroed features
            features = {
                "duration": 0.0,
                "low_freq_ratio": 0.0,
                "transient_strength": 0.0,
                "centroid_mean": 0.0,
                "centroid_early": 0.0,
                "zcr_mean": 0.0,
                "flatness_mean": 0.0,
                "voiced_ratio": 0.0,
                "median_f0": 0.0,
                "pitch_std": 0.0,
                "glide_detected": False,
                "glide_confidence": 0.0,
                "glide_drop": 0.0,
            }
        # Cache features
        self._feature_cache[key] = features
        return features

    def _detect_glide(self, f0: np.ndarray, sr: int, win: int, hop: int) -> dict:
        """
        Detect pitch glide on the provided f0 array.  Returns a dict
        with keys: 'glide_detected', 'glide_confidence', 'glide_drop'.

        The implementation follows a robust method: convert f0 to
        semitones, smooth with median and mean filters, trim the
        first and last 10%% of voiced frames, estimate slope using
        a robust median slope (Theil–Sen), compute drop in semitones
        between robust start and end medians, compute a MAD to
        determine fit quality, and decide glide presence based on
        drop, slope and stability thresholds.  A confidence score
        between 0 and 1 is returned based on the magnitude of
        the drop, slope, voiced ratio and MAD.
        """
        result = {
            "glide_detected": False,
            "glide_confidence": 0.0,
            "glide_drop": 0.0,
        }
        try:
            if f0 is None or len(f0) == 0:
                return result
            # Valid frames mask
            valid_mask = ~np.isnan(f0)
            total_frames = len(f0)
            voiced_count = int(np.sum(valid_mask))
            voiced_ratio = voiced_count / total_frames if total_frames > 0 else 0.0
            # Guardrails
            if total_frames == 0 or voiced_count == 0:
                return result
            # Approximate duration from number of frames
            duration = (total_frames * hop) / float(sr)
            if duration < 0.35 or voiced_ratio < 0.35:
                return result
            # Extract voiced semitone series
            voiced_f0 = f0[valid_mask]
            t = np.arange(len(voiced_f0)) * (hop / float(sr))
            s = 12.0 * np.log2(voiced_f0 / 55.0)
            # Smooth: median then mean filters with window size 5
            from scipy.ndimage import median_filter
            s_med = median_filter(s, size=5, mode="nearest")
            s_smooth = np.convolve(s_med, np.ones(5)/5, mode="same")
            # Trim 10%% at start/end
            n = len(s_smooth)
            if n < 15:
                return result
            start_idx = int(np.floor(n * 0.10))
            end_idx = int(np.floor(n * 0.90))
            if end_idx <= start_idx:
                return result
            t_u = t[start_idx:end_idx]
            s_u = s_smooth[start_idx:end_idx]
            # Theil–Sen slope (median of pairwise slopes)
            # To avoid O(n^2) complexity for large arrays, downsample if necessary
            # Use pairwise slopes on up to 100 points
            max_pts = 100
            if len(t_u) > max_pts:
                idxs = np.linspace(0, len(t_u) - 1, max_pts, dtype=int)
                t_sub = t_u[idxs]
                s_sub = s_u[idxs]
            else:
                t_sub = t_u
                s_sub = s_u
            slopes = []
            for i in range(len(t_sub)):
                for j in range(i+1, len(t_sub)):
                    dt = t_sub[j] - t_sub[i]
                    if dt <= 0:
                        continue
                    slopes.append((s_sub[j] - s_sub[i]) / dt)
            if not slopes:
                return result
            m = float(np.median(slopes))
            # Robust start and end medians
            q = len(s_u)
            q20 = int(np.floor(q * 0.2))
            start_med = float(np.median(s_u[:q20]))
            end_med = float(np.median(s_u[-q20:])) if q20 > 0 else float(np.median(s_u))
            drop_st = start_med - end_med
            # Fit line and residuals
            b = float(np.median(s_u - m * t_u))
            residuals = s_u - (m * t_u + b)
            mad = float(np.median(np.abs(residuals)))
            # Decision
            if drop_st >= 1.0 and m <= -2.0 and mad <= 0.35:
                # Compute confidence
                A = _clamp(drop_st / 6.0, 0.0, 1.0)
                B = _clamp((-m) / 10.0, 0.0, 1.0)
                C = _clamp((voiced_ratio - 0.35) / 0.35, 0.0, 1.0)
                D = _clamp((0.35 - mad) / 0.35, 0.0, 1.0)
                conf = 0.35*A + 0.25*B + 0.20*C + 0.20*D
                result["glide_detected"] = True
                result["glide_confidence"] = float(conf)
                result["glide_drop"] = float(drop_st)
            return result
        except Exception:
            return result

    def _compute_audio_scores(self, features: dict) -> Dict[str, float]:
        """
        Compute audio and pitch based scores for each bucket based on
        extracted feature values.  Each score is determined by comparing
        features to thresholds and adding weights as defined in
        ``AUDIO_WEIGHTS`` and ``PITCH_WEIGHTS``.  Returns a mapping
        from bucket names to scores.
        """
        scores: Dict[str, float] = {bucket: 0.0 for bucket in self.BUCKET_RULES.keys()}
        duration = features.get("duration", 0.0)
        low_ratio = features.get("low_freq_ratio", 0.0)
        centroid_mean = features.get("centroid_mean", 0.0)
        centroid_early = features.get("centroid_early", 0.0)
        transient = features.get("transient_strength", 0.0)
        zcr_mean = features.get("zcr_mean", 0.0)
        flatness_mean = features.get("flatness_mean", 0.0)
        voiced_ratio = features.get("voiced_ratio", 0.0)
        median_f0 = features.get("median_f0", 0.0)
        pitch_std = features.get("pitch_std", 0.0)
        glide_detected = features.get("glide_detected", False)
        glide_confidence = features.get("glide_confidence", 0.0)
        # 808s: if the sample looks kick‑like (short duration + strong transient),
        # suppress certain 808 bonuses so that kick may override folder hints.
        is_kick_like = (duration < FEATURE_THRESHOLDS["kick_duration_max"] and
                        transient > FEATURE_THRESHOLDS["transient_kick_min"])
        if not is_kick_like:
            if duration > FEATURE_THRESHOLDS["808_duration_min"]:
                scores["808s"] += AUDIO_WEIGHTS["duration"]
            if low_ratio > FEATURE_THRESHOLDS["lowfreq_ratio_808"]:
                scores["808s"] += AUDIO_WEIGHTS["lowfreq"]
            if centroid_mean < FEATURE_THRESHOLDS["centroid_low"]:
                scores["808s"] += AUDIO_WEIGHTS["centroid"]
            if zcr_mean < FEATURE_THRESHOLDS["zcr_tonal_max"]:
                scores["808s"] += AUDIO_WEIGHTS["zcr"]
            # Pitch bonuses for 808
            if 30 <= median_f0 <= 100:
                scores["808s"] += PITCH_WEIGHTS["median_f0_low"]
            if voiced_ratio >= 0.5:
                scores["808s"] += PITCH_WEIGHTS["voiced_ratio"]
            if glide_detected:
                scores["808s"] += PITCH_WEIGHTS["glide_bonus"] * glide_confidence
            if pitch_std is not None and pitch_std < 0.2:
                scores["808s"] += PITCH_WEIGHTS["stability_bonus"]
        # Kicks
        if duration < FEATURE_THRESHOLDS["kick_duration_max"]:
            scores["Kicks"] += AUDIO_WEIGHTS["duration"]
        if transient > FEATURE_THRESHOLDS["transient_kick_min"]:
            scores["Kicks"] += AUDIO_WEIGHTS["transient"]
        if centroid_early > FEATURE_THRESHOLDS["centroid_bright"]:
            scores["Kicks"] += AUDIO_WEIGHTS["centroid"]
        if voiced_ratio < 0.25:
            scores["Kicks"] += AUDIO_WEIGHTS["zcr"] * 0.5  # small bonus for non-tonal
        # Synergy: short duration and strong transient yields extra boost
        if (duration < FEATURE_THRESHOLDS["kick_duration_max"] and
            transient > FEATURE_THRESHOLDS["transient_kick_min"]):
            scores["Kicks"] += AUDIO_WEIGHTS["transient"] + AUDIO_WEIGHTS["duration"]
        # HiHats/Cymbals
        if centroid_mean > FEATURE_THRESHOLDS["centroid_bright"]:
            scores["HiHats"] += AUDIO_WEIGHTS["centroid"]
            scores["Cymbals"] += AUDIO_WEIGHTS["centroid"]
        if low_ratio < FEATURE_THRESHOLDS["lowfreq_ratio_hat_max"]:
            scores["HiHats"] += AUDIO_WEIGHTS["lowfreq"]
            scores["Cymbals"] += AUDIO_WEIGHTS["lowfreq"]
        if duration < 0.40:
            scores["HiHats"] += AUDIO_WEIGHTS["duration"]
            scores["Cymbals"] += AUDIO_WEIGHTS["duration"]
        if flatness_mean > FEATURE_THRESHOLDS["flatness_high"]:
            scores["HiHats"] += AUDIO_WEIGHTS["flatness"]
            scores["Cymbals"] += AUDIO_WEIGHTS["flatness"]
        # Snares and Claps
        if flatness_mean > 0.2 and zcr_mean > FEATURE_THRESHOLDS["zcr_high"]:
            scores["Snares"] += AUDIO_WEIGHTS["flatness"]
            scores["Claps"] += AUDIO_WEIGHTS["flatness"]
        if transient > 2.0:
            scores["Snares"] += AUDIO_WEIGHTS["transient"] * 0.5
            scores["Claps"] += AUDIO_WEIGHTS["transient"] * 0.5
        if FEATURE_THRESHOLDS["centroid_moderate_low"] <= centroid_mean <= FEATURE_THRESHOLDS["centroid_moderate_high"]:
            scores["Snares"] += AUDIO_WEIGHTS["centroid"] * 0.5
            scores["Claps"] += AUDIO_WEIGHTS["centroid"] * 0.5
        # Percs (generic catch‑all percussive)
        if transient > 1.5 and duration < 0.5:
            scores["Percs"] += AUDIO_WEIGHTS["transient"]
        # Vox (vocal / acapella) – not implemented in detail but favour high voiced ratio
        if voiced_ratio > 0.75 and centroid_mean < 2000:
            scores["Vox"] += AUDIO_WEIGHTS["duration"]
        # FX and others – basic heuristics: high flatness and long duration can indicate FX
        if flatness_mean > 0.5 and duration > 0.5:
            scores["FX"] += AUDIO_WEIGHTS["flatness"]
        return scores

    def _classify_file(self, file_path: Path) -> Tuple[Optional[str], str, float, List[Tuple[str, float]], bool, dict]:
        """
        Hybrid classification for a given file.  Returns a tuple of
        (bucket, category, confidence_ratio, candidates, low_confidence, reason).
        If no bucket scores above zero, bucket is None and category is
        "UNSORTED".  The ``candidates`` list contains tuples of
        (bucket, score) for the top three buckets.  The ``reason`` is
        a dictionary summarising the matching evidence.
        """
        # Default reason object
        reason = {
            "folder_matches": [],
            "filename_matches": [],
            "audio_summary": {},
            "pitch_summary": {},
            "glide_summary": {},
        }
        # Determine file type
        suffix = file_path.suffix.lower()
        # Skip ignored names
        if self._should_ignore(file_path.name):
            return (None, "UNSORTED", 0.0, [], False, reason)
        # Non-WAV classification fallback
        if suffix != ".wav":
            # Use original filename-based classifier for non-wav
            bucket, category, confidence, candidates = self._classify_filename(file_path.name)
            low_confidence = False
            if bucket is None:
                low_confidence = True
            # Build reason based on candidate scores
            reason["filename_matches"] = [(b, s) for b, s in candidates]
            return (bucket, category, confidence, candidates, low_confidence, reason)
        # For WAV, perform hybrid analysis
        # Compute folder and filename hint scores
        folder_scores = self._get_folder_hint_scores(file_path)
        filename_scores = self._get_filename_hint_scores(file_path.name)
        # Extract audio features and compute audio scores
        features = self._extract_features(file_path)
        audio_scores = self._compute_audio_scores(features)
        # Combine scores
        final_scores: Dict[str, float] = {}
        for bucket in self.BUCKET_RULES.keys():
            final_scores[bucket] = folder_scores.get(bucket, 0) + filename_scores.get(bucket, 0) + audio_scores.get(bucket, 0)
        # Determine candidates
        # Filter buckets with positive scores
        positive_scores = {b: s for b, s in final_scores.items() if s > 0}
        if not positive_scores:
            # Nothing matched – unsorted
            # Build reason dictionary
            reason["folder_matches"] = [(b, s) for b, s in folder_scores.items() if s > 0]
            reason["filename_matches"] = [(b, s) for b, s in filename_scores.items() if s > 0]
            reason["audio_summary"] = features
            return (None, "UNSORTED", 0.0, [], False, reason)
        # Sort scores descending
        sorted_scores = sorted(positive_scores.items(), key=lambda kv: kv[1], reverse=True)
        best_bucket, best_score = sorted_scores[0]
        # Top 3 candidates (include bucket even if score 0 for completeness)
        top3 = sorted_scores[:3]
        # Compute confidence ratio and margin
        sum_top3 = sum([score for _, score in top3])
        confidence_ratio = best_score / sum_top3 if sum_top3 > 0 else 1.0
        confidence_margin = best_score - (top3[1][1] if len(top3) > 1 else 0.0)
        low_confidence = confidence_ratio < LOW_CONFIDENCE_THRESHOLD
        # Compose reason details
        reason["folder_matches"] = [(b, s) for b, s in folder_scores.items() if s > 0]
        reason["filename_matches"] = [(b, s) for b, s in filename_scores.items() if s > 0]
        reason["audio_summary"] = {
            "duration": features.get("duration"),
            "low_freq_ratio": features.get("low_freq_ratio"),
            "transient_strength": features.get("transient_strength"),
            "centroid_mean": features.get("centroid_mean"),
            "centroid_early": features.get("centroid_early"),
            "zcr_mean": features.get("zcr_mean"),
            "flatness_mean": features.get("flatness_mean"),
        }
        reason["pitch_summary"] = {
            "median_f0": features.get("median_f0"),
            "voiced_ratio": features.get("voiced_ratio"),
            "pitch_std": features.get("pitch_std"),
        }
        reason["glide_summary"] = {
            "glide_detected": features.get("glide_detected"),
            "glide_confidence": features.get("glide_confidence"),
            "glide_drop": features.get("glide_drop"),
        }
        # Category
        category = self.CATEGORY_MAP.get(best_bucket, "Samples")
        return (best_bucket, category, confidence_ratio, top3, low_confidence, reason)

    def _should_ignore(self, name: str) -> bool:
        """Return True if the file or folder name should be ignored."""
        for rule in self.ignore_rules:
            # rule may be prefix (e.g., '._'), exact file, or directory name
            if name == rule or name.startswith(rule):
                return True
        return False

    def _classify_filename(self, filename: str) -> ClassificationResult:
        """Classify a filename into a bucket and category.

        Returns a ``ClassificationResult``.  The string matching is case
        insensitive and counts the number of occurrences of each rule’s
        substrings.  The top three buckets by score are returned in
        ``candidates``.
        """
        lower_name = filename.lower()
        scores: Dict[str, int] = {}
        for bucket, patterns in self.BUCKET_RULES.items():
            score = 0
            for pat in patterns:
                # treat .mid extension specially
                if pat == ".mid" and lower_name.endswith(".mid"):
                    score += 3  # strong match for MIDI
                else:
                    count = lower_name.count(pat)
                    score += count
            if score > 0:
                scores[bucket] = score
        if not scores:
            return (None, "UNSORTED", 0.0, [])
        # Sort buckets by score descending
        sorted_scores = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        total = sum(scores.values())
        best_bucket, best_score = sorted_scores[0]
        confidence = best_score / total if total > 0 else 0.0
        candidates = sorted_scores[:3]
        if confidence >= self.confidence_threshold:
            category = self.CATEGORY_MAP.get(best_bucket, "Samples")
            return (best_bucket, category, confidence, candidates)
        # Low confidence – route to UNSORTED
        return (None, "UNSORTED", confidence, candidates)

    def _wrap_loose_files(self) -> None:
        """Wrap loose files in the inbox root into a timestamped folder.

        Some sample packs consist of individual files placed directly in
        the inbox root instead of inside a dedicated folder.  To keep
        the routing logic uniform each loose file is moved into a
        temporary folder named after the current timestamp.  This
        folder then becomes a pack for classification.
        """
        loose_files = [p for p in self.inbox_dir.iterdir() if p.is_file() and not self._should_ignore(p.name)]
        if not loose_files:
            return
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp_folder = self.inbox_dir / f"Loose_{timestamp}"
        tmp_folder.mkdir(exist_ok=True)
        for file_path in loose_files:
            dest = tmp_folder / file_path.name
            shutil.move(str(file_path), str(dest))

    def _discover_packs(self) -> List[Path]:
        """Return a list of pack directories within the inbox."""
        packs = []
        for entry in self.inbox_dir.iterdir():
            if self._should_ignore(entry.name):
                continue
            if entry.is_dir():
                packs.append(entry)
        return packs

    def _ensure_hub_structure(self, category: str, bucket: str, pack_name: str) -> Tuple[Path, Path, Path]:
        """Ensure that the destination directories exist and write `.nfo` files.

        Returns a tuple of (category_dir, bucket_dir, pack_dir).
        """
        category_dir = self.hub_dir / category
        # Use display name for bucket via bucket_service
        display_bucket = self.bucket_service.get_display_name(bucket)
        bucket_dir = category_dir / display_bucket
        pack_dir = bucket_dir / pack_name
        # Create directories
        pack_dir.mkdir(parents=True, exist_ok=True)
        # Write `.nfo` for category, bucket and pack using style service
        category_style = self.style_service.resolve_style(bucket, category)
        self.style_service.write_nfo(self.hub_dir, category, category_style)
        bucket_style = self.style_service.resolve_style(bucket, category)
        # Note: bucket .nfo goes next to category_dir
        self.style_service.write_nfo(category_dir, display_bucket, bucket_style)
        pack_style = self.style_service.pack_style_from_bucket(bucket_style)
        # Pack .nfo goes next to bucket_dir (sibling to pack folder)
        self.style_service.write_nfo(bucket_dir, pack_name, pack_style)
        return category_dir, bucket_dir, pack_dir

    def _ensure_unsorted_structure(self, pack_name: str) -> Path:
        """Ensure that the UNSORTED folder exists for a pack and return its path."""
        unsorted_dir = self.hub_dir / "UNSORTED" / pack_name
        unsorted_dir.mkdir(parents=True, exist_ok=True)
        # Write `.nfo` for UNSORTED category if not already
        self.style_service.write_nfo(self.hub_dir, "UNSORTED", DEFAULT_UNSORTED_STYLE)
        # Write `.nfo` for the pack in UNSORTED reusing default
        self.style_service.write_nfo(self.hub_dir / "UNSORTED", pack_name, DEFAULT_UNSORTED_STYLE)
        return unsorted_dir

    def _move_or_copy(self, src: Path, dst: Path, mode: str) -> None:
        """Move or copy a file based on the selected mode."""
        dst.parent.mkdir(parents=True, exist_ok=True)
        if mode == "move":
            shutil.move(str(src), str(dst))
        elif mode == "copy":
            shutil.copy2(str(src), str(dst))
        else:  # dry-run, analyze, repair
            pass

    def _log_audit_row(
        self,
        writer: csv.writer,
        file_path: Path,
        pack: Path,
        bucket: Optional[str],
        category: str,
        confidence: float,
        action: str,
        reason: str,
    ) -> None:
        writer.writerow(
            [
                str(file_path),
                pack.name,
                category,
                bucket or "UNSORTED",
                f"{confidence:.2f}",
                action,
                reason,
            ]
        )

    def run(
        self,
        mode: str = "analyze",
        overwrite_nfo: bool = False,
        normalize_pack_name: bool = False,
        developer_options: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, any]:
        """Execute a run in the specified mode.

        ``mode`` may be ``analyze`` (collect stats only), ``dry-run``
        (determine destinations but do nothing), ``copy`` (copy files),
        ``move`` (move files) or ``repair-styles`` (regenerate `.nfo`
        files).  The engine always produces a run report dictionary
        summarising what happened.  In ``move`` mode an ``audit.csv``
        will be generated to support undo.
        """
        mode = mode.lower()
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
        log_dir = self.hub_dir / "logs" / run_id
        log_dir.mkdir(parents=True, exist_ok=True)
        audit_path = log_dir / "audit.csv"
        run_log_path = log_dir / "run_log.txt"
        report_path = log_dir / "run_report.json"
        # prepare logging
        report = {
            "run_id": run_id,
            "mode": mode,
            "timestamp": datetime.datetime.now().isoformat(),
            "files_processed": 0,
            "files_moved": 0,
            "files_copied": 0,
            "unsorted": 0,
            "packs": [],
        }
        # wrap loose files before scanning
        self._wrap_loose_files()
        packs = self._discover_packs()
        with open(run_log_path, "w", encoding="utf-8") as log_file:
            # Prepare audit writer if necessary
            audit_file = None
            audit_writer = None
            if mode == "move":
                audit_file = open(audit_path, "w", newline="", encoding="utf-8")
                audit_writer = csv.writer(audit_file)
                audit_writer.writerow([
                    "file",
                    "pack",
                    "category",
                    "bucket",
                    "confidence",
                    "action",
                    "reason",
                ])
            for pack_dir in packs:
                pack_report = {
                    "pack": pack_dir.name,
                    "files": [],
                }
                files = list(pack_dir.rglob("*"))
                for file_path in files:
                    if file_path.is_dir() or self._should_ignore(file_path.name):
                        continue
                    rel_path = file_path.relative_to(pack_dir)
                    # Perform hybrid classification for this file
                    bucket, category, confidence, candidates, low_confidence, reason_dict = self._classify_file(file_path)
                    dest_path: Optional[Path] = None
                    if bucket is None:
                        # Route to UNSORTED when no bucket match
                        dest_dir = self._ensure_unsorted_structure(pack_dir.name)
                        dest_path = dest_dir / rel_path
                        report["unsorted"] += 1
                        # Build reason string with top candidate scores if available
                        if candidates:
                            reason = "; ".join([f"{b}:{int(score)}" for b, score in candidates])
                        else:
                            reason = "no matches"
                    else:
                        # Create hub structure and compute destination
                        _, _, pack_dest_dir = self._ensure_hub_structure(category, bucket, pack_dir.name)
                        dest_path = pack_dest_dir / rel_path
                        reason = f"best match: {bucket}, confidence={confidence:.2f}"
                        # Append low confidence note
                        if low_confidence:
                            reason += "; low confidence"
                        # Always append top candidates for transparency
                        if candidates:
                            reason += "; candidates: " + ", ".join([f"{b}:{int(score)}" for b, score in candidates])
                    action = "NONE"
                    if mode in {"copy", "move"}:
                        # Skip if file already exists at destination
                        if dest_path.exists():
                            reason += "; destination exists"
                        else:
                            self._move_or_copy(file_path, dest_path, mode)
                            action = mode.upper()
                            if mode == "move":
                                report["files_moved"] += 1
                            else:
                                report["files_copied"] += 1
                    pack_report["files"].append(
                        {
                            "source": str(file_path),
                            "dest": str(dest_path),
                            "bucket": bucket or "UNSORTED",
                            "category": category,
                            "confidence": confidence,
                            "action": action,
                            "reason": reason,
                        }
                    )
                    report["files_processed"] += 1
                    # Write audit row
                    if audit_writer:
                        audit_action = action if action else "NONE"
                        audit_writer.writerow([
                            str(file_path),
                            pack_dir.name,
                            category,
                            bucket or "UNSORTED",
                            f"{confidence:.2f}",
                            audit_action,
                            reason,
                        ])
                report["packs"].append(pack_report)
            if audit_file:
                audit_file.close()
        # Save JSON report
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        # Persist feature cache across runs
        self._save_feature_cache()
        return report

    def undo_last_run(self) -> Dict[str, any]:
        """Undo the most recent move run by reading its audit.csv.

        Files are moved back to the inbox.  If a file already exists in the
        inbox its original name is preserved and the conflicting file is
        placed into ``HUB/Quarantine/UndoConflicts``.  Returns a summary
        report with counts of restored and conflicted files.
        """
        logs_root = self.hub_dir / "logs"
        if not logs_root.exists():
            return {"error": "No logs found"}
        # Find latest audit.csv
        audit_files = sorted(logs_root.rglob("audit.csv"), key=os.path.getmtime, reverse=True)
        if not audit_files:
            return {"error": "No audit files found"}
        audit_path = audit_files[0]
        restored = 0
        conflicts = 0
        quarantine_dir = self.hub_dir / "Quarantine" / "UndoConflicts"
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        with open(audit_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = Path(row["file"])
                dest_in_inbox = self.inbox_dir / src.name
                # Only attempt to restore if action was move
                if row["action"].upper() != "MOVE":
                    continue
                # Determine where the file currently is: it's either in hub or already moved
                current_location = None
                # We recorded destination path in report, but reconstruct from hub
                bucket = row["bucket"]
                category = row["category"]
                pack = row["pack"] if "pack" in row else row["pack"]
                if bucket != "UNSORTED":
                    # Use display name for bucket when building current path
                    display_bucket = self.bucket_service.get_display_name(bucket)
                    current_location = self.hub_dir / category / display_bucket / pack / src.name
                else:
                    current_location = self.hub_dir / "UNSORTED" / pack / src.name
                if not current_location.exists():
                    # File might have been deleted or already restored
                    continue
                if dest_in_inbox.exists():
                    # Conflict – move to quarantine
                    shutil.move(str(current_location), str(quarantine_dir / src.name))
                    conflicts += 1
                else:
                    shutil.move(str(current_location), str(dest_in_inbox))
                    restored += 1
        return {
            "restored": restored,
            "conflicts": conflicts,
            "audit_file": str(audit_path),
        }

    def repair_styles(self) -> Dict[str, any]:
        """Repair and regenerate missing or misplaced `.nfo` files.

        The repair process traverses the hub directory and ensures that a
        `.nfo` exists next to each category, bucket and pack folder.  It
        removes orphan `.nfo` files that no longer correspond to any
        folder and relocates incorrectly placed files.  Returns a
        summary of actions taken.
        """
        actions = {
            "created": 0,
            "updated": 0,
            "removed": 0,
            "relocated": 0,
        }
        # Collect desired `.nfo` paths
        desired_nfos = set()
        for category_dir in self.hub_dir.iterdir():
            if not category_dir.is_dir() or self._should_ignore(category_dir.name):
                continue
            category = category_dir.name
            # Category nfo
            desired_nfos.add(self.hub_dir / f"{category}.nfo")
            for bucket_dir in category_dir.iterdir():
                if not bucket_dir.is_dir() or self._should_ignore(bucket_dir.name):
                    continue
                # Determine bucket ID from display name
                display_bucket = bucket_dir.name
                bucket_id = self.bucket_service.get_bucket_id(display_bucket)
                bucket = bucket_id if bucket_id else display_bucket
                # Bucket nfo lives in category dir with display name
                desired_nfos.add(category_dir / f"{display_bucket}.nfo")
                for pack_dir in bucket_dir.iterdir():
                    if not pack_dir.is_dir() or self._should_ignore(pack_dir.name):
                        continue
                    pack = pack_dir.name
                    # Pack nfo lives in bucket dir
                    desired_nfos.add(bucket_dir / f"{pack}.nfo")
        # Create or update desired nfos
        for nfo_path in desired_nfos:
            folder_name = nfo_path.stem
            parent_dir = nfo_path.parent
            # Determine type (category/bucket/pack) and obtain style
            if parent_dir == self.hub_dir:
                category = folder_name
                # For UNSORTED use default style
                if category.upper() == "UNSORTED":
                    style = DEFAULT_UNSORTED_STYLE
                else:
                    # Category style uses same bucket name for colour fallback
                    # but here we don't know bucket; treat bucket=category
                    style = self.style_service.resolve_style(category, category)
            else:
                # Determine bucket or pack
                grandparent = parent_dir.parent
                if grandparent == self.hub_dir:
                    # Bucket nfo
                    category = parent_dir.name
                    display_bucket = folder_name
                    # Find bucket ID from display name for style resolution
                    bucket_id = self.bucket_service.get_bucket_id(display_bucket) or display_bucket
                    style = self.style_service.resolve_style(bucket_id, category)
                else:
                    # Pack nfo
                    category = grandparent.name
                    display_bucket = parent_dir.name
                    bucket_id = self.bucket_service.get_bucket_id(display_bucket) or display_bucket
                    style = self.style_service.pack_style_from_bucket(
                        self.style_service.resolve_style(bucket_id, category)
                    )
            # Write nfo using style_service
            if nfo_path.exists():
                existing = nfo_path.read_text(encoding="utf-8").strip()
                new_contents = self.style_service._nfo_contents(style)
                if existing != new_contents:
                    self.style_service.write_nfo(parent_dir, folder_name, style)
                    actions["updated"] += 1
            else:
                self.style_service.write_nfo(parent_dir, folder_name, style)
                actions["created"] += 1
        # Remove orphan nfos
        for nfo in self.hub_dir.rglob("*.nfo"):
            if nfo not in desired_nfos:
                # Only remove if file corresponds to a folder in our tree; do not remove user files
                nfo.unlink()
                actions["removed"] += 1
        return actions


# Default UNSORTED style: neutral colour and generic icon
DEFAULT_UNSORTED_STYLE = {
    "Color": "$7f7f7f",
    "IconIndex": 0,
    "SortGroup": 0,
}