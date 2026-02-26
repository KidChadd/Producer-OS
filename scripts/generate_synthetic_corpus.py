from __future__ import annotations

import argparse
import json
import math
import wave
from pathlib import Path

SAMPLE_RATE = 22050


def _clamp(v: float) -> float:
    return max(-1.0, min(1.0, v))


def write_wav(path: Path, samples: list[float], sample_rate: int = SAMPLE_RATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        pcm = bytearray()
        for s in samples:
            x = int(_clamp(s) * 32767)
            pcm += int(x).to_bytes(2, byteorder="little", signed=True)
        wf.writeframes(pcm)


def sine_tone(freq: float, duration_s: float, amp: float = 0.6) -> list[float]:
    n = int(duration_s * SAMPLE_RATE)
    return [amp * math.sin(2.0 * math.pi * freq * (i / SAMPLE_RATE)) for i in range(n)]


def glide_tone(freq_start: float, freq_end: float, duration_s: float, amp: float = 0.7) -> list[float]:
    n = int(duration_s * SAMPLE_RATE)
    phase = 0.0
    out: list[float] = []
    for i in range(n):
        t = i / max(1, n - 1)
        freq = freq_start + (freq_end - freq_start) * t
        phase += (2.0 * math.pi * freq) / SAMPLE_RATE
        env = 1.0 - 0.25 * t
        out.append((amp * env) * math.sin(phase))
    return out


def kick_like(duration_s: float = 0.14) -> list[float]:
    n = int(duration_s * SAMPLE_RATE)
    phase = 0.0
    out: list[float] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 140.0 * math.exp(-12.0 * t) + 38.0
        phase += (2.0 * math.pi * freq) / SAMPLE_RATE
        env = math.exp(-28.0 * t)
        click = 0.45 * math.exp(-180.0 * t) * (1.0 if (i % 2 == 0) else -1.0)
        out.append(0.85 * env * math.sin(phase) + click)
    return out


def bright_hat_like(duration_s: float = 0.08) -> list[float]:
    n = int(duration_s * SAMPLE_RATE)
    out: list[float] = []
    state = 1
    prev = 0.0
    for i in range(n):
        # Deterministic LCG pseudo-noise (no randomness module needed).
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        noise = ((state / 0x7FFFFFFF) * 2.0) - 1.0
        hp = noise - 0.97 * prev
        prev = noise
        t = i / SAMPLE_RATE
        env = math.exp(-38.0 * t)
        out.append(0.55 * env * hp)
    return out


def ambiguous_mid(duration_s: float = 0.2) -> list[float]:
    n = int(duration_s * SAMPLE_RATE)
    out: list[float] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = math.exp(-8.0 * t)
        s = 0.28 * math.sin(2.0 * math.pi * 420.0 * t)
        s += 0.18 * math.sin(2.0 * math.pi * 840.0 * t)
        s += 0.08 * (1.0 if (i % 17) < 8 else -1.0)
        out.append(env * s)
    return out


def normalize(samples: list[float]) -> list[float]:
    peak = max((abs(x) for x in samples), default=1.0)
    if peak <= 1e-12:
        return samples
    scale = 0.95 / peak
    return [x * scale for x in samples]


def build_corpus(root: Path) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []

    def add(rel: str, data: list[float], expected_bucket: str, note: str) -> None:
        path = root / rel
        write_wav(path, normalize(data))
        cases.append(
            {
                "path": rel.replace("\\", "/"),
                "expected_bucket_hint": expected_bucket,
                "note": note,
                "sample_rate": SAMPLE_RATE,
            }
        )

    add(
        "808s_hint_pack/01.wav",
        sine_tone(55.0, 0.35, amp=0.45),
        "808s",
        "Neutral low tone in 808-named folder (folder hint demo).",
    )
    add(
        "808s_folder_misleading/kick_short.wav",
        kick_like(0.14),
        "Kicks",
        "Kick-like transient in misleading 808 folder (audio override demo).",
    )
    add(
        "808_glide_pack/808_glide_60_to_50.wav",
        glide_tone(60.0, 50.0, 0.55, amp=0.7),
        "808s",
        "Deterministic downward glide useful for glide detection demos.",
    )
    add(
        "hihats_bright_pack/hat_bright_noise.wav",
        bright_hat_like(0.08),
        "HiHats",
        "Bright short noisy sample for percussive/hat classification demos.",
    )
    add(
        "ambiguous_pack/ambiguous_mid.wav",
        ambiguous_mid(0.2),
        "unknown/low-confidence",
        "Intentionally ambiguous synthetic sample for low-confidence review demos.",
    )

    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a tiny deterministic synthetic WAV corpus for demos/tests.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("examples") / "synthetic_corpus",
        help="Output folder (default: examples/synthetic_corpus)",
    )
    args = parser.parse_args()

    output_root = args.output.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    cases = build_corpus(output_root)

    manifest = {
        "version": 1,
        "description": "Deterministic synthetic WAV corpus for Producer-OS demos and bug reports.",
        "generator": "scripts/generate_synthetic_corpus.py",
        "cases": cases,
    }
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(cases)} WAV files under {output_root}")
    print(f"Wrote manifest: {output_root / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

