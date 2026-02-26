# Synthetic Sample Corpus (Deterministic)

This folder contains a tiny synthetic WAV corpus for:

- reproducible bug reports
- classifier tuning discussions
- demos of low-confidence review and glide detection

The files are intentionally synthetic (no copyrighted sample content).

## Included Cases

- `808s_hint_pack/01.wav` - neutral low tone in an `808s` folder (folder hint demo)
- `808s_folder_misleading/kick_short.wav` - kick-like transient in misleading folder (audio override demo)
- `808_glide_pack/808_glide_60_to_50.wav` - downward tonal glide (glide detection demo)
- `hihats_bright_pack/hat_bright_noise.wav` - bright/noisy short one-shot (hat/percussion demo)
- `ambiguous_pack/ambiguous_mid.wav` - intentionally ambiguous sample (low-confidence demo)

## Manifest

See `manifest.json` for paths and notes.

## Regeneration

You can regenerate this corpus deterministically:

```powershell
python scripts/generate_synthetic_corpus.py
```

By default it writes to `examples/synthetic_corpus/`.

