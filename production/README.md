# Wanita Muda & Politik — 90s animated infographic documentary

**Deliverable:** `final/Wanita_Muda_Politik_90s_9x16.mp4` (1080×1920, 9:16, 30 fps, exactly 90.000 s, H.264 + AAC 48 kHz, −14 LUFS)
Subtitles (Malay, also burned in): `final/Wanita_Muda_Politik_subtitles_ms.srt`

Narration is **only** Nurul Jannah's original audio, cut verbatim from the reference video (no AI voice, no re-recording).

| Step | File | What it does |
|---|---|---|
| 1 | `edit_audio.py` | Cuts 12 verbatim clips from the original audio onto the 90 s timeline → `build/voice.wav`, `build/timeline.json` |
| 2 | `make_subs.py` | Word-synced Malay subtitles (spelling checked against the original's burned-in captions) |
| 3 | `doc.html` + `render.js` + `render_all.sh` | Deterministic Canvas animation, captured frame-by-frame with headless Chromium |
| 4 | `music.py` | Original synthesized score (D minor, 90 BPM, no vocals) + motion-graphics SFX |
| 5 | `mix.sh` | Voice priority mix, sidechain ducking of music under speech, 2-pass loudness normalisation |

Rebuild: `python3 edit_audio.py <src48k.wav> <whisper.json> && python3 make_subs.py && python3 -m http.server 8765 & ./render_all.sh && python3 music.py && ./mix.sh`, then mux.
