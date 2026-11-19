"""Build the 90s narration track by cutting ONLY the original speaker audio.
No synthesis, no re-voicing: clips are taken verbatim from the reference video.
Outputs: build/voice.wav (48k stereo) and build/timeline.json (clip + word timings
on the new 90s timeline, used for subtitles and visual sync)."""
import json, sys, wave, numpy as np, os
SR = 48000
src_wav, transcript = sys.argv[1], sys.argv[2]
os.makedirs('build', exist_ok=True)
w = wave.open(src_wav); ch = w.getnchannels()
A = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, ch) / 32768
mono = A.mean(1)
hop = int(.01 * SR)
nfr = len(mono) // hop
en = 20*np.log10(np.sqrt((mono[:nfr*hop].reshape(nfr, hop)**2).mean(1)) + 1e-9)
quiet = en < -24

def snap_start(t):
    f = int(round(t*100)) + 12
    while f > 3 and not quiet[f-3:f].all(): f -= 1
    return max(0, f/100 - 0.05)
def snap_end(t):
    f = int(round(t*100)) - 12
    while f < nfr-3 and not quiet[f:f+3].all(): f += 1
    return f/100 + 0.08

# (scene, source_start, source_end) — approximate word boundaries from Whisper,
# snapped to real silences below.
CLIPS = [
  ('hook',    0.00,  10.10),   # Hai geng, ramai orang tanya saya kenapa ... bidang politik
  ('change', 14.74,  24.28),   # Kerana saya percaya kalau kita mahu mengubah sesuatu ...
  ('change', 24.28,  28.24),   # Politik ialah proses kita membina dasar
  ('change', 28.24,  33.24),   # Politik menentukan bagaimana pendidikan ... ekonomi diperkasakan
  ('youth',  46.16,  54.90),   # Parlimen Belia Malaysia menyediakan ... dasar awam dan kepimpinan
  ('women',  65.32,  78.62),   # Saya percaya ... pemerhati dari jauh ... membentuk dasar negara
  ('issues',102.58, 107.62, 'x'),   # keperluan memperbanyakkan taska ... ibu bekerja
  ('issues',109.78, 114.84, 'x'),   # memperjuangkan hak wanita muslim ... tuntutan agama di tempat kerja
  ('issues',140.98, 144.98),   # keperluan sistem sokongan ... wanita bekerja
  ('voices',156.60, 166.38, 'x'),   # contoh-contoh ini membuktikan ... perspektif ... orang lain
  ('future',208.86, 212.86),   # masa depan Malaysia memerlukan ... berani untuk memimpin
  ('future',219.82, 223.76),   # Kita jadi sebahagian daripada masa depan itu sama-sama
]
# Gap (seconds of breathing room) BEFORE each clip on the new timeline.
GAPS = [0.6, 0.75, 0.3, 0.3, 0.7, 0.75, 0.63, 0.25, 0.4, 0.46, 0.7, 0.45]
TOTAL = 90.0

# Whisper words, with spelling corrected against the captions burned into the source video
FIX = {'Hai':'Hai','Yang,':'geng,','jawaban':'jawapan','memangami':'memahami','taskar':'taska',
       'keputusan@113':'tuntutan','setiap':'sentiasa','pemberubahan':'perubahan','mahu@17':'mahu'}
r = json.load(open(transcript))
words = []
for s in r['segments']:
    for wd in s['words']:
        t = wd['word'].strip()
        key = f"{t}@{int(wd['start'])}"
        t = FIX.get(key, FIX.get(t, t))
        words.append((wd['start'], wd['end'], t))
# speaker says "kalau kita tak mahu mengubah" per Whisper; captions show "kalau kita nak mengubah"
words = [(a, b, 'nak' if (t == 'tak' and 17 < a < 18) else t) for a, b, t in words if not (t == 'mahu' and 17.7 < a < 18.5)]

out = np.zeros((int(TOTAL*SR), 2), np.float32)
pos = 0.0; tl = []
for clip, g in zip(CLIPS, GAPS):
    scene, s, e = clip[:3]
    # 'x' = hand-checked onset (consonant onsets that silence-snapping would clip)
    s2, e2 = (s if len(clip) > 3 else snap_start(s)), snap_end(e)
    pos += g
    seg = A[int(s2*SR):int(e2*SR)].copy()
    fade = int(.02*SR)
    ramp = np.linspace(0, 1, fade)[:, None]
    seg[:fade] *= ramp; seg[-fade:] *= ramp[::-1]
    i = int(pos*SR); out[i:i+len(seg)] += seg
    ws = [dict(t0=round(pos+max(a, s2)-s2, 3), t1=round(pos+min(b, e2)-s2, 3), w=t)
          for a, b, t in words if s2 <= (a+b)/2 <= e2]
    tl.append(dict(scene=scene, src=[s2, e2], t0=round(pos, 3), t1=round(pos+e2-s2, 3), words=ws))
    print(f"{scene:7s} src {s2:7.2f}-{e2:7.2f} -> {pos:6.2f}-{pos+e2-s2:6.2f}  " + ' '.join(x['w'] for x in ws))
    pos += e2 - s2
print('speech ends at', round(pos, 2))
assert pos < TOTAL - 1.5
wv = wave.open('build/voice.wav', 'wb'); wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR)
wv.writeframes((np.clip(out, -1, 1)*32767).astype(np.int16).tobytes()); wv.close()
json.dump(dict(clips=tl, speech_end=pos, total=TOTAL), open('build/timeline.json', 'w'), indent=1, ensure_ascii=False)
